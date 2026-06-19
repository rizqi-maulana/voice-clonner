"""Auto-download XTTS v2 model from HuggingFace on first launch."""
from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QMessageBox,
)
from PyQt5.QtCore import Qt

REPO_ID = "coqui/XTTS-v2"
MODEL_FILES = [
    ("config.json",       "Configuration",   4_400),
    ("vocab.json",        "Vocabulary",      360_000),
    ("speakers_xtts.pth", "Speaker data",    7_600_000),
    ("dvae.pth",          "DVAE encoder",    210_000_000),
    ("model.pth",         "Main model",      1_880_000_000),
]

HF_BASE = f"https://huggingface.co/{REPO_ID}/resolve/main"


class ModelDownloadThread(QThread):
    progress = pyqtSignal(str, int, int)  # filename, bytes_done, bytes_total
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
    """Modal dialog for downloading the voice model on first launch."""

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
