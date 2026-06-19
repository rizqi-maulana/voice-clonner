STYLE = """
QMainWindow, QDialog { background: #f5f5f7; }
QWidget { background: #f5f5f7; color: #1d1d1f; font-family: "Segoe UI", "Helvetica Neue", Arial; font-size: 13px; }
QScrollArea { border: none; background: #f5f5f7; }

QGroupBox {
    border: 1px solid #d2d2d7;
    border-radius: 10px;
    margin-top: 14px;
    padding: 20px 12px 10px 12px;
    font-weight: bold;
    color: #3a3a4a;
    font-size: 12px;
    background: #ffffff;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 2px 8px; }

QPushButton {
    background: #ffffff;
    color: #1d1d1f;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 26px;
}
QPushButton:hover { background: #e8e8ed; border-color: #b0b0b8; }
QPushButton:pressed { background: #d5d5da; }
QPushButton:disabled { color: #a0a0a8; background: #f0f0f2; border-color: #e0e0e5; }

QPushButton#primary {
    background: #0066cc;
    color: #ffffff;
    border: 1px solid #0055aa;
    font-size: 15px;
    font-weight: bold;
    min-height: 42px;
    border-radius: 8px;
}
QPushButton#primary:hover { background: #0077ee; }
QPushButton#primary:pressed { background: #004499; }
QPushButton#primary:disabled { background: #b0c4de; color: #e8e8ee; border-color: #a0b4ce; }

QPushButton#record {
    background: #fff0f2;
    border-color: #e8a0b0;
    color: #cc2244;
}
QPushButton#record:hover { background: #ffe0e5; border-color: #dd6688; }

QPushButton#recording {
    background: #d93025;
    border-color: #bb1a10;
    color: #ffffff;
    font-weight: bold;
}

QTextEdit {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 8px;
    color: #1d1d1f;
    font-size: 14px;
    selection-background-color: #b3d7ff;
}
QTextEdit:focus { border-color: #0066cc; }

QComboBox {
    background: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 26px;
    color: #1d1d1f;
}
QComboBox:hover { border-color: #0066cc; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #0066cc;
    selection-background-color: #e6f0ff;
    selection-color: #1d1d1f;
    color: #1d1d1f;
}
QComboBox::drop-down { border: none; width: 20px; }

QSlider::groove:horizontal {
    height: 4px;
    background: #d2d2d7;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #0066cc;
    border-radius: 7px;
    width: 14px;
    height: 14px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal { background: #0066cc; border-radius: 2px; }

QProgressBar {
    background: #e8e8ed;
    border: 1px solid #d2d2d7;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk { background: #0066cc; border-radius: 3px; }

QLabel { color: #3a3a4a; }
QLabel#title { color: #1d1d1f; font-size: 20px; font-weight: bold; }
QLabel#subtitle { color: #6e6e73; font-size: 12px; }
QLabel#info_ok { color: #34a853; font-size: 12px; }
QLabel#info_warn { color: #ea8600; font-size: 12px; }
QLabel#info_dim { color: #8e8e93; font-size: 12px; }
QLabel#sample_header { color: #6e6e73; font-size: 11px; }

QStatusBar { background: #ffffff; color: #6e6e73; font-size: 12px; border-top: 1px solid #e8e8ed; }
QSplitter::handle { background: #d2d2d7; }
"""
