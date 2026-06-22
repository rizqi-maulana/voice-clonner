"""Auto-download XTTS v2 model from HuggingFace on first launch."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QMessageBox, QFileDialog, QFrame,
)

REPO_ID = "coqui/XTTS-v2"
MODEL_FILES = [
    ("config.json",       "Configuration",   4_400),
    ("vocab.json",        "Vocabulary",      360_000),
    ("speakers_xtts.pth", "Speaker data",    7_600_000),
    ("dvae.pth",          "DVAE encoder",    210_000_000),
    ("model.pth",         "Main model",      1_880_000_000),
]

TOTAL_MODEL_SIZE = sum(size for _, _, size in MODEL_FILES)
REQUIRED_GB = TOTAL_MODEL_SIZE / (1024 ** 3)

HF_BASE = f"https://huggingface.co/{REPO_ID}/resolve/main"


def _format_gb(b: int | float) -> str:
    return f"{b / (1024 ** 3):.1f} GB"


def _free_space(path: Path) -> int:
    try:
        p = path
        while not p.exists():
            p = p.parent
        return shutil.disk_usage(str(p)).free
    except OSError:
        return 0


class StorageCheckDialog(QDialog):
    """Pre-download dialog showing disk space and allowing location change."""

    def __init__(self, dest_dir: Path, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Storage")
        self.setFixedSize(520, 280)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        self._config = config
        self._dest_dir = dest_dir
        self._accepted = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 18)
        lay.setSpacing(10)

        title = QLabel("Voice model download")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1d1d1f;")
        lay.addWidget(title)

        desc = QLabel(
            "The voice model (~2 GB) needs to be downloaded once.\n"
            "Please make sure you have enough disk space."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #6e6e73;")
        lay.addWidget(desc)

        lay.addSpacing(6)

        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame { background: #f0f0f5; border: 1px solid #d2d2d7; "
            "border-radius: 8px; padding: 12px; }"
        )
        info_lay = QVBoxLayout(info_frame)
        info_lay.setSpacing(6)

        self._loc_label = QLabel()
        self._loc_label.setWordWrap(True)
        self._loc_label.setStyleSheet("font-size: 12px; color: #1d1d1f; border: none;")
        info_lay.addWidget(self._loc_label)

        self._space_label = QLabel()
        self._space_label.setStyleSheet("font-size: 12px; border: none;")
        info_lay.addWidget(self._space_label)

        needed = QLabel(f"Space needed:  ~{REQUIRED_GB:.1f} GB")
        needed.setStyleSheet("font-size: 12px; color: #1d1d1f; border: none;")
        info_lay.addWidget(needed)

        lay.addWidget(info_frame)

        self._warning_label = QLabel()
        self._warning_label.setWordWrap(True)
        self._warning_label.setStyleSheet("font-size: 12px; color: #d93025; font-weight: bold;")
        self._warning_label.hide()
        lay.addWidget(self._warning_label)

        lay.addStretch()

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(10)

        self._btn_change = QPushButton("Change Location")
        self._btn_change.setMaximumWidth(150)
        self._btn_change.setStyleSheet(
            "QPushButton { background: #e8e8ed; color: #1d1d1f; border: 1px solid #d2d2d7; "
            "border-radius: 6px; padding: 8px 16px; font-size: 13px; }"
            "QPushButton:hover { background: #d8d8dd; }"
        )
        btn_lay.addWidget(self._btn_change)

        btn_lay.addStretch()

        self._btn_cancel = QPushButton("Cancel")
        self._btn_cancel.setMaximumWidth(100)
        btn_lay.addWidget(self._btn_cancel)

        self._btn_download = QPushButton("Download")
        self._btn_download.setMaximumWidth(120)
        self._btn_download.setStyleSheet(
            "QPushButton { background: #0066cc; color: white; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-size: 13px; font-weight: bold; }"
            "QPushButton:hover { background: #0055aa; }"
            "QPushButton:disabled { background: #b0b0b5; }"
        )
        btn_lay.addWidget(self._btn_download)

        lay.addLayout(btn_lay)

        self._btn_change.clicked.connect(self._change_location)
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_download.clicked.connect(self._on_download)

        self._update_info()

    def _update_info(self):
        self._loc_label.setText(f"Storage location:  {self._dest_dir}")
        free = _free_space(self._dest_dir)
        free_gb = free / (1024 ** 3)
        self._space_label.setText(f"Available space:   {_format_gb(free)}")

        if free_gb < REQUIRED_GB + 0.5:
            self._space_label.setStyleSheet("font-size: 12px; color: #d93025; font-weight: bold; border: none;")
            self._warning_label.setText(
                "Not enough disk space! Please free up space or change the storage location."
            )
            self._warning_label.show()
            self._btn_download.setEnabled(False)
        else:
            self._space_label.setStyleSheet("font-size: 12px; color: #34a853; font-weight: bold; border: none;")
            self._warning_label.hide()
            self._btn_download.setEnabled(True)

    def _change_location(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Choose model storage folder", str(self._dest_dir.parent)
        )
        if folder:
            self._dest_dir = Path(folder) / "VoiceClonner" / "models" / "xtts-v2"
            self._config.custom_model_dir = str(self._dest_dir)
            self._config.save()
            self._update_info()

    def _on_download(self):
        self._accepted = True
        self.accept()

    @property
    def dest_dir(self) -> Path:
        return self._dest_dir

    @property
    def accepted_download(self) -> bool:
        return self._accepted


class ModelDownloadThread(QThread):
    progress = pyqtSignal(str, int, int)
    file_done = pyqtSignal(str)
    all_done = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, dest_dir: Path):
        super().__init__()
        self.dest_dir = dest_dir
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def run(self):
        import requests

        self.dest_dir.mkdir(parents=True, exist_ok=True)

        for filename, label, expected_size in MODEL_FILES:
            if self._cancel:
                return

            local_path = self.dest_dir / filename
            if local_path.exists() and local_path.stat().st_size > 0:
                self.file_done.emit(filename)
                continue

            url = f"{HF_BASE}/{filename}"
            try:
                r = requests.get(url, stream=True, timeout=60, allow_redirects=True)
                r.raise_for_status()
            except Exception as e:
                self.error.emit(f"Failed to download {filename}: {e}")
                return

            total = int(r.headers.get("content-length", expected_size))
            tmp = str(local_path) + ".tmp"
            downloaded = 0

            try:
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if self._cancel:
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            self.progress.emit(filename, downloaded, total)

                os.replace(tmp, str(local_path))
            except Exception as e:
                if os.path.exists(tmp):
                    os.remove(tmp)
                self.error.emit(f"Error writing {filename}: {e}")
                return

            self.file_done.emit(filename)

        self.all_done.emit()


class ModelDownloadDialog(QDialog):
    """Modal dialog for downloading the voice model."""

    def __init__(self, dest_dir: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading Voice Model")
        self.setFixedSize(500, 220)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowContextHelpButtonHint
            & ~Qt.WindowCloseButtonHint
        )

        self._success = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 24, 30, 20)
        lay.setSpacing(12)

        info = QLabel(
            "Downloading the voice model for the first time.\n"
            "This is about 2 GB and only needs to happen once."
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 14px; color: #1d1d1f;")
        lay.addWidget(info)

        self.file_lbl = QLabel("Preparing...")
        self.file_lbl.setStyleSheet("font-size: 13px; color: #6e6e73;")
        lay.addWidget(self.file_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #e8e8ed; border: 1px solid #d2d2d7;
                border-radius: 6px; height: 20px;
                text-align: center; font-size: 11px; color: #3a3a4a;
            }
            QProgressBar::chunk { background: #0066cc; border-radius: 5px; }
        """)
        lay.addWidget(self.progress_bar)

        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet("font-size: 12px; color: #8e8e93;")
        lay.addWidget(self.detail_lbl)

        lay.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setMaximumWidth(120)
        lay.addWidget(self.btn_cancel, 0, Qt.AlignCenter)

        self._thread = ModelDownloadThread(dest_dir)
        self._thread.progress.connect(self._on_progress)
        self._thread.file_done.connect(self._on_file_done)
        self._thread.all_done.connect(self._on_all_done)
        self._thread.error.connect(self._on_error)

        self.btn_cancel.clicked.connect(self._on_cancel)

    def exec_(self):
        self._thread.start()
        return super().exec_()

    def _on_progress(self, filename, done, total):
        pct = int(100 * done / total) if total > 0 else 0
        self.progress_bar.setValue(pct)
        done_mb = done // (1024 * 1024)
        total_mb = total // (1024 * 1024)
        self.file_lbl.setText(f"Downloading: {filename}")
        self.detail_lbl.setText(f"{done_mb} / {total_mb} MB  ({pct}%)")

    def _on_file_done(self, filename):
        self.file_lbl.setText(f"{filename}  [OK]")

    def _on_all_done(self):
        self._success = True
        self.accept()

    def _on_error(self, msg):
        QMessageBox.critical(self, "Download Error",
                             f"Failed to download model:\n\n{msg}")
        self.reject()

    def _on_cancel(self):
        self._thread.cancel()
        self._thread.wait(3000)
        self.reject()

    @property
    def succeeded(self):
        return self._success
