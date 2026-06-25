"""
Chatterbox-TTS-Indonesian server.
Runs as a persistent process: reads JSON requests from stdin, writes JSON responses to stdout.

Protocol:
  stdin  <- {"type":"generate","text":"...","ref":"path.wav","out":"path.wav","exaggeration":0.5}
  stdin  <- {"type":"quit"}
  stdout -> {"type":"status","msg":"..."}
  stdout -> {"type":"ready","sr":24000}
  stdout -> {"type":"success","path":"path.wav"}
  stdout -> {"type":"error","msg":"...","tb":"..."}
"""
import sys, json, os, warnings, traceback as tb_mod, io
from pathlib import Path

# Force UTF-8 stdout on Windows (pipe defaults to cp1252).
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Suppress noisy HuggingFace warnings — public models don't need a token.
warnings.filterwarnings("ignore", message=".*unauthenticated.*")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", category=FutureWarning, module="diffusers")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


def emit(obj: dict):
    print(json.dumps(obj, ensure_ascii=False), flush=True)


# ── Model directories ────────────────────────────────────────────────────────
_CACHE = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))
BASE_DIR = _CACHE / "chatterbox_base"
INDO_DIR = _CACHE / "chatterbox_indo"


_ipv4_patched = False

def _force_ipv4():
    global _ipv4_patched
    if _ipv4_patched:
        return
    try:
        import urllib3.util.connection as urllib3_conn
        urllib3_conn.HAS_IPV6 = False
    except Exception:
        pass
    _ipv4_patched = True


def _download_file(repo_id, filename, dest_dir, label, idx, total):
    """Download one file from HuggingFace with retry and resume support."""
    import requests as _req
    import time

    _force_ipv4()

    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    local_path = dest_dir / filename

    if local_path.exists() and local_path.stat().st_size > 0:
        emit({"type": "status", "msg": f"Setting up component {idx}/{total}..."})
        return str(local_path)

    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    emit({"type": "status", "msg": f"Setting up component {idx}/{total}..."})

    tmp = str(local_path) + ".tmp"
    max_retries = 5
    backoff = [5, 10, 20, 40, 60]

    for attempt in range(max_retries):
        try:
            downloaded = 0
            headers = {}
            if os.path.exists(tmp):
                downloaded = os.path.getsize(tmp)
                headers["Range"] = f"bytes={downloaded}-"

            r = _req.get(url, stream=True, timeout=(30, 300),
                         allow_redirects=True, headers=headers)

            if r.status_code == 416:
                break

            r.raise_for_status()

            if r.status_code == 200:
                total_bytes = int(r.headers.get("content-length", 0))
                downloaded = 0
                mode = "wb"
            else:
                content_range = r.headers.get("content-range", "")
                if "/" in content_range:
                    total_bytes = int(content_range.split("/")[-1])
                else:
                    total_bytes = 0
                mode = "ab"

            size_mb = int(total_bytes / (1024 * 1024)) if total_bytes else 0
            step = 5 if size_mb > 100 else 1
            last_mb = -1

            with open(tmp, mode) as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    done_mb = int(downloaded / (1024 * 1024))
                    if done_mb >= last_mb + step:
                        last_mb = done_mb
                        pct = int(100 * downloaded / total_bytes) if total_bytes else 0
                        emit({"type": "progress", "pct": pct,
                              "msg": f"Setting up... {pct}%"})

            break
        except Exception:
            if attempt < max_retries - 1:
                wait = backoff[attempt]
                emit({"type": "status",
                      "msg": f"Connection issue, retrying in {wait}s..."})
                time.sleep(wait)
            else:
                raise ConnectionError(
                    "Could not connect to the download server. "
                    "Please check your internet connection and try again."
                )

    os.replace(tmp, str(local_path))
    emit({"type": "progress", "pct": 100,
          "msg": f"Setting up... 100%"})
    emit({"type": "status", "msg": f"Setting up component {idx}/{total}..."})
    return str(local_path)


def load_model():
    emit({"type": "status", "msg": "Preparing..."})
    import torch

    emit({"type": "status", "msg": "Loading components..."})
    from chatterbox.tts import ChatterboxTTS
    from safetensors.torch import load_file

    device = "cuda" if torch.cuda.is_available() else "cpu"

    downloads = [
        ("ResembleAI/chatterbox", "tokenizer.json",    BASE_DIR, "base model"),
        ("ResembleAI/chatterbox", "conds.pt",           BASE_DIR, "base model"),
        ("ResembleAI/chatterbox", "ve.safetensors",     BASE_DIR, "base model"),
        ("ResembleAI/chatterbox", "s3gen.safetensors",  BASE_DIR, "base model (~1 GB)"),
        ("ResembleAI/chatterbox", "t3_cfg.safetensors", BASE_DIR, "base model (~2 GB)"),
        ("grandhigh/Chatterbox-TTS-Indonesian", "t3_cfg.safetensors", INDO_DIR, "Indo fine-tune (~2 GB)"),
    ]
    n = len(downloads)
    for i, (repo, fname, dest, label) in enumerate(downloads, 1):
        _download_file(repo, fname, dest, label, i, n)

    import perth
    if not getattr(perth, 'PerthImplicitWatermarker', None):
        class _NoOpWatermarker:
            def __init__(self, *a, **kw): pass
            def watermark(self, wav, *a, **kw): return wav
            def apply_watermark(self, wav, *a, **kw): return wav
            def detect(self, *a, **kw): return {}
        perth.PerthImplicitWatermarker = _NoOpWatermarker

    emit({"type": "status", "msg": "Loading voice model..."})
    model = ChatterboxTTS.from_local(BASE_DIR, device)

    emit({"type": "status", "msg": "Applying language configuration..."})
    indo_t3 = load_file(INDO_DIR / "t3_cfg.safetensors", device="cpu")
    model.t3.load_state_dict(indo_t3)

    sr = int(getattr(model, "sr", 24000))
    return model, sr


MAX_CHUNK_CHARS = 200

def _split_text(text: str) -> list:
    """Split text into chunks at sentence boundaries, each under MAX_CHUNK_CHARS."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if cur and len(cur) + len(s) + 1 > MAX_CHUNK_CHARS:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip() if cur else s
    if cur:
        chunks.append(cur)

    result = []
    import re as _re
    for chunk in chunks:
        if len(chunk) <= MAX_CHUNK_CHARS:
            result.append(chunk)
        else:
            parts = _re.split(r'(?<=,)\s+', chunk)
            sub = ""
            for p in parts:
                if sub and len(sub) + len(p) + 1 > MAX_CHUNK_CHARS:
                    result.append(sub)
                    sub = p
                else:
                    sub = f"{sub} {p}".strip() if sub else p
            if sub:
                result.append(sub)
    return result if result else [text]


def generate_audio(model, sr, text: str, ref_path: str, out_path: str,
                   exaggeration: float = 0.5):
    import torch, torchaudio

    chunks = _split_text(text)
    total = len(chunks)
    wavs = []
    # 0.3s silence between chunks for natural pauses
    silence = torch.zeros(1, int(sr * 0.3))

    for i, chunk in enumerate(chunks, 1):
        emit({"type": "status",
              "msg": f"Generating ({i}/{total}): {chunk[:50]}..."})
        wav = model.generate(
            chunk,
            audio_prompt_path=ref_path,
            exaggeration=exaggeration,
        )
        if hasattr(wav, "dim") and wav.dim() == 1:
            wav = wav.unsqueeze(0)
        wavs.append(wav.cpu().float())
        if i < total:
            wavs.append(silence)

    full_wav = torch.cat(wavs, dim=-1)
    torchaudio.save(out_path, full_wav, sr)


def main():
    emit({"type": "status", "msg": "Starting voice engine..."})
    try:
        model, sr = load_model()
    except (ConnectionError, OSError) as e:
        emit({"type": "error", "msg": str(e)})
        sys.exit(1)
    except Exception as e:
        emit({"type": "error", "msg": str(e), "tb": tb_mod.format_exc()})
        sys.exit(1)

    emit({"type": "ready", "sr": sr})

    buf = ""
    while True:
        try:
            chunk = sys.stdin.readline()
        except (EOFError, KeyboardInterrupt):
            break
        if not chunk:
            break
        buf += chunk
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as e:
                emit({"type": "error", "msg": f"Invalid JSON: {e}"})
                continue

            if req.get("type") == "quit":
                return

            if req.get("type") == "generate":
                try:
                    generate_audio(
                        model, sr,
                        req["text"], req["ref"], req["out"],
                        float(req.get("exaggeration", 0.5)),
                    )
                    emit({"type": "success", "path": req["out"]})
                except Exception as e:
                    emit({"type": "error", "msg": str(e), "tb": tb_mod.format_exc()})


if __name__ == "__main__":
    main()
