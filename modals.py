"""Startup modals: first-time setup, update checker, Discord community."""
from __future__ import annotations

import webbrowser
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from version import __version__

DISCORD_URL = "https://discord.gg/FEXhA3cQjP"
GITHUB_REPO = "rizqi-maulana/voice-clonner"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


# ─── First-Time Setup ────────────────────────────────────────────────────────

class FirstTimeSetupDialog(QDialog):
    """Mandatory first-launch modal. Cannot be closed until user scrolls to
    bottom and clicks Agree."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Voice Clonner")
        self.setFixedSize(580, 520)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 16)
        lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: #ffffff; }")
        lay.addWidget(scroll, 1)

        content = QWidget()
        content.setStyleSheet("background: #ffffff;")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(32, 28, 32, 28)
        c_lay.setSpacing(16)

        title = QLabel("Welcome to Voice Clonner")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1d1d1f; background: transparent;")
        title.setAlignment(Qt.AlignCenter)
        c_lay.addWidget(title)

        sections = [
            ("What is this app?",
             "Voice Clonner lets you clone any voice from a short audio recording. "
             "Simply load or record a reference voice, type the text you want spoken, "
             "and the app will generate speech that sounds like the reference speaker."),

            ("How to use",
             "1. Load an audio file or record your voice using the microphone.\n"
             "2. Select the language you want to generate speech in.\n"
             "3. Type or paste the text you want spoken.\n"
             "4. Click 'Generate' and wait for the result.\n"
             "5. Play the result, then save it as a WAV file if you're happy with it."),

            ("Supported Languages",
             "Indonesian, English, Spanish, French, German, Italian, Portuguese, "
             "Polish, Turkish, Russian, Dutch, Czech, Arabic, Chinese, Hungarian, "
             "Korean, Japanese, Hindi."),

            ("Disk Space Requirements",
             "The app needs to download voice models on first use:\n\n"
             "- Main voice model: ~2 GB (required for all languages except Indonesian)\n"
             "- Indonesian voice model: ~5 GB (downloaded when you first use Indonesian)\n\n"
             "Total disk space needed: up to ~7 GB.\n"
             "Models are downloaded once and cached locally."),

            ("Privacy & Processing",
             "All voice processing happens locally on your computer. "
             "No audio data is sent to external servers. "
             "The only network activity is downloading the voice models on first use "
             "and checking for app updates."),

            ("Important Notice",
             "This app is intended for creative, educational, and personal use. "
             "Please use it responsibly and respect the privacy and consent of others. "
             "Do not use this app to impersonate someone without their permission.\n\n"
             "By clicking 'I Agree' below, you acknowledge that you have read "
             "and understood the above information."),
        ]

        for heading, body in sections:
            h = QLabel(heading)
            h.setStyleSheet("font-size: 15px; font-weight: bold; color: #1d1d1f; background: transparent;")
            c_lay.addWidget(h)

            b = QLabel(body)
            b.setWordWrap(True)
            b.setStyleSheet("font-size: 13px; color: #3a3a4a; line-height: 1.5; background: transparent;")
            c_lay.addWidget(b)

        c_lay.addSpacing(20)
        scroll.setWidget(content)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e8e8ed;")
        lay.addWidget(sep)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(32, 12, 32, 0)
        btn_row.addStretch()

        self.btn_agree = QPushButton("I Agree")
        self.btn_agree.setEnabled(False)
        self.btn_agree.setMinimumWidth(140)
        self.btn_agree.setMinimumHeight(38)
        self.btn_agree.setStyleSheet("""
            QPushButton {
                background: #0066cc; color: #ffffff; border: none;
                border-radius: 8px; font-size: 14px; font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton:hover { background: #0077ee; }
            QPushButton:disabled { background: #b0c4de; color: #e8e8ee; }
        """)
        self.btn_agree.clicked.connect(self.accept)
        btn_row.addWidget(self.btn_agree)
        lay.addLayout(btn_row)

        self._scroll_bar = scroll.verticalScrollBar()
        self._scroll_bar.valueChanged.connect(self._check_scroll)

    def _check_scroll(self, value):
        if value >= self._scroll_bar.maximum() - 10:
            self.btn_agree.setEnabled(True)

    def closeEvent(self, event):
        event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            return
        super().keyPressEvent(event)


# ─── Update Checker ──────────────────────────────────────────────────────────

class UpdateCheckThread(QThread):
    result = pyqtSignal(bool, str, str, str, bool)  # needs_update, version, desc, url, required

    def run(self):
        import json
        try:
            import urllib.request
            req = urllib.request.Request(RELEASES_API, headers={"User-Agent": "VoiceClonner"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            tag = data.get("tag_name", "").lstrip("v")
            desc = data.get("body", "")
            url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest")

            if not tag:
                return

            current = tuple(int(x) for x in __version__.split("."))
            remote = tuple(int(x) for x in tag.split(".") if x.isdigit())

            if remote > current:
                is_required = "required" in desc.lower()
                self.result.emit(True, tag, desc, url, is_required)
        except Exception:
            pass


class UpdateDialog(QDialog):
    """Shows available update with Update / Update Later buttons."""

    def __init__(self, version: str, description: str, url: str,
                 is_required: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(480, 340)
        self.setModal(True)

        self._url = url

        if is_required:
            self.setWindowFlags(
                Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint
            )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 20)
        lay.setSpacing(14)

        title = QLabel(f"Version {version} is available!")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1d1d1f;")
        title.setAlignment(Qt.AlignCenter)
        lay.addWidget(title)

        if is_required:
            req_lbl = QLabel("This update is required to continue using the app.")
            req_lbl.setStyleSheet("font-size: 13px; color: #d93025; font-weight: bold;")
            req_lbl.setAlignment(Qt.AlignCenter)
            lay.addWidget(req_lbl)

        desc_lbl = QLabel(description[:800] if description else "A new version is available.")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            "font-size: 13px; color: #3a3a4a; background: #f5f5f7;"
            "border: 1px solid #e8e8ed; border-radius: 8px; padding: 12px;"
        )
        lay.addWidget(desc_lbl, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        if not is_required:
            self.btn_later = QPushButton("Update Later")
            self.btn_later.setMinimumHeight(36)
            self.btn_later.setStyleSheet("""
                QPushButton {
                    background: #ffffff; color: #3a3a4a; border: 1px solid #d2d2d7;
                    border-radius: 8px; font-size: 13px; padding: 8px 20px;
                }
                QPushButton:hover { background: #e8e8ed; }
            """)
            self.btn_later.clicked.connect(self.reject)
            btn_row.addWidget(self.btn_later)

        btn_row.addStretch()

        self.btn_update = QPushButton("Update Now")
        self.btn_update.setMinimumHeight(36)
        self.btn_update.setStyleSheet("""
            QPushButton {
                background: #0066cc; color: #ffffff; border: none;
                border-radius: 8px; font-size: 13px; font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton:hover { background: #0077ee; }
        """)
        self.btn_update.clicked.connect(self._open_update)
        btn_row.addWidget(self.btn_update)

        lay.addLayout(btn_row)

        self._is_required = is_required

    def _open_update(self):
        webbrowser.open(self._url)
        if self._is_required:
            import sys
            sys.exit(0)
        self.accept()

    def closeEvent(self, event):
        if self._is_required:
            event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._is_required:
            return
        super().keyPressEvent(event)


# ─── Discord Community ───────────────────────────────────────────────────────

class DiscordDialog(QDialog):
    """Periodic prompt to join the Discord community."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Our Community")
        self.setFixedSize(420, 240)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint
        )

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 20)
        lay.setSpacing(16)

        icon_lbl = QLabel("Join Our Community!")
        icon_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1d1d1f;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon_lbl)

        desc = QLabel(
            "Connect with other users, share your creations, "
            "get help, and stay updated on new features.\n\n"
            "Join us on Discord!"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #3a3a4a;")
        desc.setAlignment(Qt.AlignCenter)
        lay.addWidget(desc)

        lay.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_later = QPushButton("Maybe Later")
        btn_later.setMinimumHeight(36)
        btn_later.setStyleSheet("""
            QPushButton {
                background: #ffffff; color: #3a3a4a; border: 1px solid #d2d2d7;
                border-radius: 8px; font-size: 13px; padding: 8px 20px;
            }
            QPushButton:hover { background: #e8e8ed; }
        """)
        btn_later.clicked.connect(self.reject)
        btn_row.addWidget(btn_later)

        btn_row.addStretch()

        btn_join = QPushButton("Join Discord")
        btn_join.setMinimumHeight(36)
        btn_join.setStyleSheet("""
            QPushButton {
                background: #5865F2; color: #ffffff; border: none;
                border-radius: 8px; font-size: 13px; font-weight: bold;
                padding: 8px 24px;
            }
            QPushButton:hover { background: #4752c4; }
        """)
        btn_join.clicked.connect(self._join)
        btn_row.addWidget(btn_join)

        lay.addLayout(btn_row)

    def _join(self):
        webbrowser.open(DISCORD_URL)
        self.accept()
