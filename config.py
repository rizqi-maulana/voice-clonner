import sys
import os
import json
from pathlib import Path

from version import __version__

__all__ = [
    "IS_FROZEN", "APP_DIR", "INTERNAL_DIR", "APP_DATA_DIR",
    "XTTS_MODEL_DIR", "HF_CACHE_DIR", "CONFIG_FILE",
    "Config", "get_chatterbox_cmd",
]

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    APP_DIR = Path(sys.executable).parent
    INTERNAL_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).resolve().parent
    INTERNAL_DIR = APP_DIR

if sys.platform == "win32":
    _base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
elif sys.platform == "darwin":
    _base = Path.home() / "Library" / "Application Support"
else:
    _base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

APP_DATA_DIR = _base / "VoiceClonner"
XTTS_MODEL_DIR = APP_DATA_DIR / "models" / "xtts-v2"
HF_CACHE_DIR = APP_DATA_DIR / "models" / "hf_cache"
CONFIG_FILE = APP_DATA_DIR / "config.json"


class Config:
    def __init__(self):
        self.app_version = __version__
        self.first_run_complete = False
        self.open_count = 0
        self.last_skipped_version = None
        self.custom_model_dir = None

    @classmethod
    def load(cls):
        c = cls()
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                stored_version = data.get("app_version")
                if stored_version == __version__:
                    c.first_run_complete = data.get("first_run_complete", False)
                    c.open_count = data.get("open_count", 0)
                    c.last_skipped_version = data.get("last_skipped_version")
                c.custom_model_dir = data.get("custom_model_dir")
            except (json.JSONDecodeError, OSError):
                pass
        return c

    def save(self):
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        data = {
            "app_version": self.app_version,
            "first_run_complete": self.first_run_complete,
            "open_count": self.open_count,
            "last_skipped_version": self.last_skipped_version,
            "custom_model_dir": self.custom_model_dir,
        }
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(CONFIG_FILE)

    def get_model_dir(self):
        if self.custom_model_dir:
            return Path(self.custom_model_dir)
        return XTTS_MODEL_DIR

    def increment_open_count(self):
        self.open_count += 1


def get_chatterbox_cmd():
    if IS_FROZEN:
        ext = ".exe" if sys.platform == "win32" else ""
        exe = INTERNAL_DIR / f"chatterbox_server{ext}"
        return str(exe), []
    chatterbox_dir = APP_DIR / "chatterbox"
    return "uv", ["run", "python", "-u", "generate.py"], str(chatterbox_dir)
