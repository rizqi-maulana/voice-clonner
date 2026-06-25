"""
Voice Clonner — Clone any voice from a reference audio recording.
"""
from __future__ import annotations

import sys
import os
import re
import json
import random
import tempfile
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QGroupBox, QPushButton, QLabel, QTextEdit, QComboBox, QSlider,
    QFileDialog, QMessageBox, QProgressBar, QSizePolicy, QSplitter,
    QStatusBar, QFrame, QScrollArea,
)
from PyQt5.QtCore import Qt, QThread, QProcess, QProcessEnvironment, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QFontDatabase
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from config import XTTS_MODEL_DIR, HF_CACHE_DIR, APP_DIR, APP_DATA_DIR, Config
from theme import STYLE
from version import __version__

LANGUAGES = {
    "Indonesian": "_chatterbox_",  # special flag → handled by ChatterboxManager, not XTTS
    "English":    "en",
    "Spanish":    "es",
    "French":     "fr",
    "German":     "de",
    "Italian":    "it",
    "Portuguese": "pt",
    "Polish":     "pl",
    "Turkish":    "tr",
    "Russian":    "ru",
    "Dutch":      "nl",
    "Czech":      "cs",
    "Arabic":     "ar",
    "Chinese":    "zh-cn",
    "Hungarian":  "hu",
    "Korean":     "ko",
    "Japanese":   "ja",
    "Hindi":      "hi",
}

SAMPLE_TEXTS = {
    "Indonesian": [
        "Selamat pagi, hari ini cuaca sangat cerah dan saya merasa bersemangat untuk memulai hari.",
        "Teknologi kecerdasan buatan telah mengubah cara kita bekerja dan berkomunikasi setiap hari.",
        "Perpustakaan kota ini memiliki koleksi buku yang sangat lengkap dari berbagai bidang ilmu.",
        "Saya suka menikmati secangkir kopi hangat sambil membaca koran di teras rumah setiap pagi.",
        "Pemandangan gunung dan danau di daerah ini sungguh memukau saat matahari terbenam.",
        "Musik tradisional Indonesia memiliki keunikan tersendiri yang diakui dunia internasional.",
        "Anak-anak bermain dengan riang di taman sambil menunggu orang tua mereka menjemput.",
        "Perkembangan ekonomi digital membuka banyak peluang baru bagi pengusaha muda Indonesia.",
    ],
    "English": [
        "The quick brown fox jumped gracefully over the lazy dog sleeping by the warm fireplace.",
        "She sells seashells by the seashore while the waves crash against the rocky cliffs.",
        "Every morning I enjoy a fresh cup of coffee while reading the newspaper on my porch.",
        "Artificial intelligence has completely transformed how we work and communicate daily.",
        "Beautiful mountains and crystal clear lakes make this region a paradise for nature lovers.",
        "The old library on the corner has thousands of books covering every subject imaginable.",
        "Musicians from around the world gathered for the annual jazz festival downtown.",
        "Children played happily in the park while their parents watched from the benches.",
    ],
    "Spanish": [
        "Buenos dias, hoy el clima esta muy agradable y tengo ganas de pasear por el parque.",
        "La inteligencia artificial ha cambiado completamente la forma en que vivimos y trabajamos.",
        "Me encanta disfrutar de una taza de cafe caliente mientras leo un buen libro por la mana.",
        "Las montanas y los lagos de esta region son impresionantes, especialmente al atardecer.",
        "La musica tradicional de cada pais tiene una belleza unica que merece ser preservada.",
        "Los ninos jugaban alegremente en el parque mientras sus padres conversaban en los bancos.",
        "El desarrollo de la economia digital abre nuevas oportunidades para jovenes emprendedores.",
        "La biblioteca de la ciudad tiene una coleccion extraordinaria de libros de todas las epocas.",
    ],
    "French": [
        "Bonjour, aujourd'hui le temps est magnifique et j'ai envie de me promener dans le jardin.",
        "L'intelligence artificielle a profondement transforme notre facon de travailler et communiquer.",
        "J'adore savourer une tasse de cafe chaud en lisant le journal chaque matin sur la terrasse.",
        "Les montagnes et les lacs de cette region sont absolument splendides au coucher du soleil.",
        "La musique classique francaise a une richesse et une beaute qui traversent les siecles.",
        "Les enfants jouaient joyeusement dans le parc pendant que leurs parents discutaient.",
        "Le developpement du numerique ouvre de nouvelles perspectives pour les jeunes entrepreneurs.",
        "La bibliotheque municipale possede une collection remarquable de livres anciens et modernes.",
    ],
    "German": [
        "Guten Morgen, heute ist das Wetter wunderschoen und ich moechte im Park spazieren gehen.",
        "Kuenstliche Intelligenz hat unsere Art zu arbeiten und zu kommunizieren grundlegend veraendert.",
        "Ich geniesse jeden Morgen eine Tasse heissen Kaffee waehrend ich die Zeitung auf der Terrasse lese.",
        "Die Berge und Seen dieser Region sind atemberaubend schoen, besonders bei Sonnenuntergang.",
        "Deutsche Volksmusik hat eine einzigartige Schoenheit, die weltweit geschaetzt wird.",
        "Die Kinder spielten froehlich im Park, waehrend ihre Eltern auf den Baenken redeten.",
        "Die digitale Wirtschaft eroeffnet jungen Unternehmern viele neue und spannende Moeglichkeiten.",
        "Die Stadtbibliothek verfuegt ueber eine beeindruckende Sammlung von Buechern aller Wissensgebiete.",
    ],
    "Italian": [
        "Buongiorno, oggi il tempo e splendido e ho voglia di fare una passeggiata nel parco.",
        "L'intelligenza artificiale ha trasformato profondamente il nostro modo di lavorare e comunicare.",
        "Mi piace gustare una tazza di caffe caldo mentre leggo il giornale ogni mattina in terrazza.",
        "Le montagne e i laghi di questa regione sono magnifici, soprattutto al tramonto.",
        "La musica italiana ha una bellezza unica che e riconosciuta e amata in tutto il mondo.",
        "I bambini giocavano felicemente nel parco mentre i genitori chiacchieravano sulle panchine.",
        "Lo sviluppo dell'economia digitale apre nuove opportunita per i giovani imprenditori.",
        "La biblioteca comunale ha una collezione straordinaria di libri antichi e moderni.",
    ],
    "Portuguese": [
        "Bom dia, hoje o tempo esta maravilhoso e eu quero passear pelo parque da cidade.",
        "A inteligencia artificial transformou completamente a forma como trabalhamos e nos comunicamos.",
        "Eu adoro saborear uma xicara de cafe quente enquanto leio o jornal todas as manhas.",
        "As montanhas e os lagos desta regiao sao deslumbrantes, especialmente ao por do sol.",
        "A musica brasileira tem uma riqueza e diversidade que encanta pessoas do mundo inteiro.",
        "As criancas brincavam alegremente no parque enquanto os pais conversavam nos bancos.",
        "O desenvolvimento da economia digital abre novas oportunidades para jovens empreendedores.",
        "A biblioteca da cidade possui uma colecao impressionante de livros de todas as areas.",
    ],
    "Polish": [
        "Dzien dobry, dzisiaj pogoda jest wspaniala i mam ochote na spacer po parku.",
        "Sztuczna inteligencja calkowicie zmienila sposob, w jaki pracujemy i komunikujemy sie.",
        "Uwielbiam pic goraca kawe rano, czytajac gazete na tarasie mojego domu.",
        "Gory i jeziora w tym regionie sa zachwycajace, szczegolnie podczas zachodu slonca.",
        "Polska muzyka ludowa ma wyjatkowe piekno, ktore jest doceniane na calym swiecie.",
        "Dzieci bawily sie radosnie w parku, podczas gdy rodzice rozmawiali na lawkach.",
        "Rozwoj gospodarki cyfrowej otwiera nowe mozliwosci dla mlodych przedsiebiorcow w Polsce.",
        "Biblioteka miejska posiada imponujacy zbior ksiazek z roznych dziedzin nauki.",
    ],
    "Turkish": [
        "Gunaydin, bugun hava cok guzel ve parkta yuruyus yapmak istiyorum.",
        "Yapay zeka, calisma ve iletisim bicimimizi tamamen degistirdi.",
        "Her sabah terasta gazete okurken sicak bir fincan kahve icmeyi seviyorum.",
        "Bu bolgedeki daglar ve goller, ozellikle gun batiminda muhtesem gorunuyor.",
        "Turk muzigi, dunya genelinde takdir edilen benzersiz bir guzellige sahiptir.",
        "Cocuklar parkta neseyle oynarken, ebeveynleri banklarda oturup sohbet ediyordu.",
        "Dijital ekonominin gelismesi, genc girisimcilere yeni firsatlar sunmaktadir.",
        "Sehir kutuphanesi, her alanda etkileyici bir kitap koleksiyonuna sahiptir.",
    ],
    "Russian": [
        "Dobroe utro, segodnya prekrasnaya pogoda i ya khochu proguliat'sya po parku.",
        "Iskusstvennyy intellekt polnost'yu izmenil nash sposob raboty i obshcheniya.",
        "Kazhdoe utro ya lyublyu pit' goryachiy kofe, chitaya gazetu na terrasse svoego doma.",
        "Gory i ozyora etogo regiona porazhayut svoyey krasotoy, osobenno na zakate solntsa.",
        "Russkaya klassicheskaya muzyka obladayet unikal'noy krasotoy, priznannoy vo vsyom mire.",
        "Deti veselo igrali v parke, poka ikh roditeli razgovarivali na skameykakh.",
        "Razvitie tsifrovoy ekonomiki otkryvayet novye vozmozhnosti dlya molodykh predprinimateley.",
        "Gorodskaya biblioteka raspolagayet vpechatlyayushchey kollektsiyey knig po vsem oblastyam znaniy.",
    ],
    "Dutch": [
        "Goedemorgen, het weer is vandaag prachtig en ik wil graag een wandeling in het park maken.",
        "Kunstmatige intelligentie heeft onze manier van werken en communiceren volledig veranderd.",
        "Elke ochtend geniet ik van een kopje warme koffie terwijl ik de krant lees op het terras.",
        "De bergen en meren in deze regio zijn adembenemend mooi, vooral bij zonsondergang.",
        "Nederlandse volksmuziek heeft een unieke schoonheid die wereldwijd wordt gewaardeerd.",
        "De kinderen speelden vrolijk in het park terwijl hun ouders op de bankjes zaten te praten.",
        "De ontwikkeling van de digitale economie biedt jonge ondernemers veel nieuwe kansen.",
        "De stadsbibliotheek heeft een indrukwekkende collectie boeken uit alle vakgebieden.",
    ],
    "Czech": [
        "Dobre rano, dnes je krasne pocasi a chtel bych se projit parkem.",
        "Umela inteligence zcela zmenila zpusob, jakym pracujeme a komunikujeme.",
        "Kazde rano si rad vychutnavam salek horke kavy pri cteni novin na terase.",
        "Hory a jezera v tomto regionu jsou ohromujici, zejmena pri zapadu slunce.",
        "Ceska hudebni tradice ma jedinecnou krasu, ktera je ocenovana po celem svete.",
        "Deti si vesele hraly v parku, zatimco jejich rodice sedeli na lavickach a povidali si.",
        "Rozvoj digitalni ekonomiky otevira nove prilezitosti pro mlade podnikatele v Cesku.",
        "Mestska knihovna ma pusobivou sbirku knih z nejruznejsich oboru lidskeho poznani.",
    ],
    "Arabic": [
        "Sabah al-khayr, al-taqs jamil al-yawm wa-urid an atamashsha fi al-hadiqa al-amma.",
        "Laqad ghayyara al-dhaka al-istinaiy tariqa amalina wa-tawasulina bi-shaklin jadhri.",
        "Uhibbu an astamtia bi-finjan min al-qahwa al-sakhina kulla sabah athna qiraat al-sahifa.",
        "Al-jibal wa-al-buhayrat fi hadhihi al-mintaqa sahira, khassatan inda ghurub al-shams.",
        "Al-musiqa al-arabiyya laha jamal farid yahza bi-al-taqdir fi jami anhar al-alam.",
        "Kana al-atfal yalaabun bi-saada fi al-hadiqa baynama yatahadath abaauhum ala al-maqaaid.",
        "Yaftah tatawwur al-iqtisad al-raqami furasan jadida amam ruwwad al-aamal al-shabab.",
        "Tamtalik maktabat al-madina majmuaa raia min al-kutub fi mukhtalaf majalat al-maarifa.",
    ],
    "Chinese": [
        "Zao shang hao, jin tian tian qi hen hao, wo xiang qu gong yuan san bu.",
        "Ren gong zhi neng yi jing che di gai bian le wo men gong zuo he jiao liu de fang shi.",
        "Mei tian zao shang wo dou xi huan yi bian he re ka fei yi bian kan bao zhi.",
        "Zhe ge di qu de shan he hu fei chang zhuang guan, you qi shi ri luo shi fen.",
        "Zhong guo chuan tong yin yue you zhe du te de mei gan, shou dao quan shi jie ren min de xi ai.",
        "Hai zi men zai gong yuan li kuai le de wan shua, ta men de fu mu zai chang yi shang liao tian.",
        "Shu zi jing ji de fa zhan wei nian qing de chuang ye zhe ti gong le xu duo xin de ji yu.",
        "Cheng shi tu shu guan yong you yi ge han gai ge ge zhi shi ling yu de feng fu cang shu.",
    ],
    "Hungarian": [
        "Jo reggelt, ma gyonyoru az ido es szeretnek setalni a parkban.",
        "A mestersege intelligencia teljesen megvaltoztatta a munkankat es kommunikacionkat.",
        "Minden reggel elvezem a forro kavemat, mikozben ujsagot olvasok a teraszon.",
        "Ennek a videknek a hegyei es tavai lelegzetelallitoak, kulonosen naplementekor.",
        "A magyar nepzene egyedulallo szepsege az egesz vilagon elismert es nagyra becsult.",
        "A gyerekek vidaman jatszottak a parkban, mikozben a szuleik a padokon beszelgettek.",
        "A digitalis gazdasag fejlodese uj lehetosegeket nyit a fiatal vallalkozok szamara.",
        "A varosi konyvtar lenyugozo gyujtemenynyel rendelkezik minden tudomanyteruletrol.",
    ],
    "Korean": [
        "Joeun achimimnida. Oneul nalssi ga jeongmal joaseo gonwon eseo sanchaek hago sipseumnida.",
        "Ingong jineung eun uriga ilhago sotong haneun bangsig eul wanjeonhi bakkwo noasseumnida.",
        "Maeil achim teraseu eseo sinmun eul ilgeumyeo ttatteutan keopi han jan eul jeulgimmnida.",
        "I jiyeog ui san gwa hosu neun teukhi haejilnyeok e jeongmal areumdaun punggyeong eul boyeojumnida.",
        "Hangug ui jeontong eumag eun segyejeog euro injeongbadneun dokteukan areumdaum eul gajigo isseumnida.",
        "Aideul eun gonwon eseo jeulgeopge nolgo isseotgo bumonim deul eun benchi eseo daehwa reul nanugo isseosseumnida.",
        "Dijiteol gyeongje ui baljeon eun jeolmeun gieopga deurege manheun saeroun gihoe reul yeoreojugo isseumnida.",
        "Sirip doseogwan eun dayanghan bunya ui chaekdeul euro guseongdoen insangjeog in keolleksyeon eul boyuhago isseumnida.",
    ],
    "Japanese": [
        "Ohayou gozaimasu. Kyou wa totemo yoi tenki nanode kouen wo sanpo shitai to omoimasu.",
        "Jinkou chinou wa watashitachi no hatarakikata ya komyunikeeshon no houhou wo ookiku kaemashita.",
        "Maiasa terasu de shinbun wo yominagara atatakai koohii wo tanoshimu no ga nikka desu.",
        "Kono chiiki no yamayama to mizuumi wa iki wo nomu hodo utsukushiku, yuugure doki wa kakubetsu desu.",
        "Nihon no dentou ongaku ni wa sekaijuu de mitomerarete iru dokutoku no utsukushisa ga arimasu.",
        "Kodomotachi wa kouen de tanoshisou ni asonde ite, oyatachi wa benchi de hanashi wo shite imashita.",
        "Dejitaru keizai no hatten ni yori wakai kigyoukatachi ni ooku no atarashii kikai ga umarete imasu.",
        "Shiritsu toshokan ni wa arayuru bunya no hon wo moura shita subarashii korekushon ga arimasu.",
    ],
    "Hindi": [
        "Suprabhat, aaj mausam bahut achha hai aur main park mein tahelna chahta hoon.",
        "Kritrim buddhimatta ne hamare kaam karne aur samvaad karne ke tareeke ko poori tarah badal diya hai.",
        "Har subah mujhe chhat par akhbaar padhte hue garam coffee peena bahut pasand hai.",
        "Is kshetra ke pahad aur jheelen adbhut hain, khaasakar sooryaast ke samay.",
        "Bharatiya shaastriya sangeet ki anoothee sundarta ko pooree duniya mein saraaha jaata hai.",
        "Bachche park mein khushi se khel rahe the jabki unke maata-pita bench par baithkar baatein kar rahe the.",
        "Digital arthvyavastha ka vikaas yuva udyamiyon ke liye naye avasar khol raha hai.",
        "Shahar ke pustakalaya mein gyaan ke har kshetra ki pustakon ka prabhaavshaalee sangraha hai.",
    ],
}

# Max characters per XTTS generation chunk (~400 tokens ≈ 350 chars)
MAX_CHUNK_CHARS = 300



_ID_ABBR = [
    (r'\byg\b',   'yang'),
    (r'\bdgn\b',  'dengan'),
    (r'\bdll\b',  'dan lain-lain'),
    (r'\bdsb\b',  'dan sebagainya'),
    (r'\btsb\b',  'tersebut'),
    (r'\butk\b',  'untuk'),
    (r'\bjd\b',   'jadi'),
    (r'\bkrn\b',  'karena'),
    (r'\bspt\b',  'seperti'),
    (r'\bsdh\b',  'sudah'),
    (r'\bblm\b',  'belum'),
    (r'\bbgt\b',  'banget'),
    (r'\bbnyk\b', 'banyak'),
    (r'\bdpt\b',  'dapat'),
    (r'\bttg\b',  'tentang'),
    (r'\bmnrt\b', 'menurut'),
    (r'\bsprti\b','seperti'),
]

def preprocess_indonesian(text: str) -> str:
    for pattern, replacement in _ID_ABBR:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def split_text_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into chunks at sentence boundaries for long-form generation."""
    # Split at sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, current = [], ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(current) + len(sentence) + 1 <= max_chars:
            current = (current + " " + sentence).strip()
        else:
            if current:
                chunks.append(current)
            # If a single sentence is too long, split at commas
            if len(sentence) > max_chars:
                parts = re.split(r',\s*', sentence)
                cur = ""
                for p in parts:
                    if len(cur) + len(p) + 2 <= max_chars:
                        cur = (cur + ", " + p).lstrip(", ")
                    else:
                        if cur:
                            chunks.append(cur)
                        cur = p
                if cur:
                    current = cur
                else:
                    current = ""
            else:
                current = sentence
    if current:
        chunks.append(current)
    return chunks or [text]


# ─── Background Threads ───────────────────────────────────────────────────────

class ModelLoaderThread(QThread):
    finished = pyqtSignal(object, object, str)
    status   = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, model_dir: Path):
        super().__init__()
        self.model_dir = model_dir

    def run(self):
        try:
            self.status.emit("Importing voice library...")
            from TTS.tts.configs.xtts_config import XttsConfig
            from TTS.tts.models.xtts import Xtts
            import torch

            self.status.emit("Loading model config...")
            config = XttsConfig()
            config.load_json(str(self.model_dir / "config.json"))

            self.status.emit("Initializing voice model...")
            model = Xtts.init_from_config(config)

            self.status.emit("Loading model weights (this may take a minute)...")
            model.load_checkpoint(
                config,
                checkpoint_dir=str(self.model_dir),
                eval=True,
            )

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model.to(device)

            self.finished.emit(model, config, device)
        except Exception as e:
            import traceback
            self.error.emit(traceback.format_exc())


class RecordThread(QThread):
    finished    = pyqtSignal(object, int)
    level_rms   = pyqtSignal(float)

    def __init__(self, samplerate: int = 22050):
        super().__init__()
        self.samplerate = samplerate
        self._stop = False
        self._frames = []

    def run(self):
        self._frames = []
        self._stop = False

        def callback(indata, frames, time, status):
            self._frames.append(indata.copy())
            rms = float(np.sqrt(np.mean(indata ** 2) + 1e-9))
            self.level_rms.emit(rms)
            if self._stop:
                raise sd.CallbackStop()

        with sd.InputStream(samplerate=self.samplerate, channels=1,
                            dtype="float32", callback=callback):
            while not self._stop:
                self.msleep(50)

        if self._frames:
            wav = np.concatenate(self._frames).flatten()
            self.finished.emit(wav, self.samplerate)

    def stop(self):
        self._stop = True


class GenerateThread(QThread):
    finished = pyqtSignal(object, int)
    status   = pyqtSignal(str)
    error    = pyqtSignal(str)

    def __init__(self, model, config, text, speaker_wavs,
                 language, temperature, speed):
        super().__init__()
        self.model       = model
        self.config      = config
        self.text        = text
        self.speaker_wavs = speaker_wavs
        self.language    = language
        self.temperature = temperature
        self.speed       = speed

    def run(self):
        try:
            self.status.emit("Computing speaker voice embedding...")
            gpt_cond_latent, speaker_embedding = self.model.get_conditioning_latents(
                audio_path=self.speaker_wavs,
                gpt_cond_len=getattr(self.config, "gpt_cond_len", 30),
                max_ref_length=60,
                sound_norm_refs=False,
            )

            chunks = split_text_into_chunks(self.text)
            wavs = []

            for i, chunk in enumerate(chunks, 1):
                self.status.emit(
                    f"Generating speech {i}/{len(chunks)}: \"{chunk[:40]}{'...' if len(chunk) > 40 else ''}\"")
                out = self.model.inference(
                    text=chunk,
                    language=self.language,
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=self.temperature,
                    length_penalty=1.0,
                    repetition_penalty=5.0,
                    top_k=50,
                    top_p=0.85,
                    speed=self.speed,
                )
                wav = out["wav"]
                if not isinstance(wav, np.ndarray):
                    wav = np.array(wav, dtype=np.float32)
                wavs.append(wav)
                # 200 ms silence between chunks
                if i < len(chunks):
                    wavs.append(np.zeros(int(0.2 * 24000), dtype=np.float32))

            final_wav = np.concatenate(wavs).astype(np.float32)
            # Normalize to -1..1
            max_val = np.abs(final_wav).max()
            if max_val > 0:
                final_wav = final_wav / max_val * 0.95

            self.finished.emit(final_wav, 24000)

        except Exception as e:
            import traceback
            self.error.emit(traceback.format_exc())


class ChatterboxManager:
    """
    Manages the persistent Chatterbox Indonesian subprocess.
    The generate.py server loads the model ONCE, then accepts multiple requests
    via JSON on stdin, returning results on stdout.
    """

    status_msg  = pyqtSignal if False else None   # placeholder — signals live in MainWindow

    def __init__(self, on_status, on_ready, on_error, on_audio_done,
                 on_progress=None):
        self._on_status     = on_status
        self._on_ready      = on_ready
        self._on_error      = on_error
        self._on_audio_done = on_audio_done
        self._on_progress   = on_progress
        self._sr            = 24000
        self.is_ready       = False
        self._stdout_buf    = b""
        self._pending_out   = None

        self._proc = QProcess()
        self._proc.readyReadStandardOutput.connect(self._on_stdout)
        self._proc.readyReadStandardError.connect(self._on_stderr)
        self._proc.finished.connect(self._on_finished)
        self._proc.errorOccurred.connect(self._on_proc_error)

    def start(self):
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("PYTHONIOENCODING", "utf-8")
        env.insert("HF_HOME", str(HF_CACHE_DIR))
        env.insert("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        env.remove("VIRTUAL_ENV")
        self._proc.setProcessEnvironment(env)

        chatterbox_dir = APP_DIR / "chatterbox"
        if not chatterbox_dir.exists():
            self._on_error(
                "Indonesian voice engine not found.\n\n"
                "Please re-download the application."
            )
            return
        self._proc.setWorkingDirectory(str(chatterbox_dir))
        self._proc.start("uv", ["run", "python", "-u", "generate.py"])

    def generate(self, text: str, ref_path: str, out_path: str,
                 exaggeration: float = 0.5):
        self._pending_out = out_path
        req = json.dumps({
            "type": "generate", "text": text,
            "ref": ref_path, "out": out_path,
            "exaggeration": exaggeration,
        }, ensure_ascii=False)
        self._proc.write((req + "\n").encode("utf-8"))

    @property
    def is_running(self):
        return self._proc.state() != QProcess.NotRunning

    def stop(self):
        if self._proc.state() != QProcess.NotRunning:
            try:
                self._proc.write(json.dumps({"type": "quit"}).encode() + b"\n")
                self._proc.waitForFinished(5000)
            except Exception:
                pass
            self._proc.kill()
        self.is_ready = False

    # ── internal ──

    def _on_stdout(self):
        self._stdout_buf += bytes(self._proc.readAllStandardOutput())
        while b"\n" in self._stdout_buf:
            raw, self._stdout_buf = self._stdout_buf.split(b"\n", 1)
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = msg.get("type")
            if t == "status":
                self._on_status(msg.get("msg", ""))
            elif t == "progress":
                if self._on_progress:
                    self._on_progress(msg.get("pct", 0), msg.get("msg", ""))
            elif t == "ready":
                self._sr = int(msg.get("sr", 24000))
                self.is_ready = True
                self._on_ready()
            elif t == "success":
                path = msg.get("path", self._pending_out)
                try:
                    wav, sr = sf.read(path, always_2d=False)
                    wav = wav.astype(np.float32)
                    m = np.abs(wav).max()
                    if m > 0:
                        wav = wav / m * 0.95
                    self._on_audio_done(wav, self._sr)
                except Exception as e:
                    self._on_error(f"Gagal membaca output audio: {e}")
            elif t == "error":
                self._on_error(msg.get("tb", msg.get("msg", "Unknown error")))

    def _on_stderr(self):
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace")
        # uv uses \r for progress updates — split on both \r and \n
        lines = re.split(r'[\r\n]+', data)
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("warning"):
                continue
            print("[Chatterbox stderr]", line, flush=True)
            clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line).strip()
            if len(clean) > 3:
                self._on_status(clean[:120])

    def _on_finished(self, exit_code, _):
        self.is_ready = False
        if exit_code not in (0, 15):    # 15 = SIGTERM from stop()
            self._on_error(
                f"Indonesian voice engine exited with code {exit_code}.\n"
                "Check the console for details.")

    def _on_proc_error(self, error):
        if error == QProcess.FailedToStart:
            self._on_error("Failed to start Indonesian voice engine.")


# ─── Loading Dialog ──────────────────────────────────────────────────────────

class SpinnerWidget(QWidget):
    """12-line rotating spinner (like macOS activity indicator)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 48)
        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

    def _tick(self):
        self._step = (self._step + 1) % 12
        self.update()

    def paintEvent(self, event):
        n = 12
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx = self.width() / 2
        p.translate(cx, cx)
        for i in range(n):
            p.save()
            p.rotate(i * 360.0 / n)
            fade = 1.0 - ((self._step - i) % n) / n
            p.setPen(QPen(QColor(0, 102, 204, int(40 + 215 * fade)),
                          2.5, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(0, int(-cx * 0.35), 0, int(-cx * 0.8))
            p.restore()
        p.end()


class ChatterboxLoadDialog(QDialog):
    """Modal dialog shown while Indonesian voice model is loading."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading Indonesian Voice Model")
        self.setFixedSize(440, 230)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 20)
        lay.setSpacing(10)

        self.spinner = SpinnerWidget()
        lay.addWidget(self.spinner, 0, Qt.AlignCenter)

        self.status_lbl = QLabel("Starting...")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        lay.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #e8e8ed; border: 1px solid #d2d2d7;
                border-radius: 6px; height: 18px;
                text-align: center; font-size: 11px; color: #3a3a4a;
            }
            QProgressBar::chunk { background: #0066cc; border-radius: 5px; }
        """)
        lay.addWidget(self.progress_bar)

        self.detail_lbl = QLabel("")
        self.detail_lbl.setAlignment(Qt.AlignCenter)
        self.detail_lbl.setStyleSheet("font-size: 12px; color: #8e8e93;")
        lay.addWidget(self.detail_lbl)

        lay.addStretch()

        self.btn_cancel = QPushButton("Batal")
        self.btn_cancel.setMaximumWidth(120)
        lay.addWidget(self.btn_cancel, 0, Qt.AlignCenter)

    def set_status(self, msg):
        self.status_lbl.setText(msg)

    def set_progress(self, pct, detail=""):
        if pct < 0:
            self.progress_bar.setRange(0, 0)
            self.detail_lbl.setText("")
        elif pct == 0:
            if detail:
                self.status_lbl.setText(detail)
                self.detail_lbl.setText("Mohon tunggu, mengunduh model…")
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(pct)
            if detail:
                self.status_lbl.setText(detail)
                self.detail_lbl.setText(f"{pct}% selesai")


# ─── Waveform Widget ──────────────────────────────────────────────────────────

class WaveformCanvas(FigureCanvas):
    def __init__(self, color="#4466cc", parent=None):
        self.fig = Figure(figsize=(6, 1.2), dpi=80, tight_layout=True)
        super().__init__(self.fig)
        self.setParent(parent)
        self.color = color
        self.ax = self.fig.add_subplot(111)
        self._style_axes()
        self.draw_idle()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(76)

    def _style_axes(self):
        self.fig.patch.set_facecolor("#f5f5f7")
        self.ax.set_facecolor("#f5f5f7")
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        for sp in self.ax.spines.values():
            sp.set_visible(False)

    def plot_wave(self, wav: np.ndarray | None, sr: int = 24000):
        self.ax.clear()
        self._style_axes()
        if wav is not None and len(wav) > 0:
            n = min(len(wav), 6000)
            idx = np.linspace(0, len(wav) - 1, n, dtype=int)
            t = np.linspace(0, len(wav) / sr, n)
            w = wav[idx]
            self.ax.fill_between(t, w, alpha=0.55, color=self.color)
            self.ax.plot(t, w, lw=0.6, color=self.color, alpha=0.9)
            self.ax.set_ylim(-1.05, 1.05)
        self.draw_idle()


# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self, app_config=None):
        super().__init__()
        self.app_config   = app_config
        self.model        = None
        self.config       = None
        self.device       = "cpu"
        self.ref_wav      = None
        self.ref_sr       = None
        self.ref_path     = None
        self.output_wav   = None
        self.output_sr    = 24000
        self._rec_thread  = None
        self._gen_thread  = None
        self._chatterbox  = None      # created lazily when Indonesian mode first used
        self._pending_chatterbox_text = ""
        self._cb_dialog   = None

        self._build_ui()
        self._load_model()

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowTitle("Voice Clonner")
        self.setMinimumSize(860, 700)
        self.setStyleSheet(STYLE)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)

        root = QWidget()
        scroll.setWidget(root)
        root_vbox = QVBoxLayout(root)
        root_vbox.setContentsMargins(20, 12, 20, 10)
        root_vbox.setSpacing(6)

        # ── Header ──
        hdr_row = QHBoxLayout()
        hdr_row.setContentsMargins(0, 0, 0, 0)
        hdr_row.addStretch()

        hdr_center = QVBoxLayout()
        hdr_center.setSpacing(2)
        title = QLabel("Voice Clonner")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        self.model_lbl = QLabel("Loading voice model, please wait...")
        self.model_lbl.setObjectName("info_warn")
        self.model_lbl.setAlignment(Qt.AlignCenter)
        hdr_center.addWidget(title)
        hdr_center.addWidget(self.model_lbl)
        hdr_row.addLayout(hdr_center, 1)

        import webbrowser
        btn_discord = QPushButton("Discord")
        btn_discord.setFixedSize(80, 30)
        btn_discord.setStyleSheet(
            "QPushButton { background: #5865F2; color: white; border: none; "
            "border-radius: 6px; font-size: 12px; font-weight: bold; }"
            "QPushButton:hover { background: #4752C4; }"
        )
        btn_discord.clicked.connect(
            lambda: webbrowser.open("https://discord.gg/FEXhA3cQjP"))
        hdr_row.addWidget(btn_discord, 0, Qt.AlignTop)

        root_vbox.addLayout(hdr_row)

        # ── Top row: reference + settings ──
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Reference group
        ref_grp = QGroupBox("Reference Voice  —  load or record")
        ref_vbox = QVBoxLayout(ref_grp)
        ref_vbox.setSpacing(6)

        btn_row = QHBoxLayout()
        self.btn_load   = QPushButton("📂  Load Audio File")
        self.btn_record = QPushButton("🎙  Record from Mic")
        self.btn_record.setObjectName("record")
        self.btn_clear  = QPushButton("✕")
        self.btn_clear.setMaximumWidth(36)
        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_record)
        btn_row.addWidget(self.btn_clear)
        ref_vbox.addLayout(btn_row)

        self.ref_wave = WaveformCanvas(color="#4499ff")
        ref_vbox.addWidget(self.ref_wave)

        info_row = QHBoxLayout()
        self.ref_info   = QLabel("No reference audio loaded")
        self.ref_info.setObjectName("info_dim")
        self.btn_play_ref = QPushButton("▶  Play")
        self.btn_play_ref.setMaximumWidth(80)
        self.btn_play_ref.setEnabled(False)
        info_row.addWidget(self.ref_info, 1)
        info_row.addWidget(self.btn_play_ref)
        ref_vbox.addLayout(info_row)

        # Mic level bar (hidden when not recording)
        self.mic_bar = QProgressBar()
        self.mic_bar.setRange(0, 100)
        self.mic_bar.setValue(0)
        self.mic_bar.setFixedHeight(5)
        self.mic_bar.setTextVisible(False)
        self.mic_bar.setStyleSheet(
            "QProgressBar::chunk { background: #d93025; } QProgressBar { border-color: #e8a0a0; }")
        self.mic_bar.setVisible(False)
        ref_vbox.addWidget(self.mic_bar)

        top_row.addWidget(ref_grp, 3)

        # Settings group
        set_grp = QGroupBox("Settings")
        set_form = QVBoxLayout(set_grp)
        set_form.setSpacing(10)

        # Language
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Language:"))
        self.lang_box = QComboBox()
        for name in LANGUAGES:
            self.lang_box.addItem(name)
        lang_row.addWidget(self.lang_box, 1)
        set_form.addLayout(lang_row)

        # ── Indonesian Chatterbox panel (shown only when Indonesian selected) ──
        self.chatterbox_panel = QWidget()
        cb_vbox = QVBoxLayout(self.chatterbox_panel)
        cb_vbox.setContentsMargins(0, 0, 0, 0)
        cb_vbox.setSpacing(6)

        self.cb_status_lbl = QLabel("Indonesian voice model will load on first Generate.")
        self.cb_status_lbl.setObjectName("info_warn")
        self.cb_status_lbl.setWordWrap(True)
        cb_vbox.addWidget(self.cb_status_lbl)

        cb_note = QLabel(
            "Native Indonesian accent voice cloning.\n"
            "First run: ~5 GB model download (one-time only)."
        )
        cb_note.setObjectName("info_dim")
        cb_note.setWordWrap(True)
        cb_vbox.addWidget(cb_note)

        set_form.addWidget(self.chatterbox_panel)
        self.chatterbox_panel.setVisible(True)   # Indonesian is default

        set_form.addWidget(self._separator())

        # Temperature
        temp_row = QHBoxLayout()
        temp_row.addWidget(QLabel("Expressiveness:"))
        self.temp_sl  = QSlider(Qt.Horizontal)
        self.temp_sl.setRange(30, 90)
        self.temp_sl.setValue(65)
        self.temp_lbl = QLabel("0.65")
        self.temp_lbl.setMinimumWidth(34)
        temp_row.addWidget(self.temp_sl, 1)
        temp_row.addWidget(self.temp_lbl)
        set_form.addLayout(temp_row)

        # Speed
        spd_row = QHBoxLayout()
        spd_row.addWidget(QLabel("Speed:"))
        self.spd_sl   = QSlider(Qt.Horizontal)
        self.spd_sl.setRange(50, 200)
        self.spd_sl.setValue(100)
        self.spd_lbl  = QLabel("1.00×")
        self.spd_lbl.setMinimumWidth(34)
        spd_row.addWidget(self.spd_sl, 1)
        spd_row.addWidget(self.spd_lbl)
        set_form.addLayout(spd_row)

        set_form.addStretch()
        top_row.addWidget(set_grp, 2)
        root_vbox.addLayout(top_row)

        # ── Sample text — compact inline panel ──
        sample_frame = QFrame()
        sample_frame.setStyleSheet(
            "QFrame { background:#ffffff; border:1px solid #d2d2d7;"
            "border-radius:8px; padding:0px; }")
        sf_vbox = QVBoxLayout(sample_frame)
        sf_vbox.setContentsMargins(14, 10, 14, 10)
        sf_vbox.setSpacing(6)

        sample_hdr = QHBoxLayout()
        sample_lbl = QLabel("Read this aloud while recording:")
        sample_lbl.setObjectName("sample_header")
        self.btn_next_sample = QPushButton("Next")
        self.btn_next_sample.setMaximumWidth(60)
        self.btn_next_sample.setStyleSheet(
            "font-size:11px; padding:3px 10px; min-height:20px;"
            "background:#f0f0f5; border:1px solid #d2d2d7;")
        sample_hdr.addWidget(sample_lbl)
        sample_hdr.addStretch()
        sample_hdr.addWidget(self.btn_next_sample)
        sf_vbox.addLayout(sample_hdr)

        self.sample_text_lbl = QLabel("")
        self.sample_text_lbl.setWordWrap(True)
        self.sample_text_lbl.setStyleSheet(
            "background:transparent; border:none; padding:2px 0px;"
            "color:#3a3a4a; font-size:14px; font-style:italic;")
        self.sample_text_lbl.setMinimumHeight(20)
        sf_vbox.addWidget(self.sample_text_lbl)

        self._sample_idx = -1
        root_vbox.addWidget(sample_frame)

        # ── Text input ──
        txt_grp = QGroupBox("Text to Speak")
        txt_vbox = QVBoxLayout(txt_grp)
        txt_vbox.setSpacing(4)
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Type the text you want spoken in the cloned voice...\n"
            "Long texts are automatically split into sentences.")
        self.text_edit.setMinimumHeight(70)
        self.text_edit.setMaximumHeight(120)
        txt_vbox.addWidget(self.text_edit)
        self.char_lbl = QLabel("0 characters")
        self.char_lbl.setObjectName("info_dim")
        txt_vbox.addWidget(self.char_lbl)
        root_vbox.addWidget(txt_grp)

        # ── Generate button ──
        self.btn_generate = QPushButton("🎤  Generate Cloned Voice")
        self.btn_generate.setObjectName("primary")
        self.btn_generate.setEnabled(False)
        root_vbox.addWidget(self.btn_generate)

        self.gen_progress = QProgressBar()
        self.gen_progress.setRange(0, 0)   # indeterminate / pulsing
        self.gen_progress.setFixedHeight(4)
        self.gen_progress.setTextVisible(False)
        self.gen_progress.setVisible(False)
        root_vbox.addWidget(self.gen_progress)

        # ── Output ──
        out_grp = QGroupBox("Output")
        out_vbox = QVBoxLayout(out_grp)
        out_vbox.setSpacing(8)

        self.out_wave = WaveformCanvas(color="#44cc88")
        out_vbox.addWidget(self.out_wave)

        out_btns = QHBoxLayout()
        self.btn_play_out = QPushButton("▶  Play")
        self.btn_stop     = QPushButton("⏹  Stop")
        self.btn_save     = QPushButton("💾  Save WAV")
        for b in (self.btn_play_out, self.btn_stop, self.btn_save):
            b.setEnabled(False)
        out_btns.addWidget(self.btn_play_out)
        out_btns.addWidget(self.btn_stop)
        out_btns.addWidget(self.btn_save)
        out_btns.addStretch()
        out_vbox.addLayout(out_btns)
        root_vbox.addWidget(out_grp)

        # ── Status bar ──
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Loading voice model...")

        # ── Connections ──
        self.btn_load.clicked.connect(self._on_load_ref)
        self.btn_record.clicked.connect(self._on_toggle_record)
        self.btn_clear.clicked.connect(self._on_clear_ref)
        self.btn_play_ref.clicked.connect(self._on_play_ref)
        self.btn_generate.clicked.connect(self._on_generate)
        self.btn_play_out.clicked.connect(self._on_play_out)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_save.clicked.connect(self._on_save)

        self.temp_sl.valueChanged.connect(
            lambda v: self.temp_lbl.setText(f"{v / 100:.2f}")
        )
        self.spd_sl.valueChanged.connect(
            lambda v: self.spd_lbl.setText(f"{v / 100:.2f}×")
        )
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.lang_box.currentTextChanged.connect(self._on_lang_changed)
        self.btn_next_sample.clicked.connect(self._show_next_sample)
        self._show_next_sample()

    @staticmethod
    def _separator():
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e0e0e5;")
        return sep

    def _show_next_sample(self):
        lang = self.lang_box.currentText()
        texts = SAMPLE_TEXTS.get(lang, SAMPLE_TEXTS["English"])
        self._sample_idx = (self._sample_idx + 1) % len(texts)
        self.sample_text_lbl.setText(texts[self._sample_idx])

    def _on_lang_changed(self, lang_name: str):
        is_indonesian = (lang_name == "Indonesian")
        self.chatterbox_panel.setVisible(is_indonesian)
        self._sample_idx = -1
        self._show_next_sample()
        self._refresh_generate_btn()

    # ── Model Loading ─────────────────────────────────────────────────────────

    def _load_model(self):
        cfg = self.app_config
        model_dir = cfg.get_model_dir() if cfg else XTTS_MODEL_DIR
        if not model_dir.exists() or not (model_dir / "model.pth").exists():
            from model_downloader import StorageCheckDialog, ModelDownloadDialog

            storage_dlg = StorageCheckDialog(model_dir, cfg, self)
            if storage_dlg.exec_() != QDialog.Accepted or not storage_dlg.accepted_download:
                self.model_lbl.setText("Model download cancelled.")
                self.model_lbl.setObjectName("info_warn")
                return
            model_dir = storage_dlg.dest_dir

            self.model_lbl.setText("Downloading voice model for first use...")
            dlg = ModelDownloadDialog(model_dir, self)
            dlg.exec_()
            if not dlg.succeeded:
                self.model_lbl.setText("Model download failed.")
                self.model_lbl.setObjectName("info_warn")
                return

        self._loader = ModelLoaderThread(model_dir)
        self._loader.status.connect(
            lambda s: self.statusBar().showMessage(s))
        self._loader.finished.connect(self._on_model_ready)
        self._loader.error.connect(self._on_model_error)
        self._loader.start()

    def _on_model_ready(self, model, config, device):
        self.model  = model
        self.config = config
        self.device = device
        device_label = "GPU" if device == "cuda" else "CPU"
        self.model_lbl.setText(f"Voice model ready  ({device_label})")
        self.model_lbl.setObjectName("info_ok")
        self.statusBar().showMessage(f"Model loaded [{device_label}]  |  Output: 24 kHz")
        self._refresh_generate_btn()

    def _on_model_error(self, tb: str):
        short = tb.strip().splitlines()[-1]
        self.model_lbl.setText(f"✗  {short}")
        self.model_lbl.setObjectName("info_warn")
        self.statusBar().showMessage("Model load failed — see error dialog")
        QMessageBox.critical(self, "Model Load Error",
                             "Failed to load voice model:\n\n" + tb[-1800:])

    # ── Reference Audio ───────────────────────────────────────────────────────

    def _on_load_ref(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Reference Audio", "",
            "Audio Files (*.wav *.mp3 *.flac *.ogg *.m4a *.aac)")
        if path:
            self._set_ref(path)

    def _set_ref(self, path: str):
        try:
            wav, sr = sf.read(path, always_2d=False)
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            wav = wav.astype(np.float32)
            # Normalize
            m = np.abs(wav).max()
            if m > 0:
                wav = wav / m * 0.95

            self.ref_wav  = wav
            self.ref_sr   = sr
            self.ref_path = path

            dur = len(wav) / sr
            name = Path(path).name
            self.ref_info.setText(f"📎  {name}   {dur:.1f} s   {sr} Hz")
            self.ref_info.setObjectName("info_ok")
            self.btn_play_ref.setEnabled(True)
            self.ref_wave.plot_wave(wav, sr)

            spd_val, expr_val = self._analyze_voice(wav, sr)
            self.spd_sl.setValue(spd_val)
            self.temp_sl.setValue(expr_val)

            if dur < 3:
                self.statusBar().showMessage(
                    "⚠  Reference is very short (<3 s). Use 5–15 s for best quality.")
            elif dur > 30:
                self.statusBar().showMessage(
                    f"Reference loaded ({dur:.0f} s). Only first 30 s will be used for conditioning.")
            else:
                self.statusBar().showMessage(f"Reference loaded: {name}  ({dur:.1f} s)")

        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Cannot load audio:\n{e}")

        self._refresh_generate_btn()

    def _analyze_voice(self, wav: np.ndarray, sr: int):
        """Estimate speaking speed and expressiveness from audio.
        Returns (speed_slider_val: int 50-200, expr_slider_val: int 30-90).
        """
        duration = len(wav) / sr
        if duration < 1.0:
            return 100, 50

        # -- Speed: count syllable-like energy peaks per second --
        frame_len = max(1, int(sr * 0.01))  # 10ms frames
        n_frames = len(wav) // frame_len
        if n_frames < 20:
            return 100, 50

        frames = wav[:n_frames * frame_len].reshape(n_frames, frame_len)
        energy = np.sqrt(np.mean(frames ** 2, axis=1))

        kernel = np.ones(7) / 7.0
        energy_sm = np.convolve(energy, kernel, mode="same")
        thresh = np.mean(energy_sm) * 0.35

        # Local maxima above threshold with min 100ms gap between peaks
        min_gap = 10  # 10 frames = 100ms
        peaks = 0
        last_pk = -min_gap
        for i in range(1, len(energy_sm) - 1):
            if (energy_sm[i] > energy_sm[i - 1]
                    and energy_sm[i] >= energy_sm[i + 1]
                    and energy_sm[i] > thresh
                    and i - last_pk >= min_gap):
                peaks += 1
                last_pk = i

        syl_per_sec = peaks / duration if duration > 0 else 4.0
        speed = syl_per_sec / 4.0
        speed_val = int(max(50, min(200, speed * 100)))

        # -- Expressiveness: pitch variance via autocorrelation --
        hop = int(sr * 0.02)
        win = int(sr * 0.04)
        f0_list = []
        for start in range(0, len(wav) - win, hop):
            seg = wav[start:start + win]
            if np.sqrt(np.mean(seg ** 2)) < thresh * 0.01:
                continue
            seg = seg - np.mean(seg)
            corr = np.correlate(seg, seg, mode="full")
            corr = corr[len(corr) // 2:]
            if corr[0] == 0:
                continue
            lo = max(1, int(sr / 500))
            hi = min(len(corr), int(sr / 60))
            if lo >= hi:
                continue
            region = corr[lo:hi]
            pk = int(np.argmax(region)) + lo
            if corr[pk] > 0.25 * corr[0]:
                f0 = sr / pk
                if 60 < f0 < 500:
                    f0_list.append(f0)

        if len(f0_list) < 5:
            return speed_val, 50

        log_f0 = np.log2(np.array(f0_list))
        f0_std = float(np.std(log_f0))
        expr = 0.30 + (f0_std - 0.05) * 2.75
        expr_val = int(max(30, min(90, expr * 100)))

        return speed_val, expr_val

    def _on_clear_ref(self):
        sd.stop()
        self.ref_wav = self.ref_sr = self.ref_path = None
        self.ref_info.setText("No reference audio loaded")
        self.ref_info.setObjectName("info_dim")
        self.btn_play_ref.setEnabled(False)
        self.ref_wave.plot_wave(None)
        self._refresh_generate_btn()

    # ── Microphone Recording ──────────────────────────────────────────────────

    def _on_toggle_record(self):
        if self._rec_thread and self._rec_thread.isRunning():
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._rec_thread = RecordThread(samplerate=22050)
        self._rec_thread.finished.connect(self._on_rec_done)
        self._rec_thread.level_rms.connect(
            lambda v: self.mic_bar.setValue(int(min(100, v * 800))))
        self.btn_record.setText("⏹  Stop Recording")
        self.btn_record.setObjectName("recording")
        self.btn_record.setStyleSheet(
            "background:#d93025; border-color:#bb1a10; color:#ffffff; font-weight:bold;")
        self.mic_bar.setVisible(True)
        self.mic_bar.setValue(0)
        self.statusBar().showMessage("🔴  Recording…  speak clearly, then click Stop")
        self._rec_thread.start()

    def _stop_recording(self):
        if self._rec_thread:
            self._rec_thread.stop()
        self.btn_record.setText("🎙  Record from Mic")
        self.btn_record.setObjectName("record")
        self.btn_record.setStyleSheet("")
        self.mic_bar.setVisible(False)
        self.statusBar().showMessage("Saving recording…")

    def _on_rec_done(self, wav: np.ndarray, sr: int):
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, wav, sr)
        tmp.close()
        self._set_ref(tmp.name)
        name = Path(tmp.name).name
        self.ref_info.setText(f"🎙  Recorded  {len(wav)/sr:.1f} s  |  {sr} Hz")
        self.ref_info.setObjectName("info_ok")

    # ── Generation ────────────────────────────────────────────────────────────

    def _on_text_changed(self):
        txt = self.text_edit.toPlainText()
        chunks = split_text_into_chunks(txt) if txt.strip() else []
        n = len(chunks)
        self.char_lbl.setText(
            f"{len(txt)} chars"
            + (f"  —  will generate in {n} chunk{'s' if n != 1 else ''}" if n > 1 else ""))
        self._refresh_generate_btn()

    def _refresh_generate_btn(self):
        lang_name = self.lang_box.currentText()
        has_text  = bool(self.text_edit.toPlainText().strip())
        if lang_name == "Indonesian":
            # Chatterbox voice clone: needs reference audio + text
            ready = has_text and self.ref_path is not None
        else:
            ready = (self.model is not None
                     and self.ref_path is not None
                     and has_text)
        self.btn_generate.setEnabled(ready)

    def _on_generate(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        lang_name = self.lang_box.currentText()

        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳  Generating…")
        self.gen_progress.setRange(0, 0)
        self.gen_progress.setVisible(True)

        if lang_name == "Indonesian":
            text = preprocess_indonesian(text)
            if self._chatterbox is None:
                self._start_chatterbox(pending_text=text)
            elif self._chatterbox.is_ready:
                self._do_chatterbox_generate(text)
            elif self._chatterbox.is_running:
                self._pending_chatterbox_text = text
                self.statusBar().showMessage("Indonesian voice model is loading, please wait...")
            else:
                self._start_chatterbox(pending_text=text)
            return   # result arrives via on_audio_done callback
        else:
            language = LANGUAGES[lang_name]
            temp     = self.temp_sl.value() / 100.0
            speed    = self.spd_sl.value()  / 100.0
            self._gen_thread = GenerateThread(
                self.model, self.config, text,
                [self.ref_path], language, temp, speed,
            )

        self._gen_thread.finished.connect(self._on_gen_done)
        self._gen_thread.error.connect(self._on_gen_error)
        self._gen_thread.status.connect(self.statusBar().showMessage)
        self._gen_thread.start()

    def _on_gen_done(self, wav: np.ndarray, sr: int):
        self.output_wav = wav
        self.output_sr  = sr
        self.out_wave.plot_wave(wav, sr)
        self.btn_play_out.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_save.setEnabled(True)
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🎤  Generate Cloned Voice")
        self.gen_progress.setVisible(False)
        dur = len(wav) / sr
        self.statusBar().showMessage(
            f"✓  Done — {dur:.1f} s generated at {sr} Hz  |  Click ▶ Play to listen")
        # Auto-play
        self._play(wav, sr)

    def _on_gen_error(self, tb: str):
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🎤  Generate Cloned Voice")
        self.gen_progress.setVisible(False)
        if self._cb_dialog:
            self._cb_dialog.accept()
            self._cb_dialog = None
        self.statusBar().showMessage("Generation failed.")
        QMessageBox.critical(self, "Generation Error",
                             "Failed to generate speech:\n\n" + tb[-2000:])

    def _start_chatterbox(self, pending_text: str = ""):
        self._pending_chatterbox_text = pending_text
        self.gen_progress.setVisible(False)

        self._cb_dialog = ChatterboxLoadDialog(self)
        self._cb_dialog.btn_cancel.clicked.connect(self._cb_dialog.reject)
        self._cb_dialog.rejected.connect(self._cancel_chatterbox)
        self._cb_dialog.show()

        self._chatterbox = ChatterboxManager(
            on_status     = self._on_cb_status,
            on_ready      = self._on_chatterbox_ready,
            on_error      = self._on_gen_error,
            on_audio_done = self._on_gen_done,
            on_progress   = self._on_cb_progress,
        )
        self.btn_generate.setText("Loading Indonesian model...")
        self.statusBar().showMessage(
            "Loading Indonesian voice model (first run: ~5 GB download)...")
        self._chatterbox.start()

    def _cancel_chatterbox(self):
        if self._chatterbox:
            self._chatterbox.stop()
            self._chatterbox = None
        dlg = self._cb_dialog
        self._cb_dialog = None
        if dlg:
            dlg.close()
        self.btn_generate.setEnabled(True)
        self.btn_generate.setText("🎤  Generate Cloned Voice")
        self.gen_progress.setVisible(False)
        self.statusBar().showMessage("Indonesian model loading cancelled.")

    def _on_cb_status(self, msg):
        self.statusBar().showMessage(msg)
        if self._cb_dialog and self._cb_dialog.isVisible():
            self._cb_dialog.set_status(msg)

    def _on_chatterbox_ready(self):
        self.cb_status_lbl.setText("Indonesian voice model ready.")
        self.cb_status_lbl.setObjectName("info_ok")
        if self._cb_dialog:
            self._cb_dialog.accept()
            self._cb_dialog = None
        if getattr(self, "_pending_chatterbox_text", ""):
            self.btn_generate.setText("⏳  Generating…")
            self.gen_progress.setRange(0, 0)
            self.gen_progress.setVisible(True)
            self._do_chatterbox_generate(self._pending_chatterbox_text)
            self._pending_chatterbox_text = ""

    def _do_chatterbox_generate(self, text: str):
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        self._chatterbox.generate(
            text, self.ref_path, tmp.name,
            exaggeration=self.temp_sl.value() / 100.0,
        )

    def _on_cb_progress(self, pct, detail=""):
        if self._cb_dialog and self._cb_dialog.isVisible():
            self._cb_dialog.set_progress(pct, detail)
        if detail:
            self.statusBar().showMessage(detail)
        if pct < 0:
            if self.gen_progress.maximum() != 0:
                self.gen_progress.setRange(0, 0)
        else:
            if self.gen_progress.maximum() == 0:
                self.gen_progress.setRange(0, 100)
            self.gen_progress.setValue(pct)

    # ── Playback ─────────────────────────────────────────────────────────────

    def _play(self, wav: np.ndarray, sr: int):
        sd.stop()
        sd.play(wav.astype(np.float32), sr)

    def _on_play_ref(self):
        if self.ref_wav is not None:
            self._play(self.ref_wav, self.ref_sr)

    def _on_play_out(self):
        if self.output_wav is not None:
            self._play(self.output_wav, self.output_sr)

    def _on_stop(self):
        sd.stop()

    # ── Save ─────────────────────────────────────────────────────────────────

    def _on_save(self):
        if self.output_wav is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Cloned Audio", "cloned_voice.wav", "WAV (*.wav)")
        if path:
            sf.write(path, self.output_wav, self.output_sr)
            self.statusBar().showMessage(f"Saved → {path}")

    # ── Cleanup ───────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        sd.stop()
        if self._rec_thread and self._rec_thread.isRunning():
            self._rec_thread.stop()
            self._rec_thread.wait(3000)
        if self._chatterbox is not None:
            self._chatterbox.stop()
        event.accept()


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Voice Clonner")
    app.setStyle("Fusion")

    cfg = Config.load()
    cfg.increment_open_count()
    cfg.save()

    from modals import FirstTimeSetupDialog, UpdateCheckThread, UpdateDialog

    if not cfg.first_run_complete:
        dlg = FirstTimeSetupDialog()
        if dlg.exec_() == QDialog.Accepted:
            cfg.first_run_complete = True
            cfg.save()
        else:
            sys.exit(0)

    # Update check (non-blocking on failure, blocking on required update)
    _update_result = [None]

    def _on_update_result(needs_update, ver, desc, url, required):
        _update_result[0] = (needs_update, ver, desc, url, required)

    checker = UpdateCheckThread()
    checker.result.connect(_on_update_result)
    checker.start()
    checker.wait(5000)

    if _update_result[0] and _update_result[0][0]:
        _, ver, desc, url, required = _update_result[0]
        if required or ver != cfg.last_skipped_version:
            dlg = UpdateDialog(ver, desc, url, required)
            result = dlg.exec_()
            if result == QDialog.Rejected and not required:
                cfg.last_skipped_version = ver
                cfg.save()

    win = MainWindow(app_config=cfg)
    win.show()

    from PyQt5.QtCore import QTimer
    from modals import DiscordDialog

    def _show_discord():
        try:
            dlg = DiscordDialog(win)
            dlg.raise_()
            dlg.activateWindow()
            dlg.exec_()
        except Exception:
            pass

    QTimer.singleShot(2000, _show_discord)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
