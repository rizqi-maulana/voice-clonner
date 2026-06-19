# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the main Voice Clonner GUI (Python 3.9)."""

import sys
import os

block_cipher = None

a = Analysis(
    ['../app.py'],
    pathex=[os.path.abspath('..')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'TTS',
        'TTS.tts',
        'TTS.tts.configs',
        'TTS.tts.configs.xtts_config',
        'TTS.tts.models',
        'TTS.tts.models.xtts',
        'TTS.tts.layers',
        'TTS.tts.utils',
        'TTS.utils',
        'TTS.vocoder',
        'torch',
        'torchaudio',
        'sounddevice',
        'soundfile',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
        'numpy',
        'scipy',
        'librosa',
        'transformers',
        'spacy',
        'cutlet',
        'fugashi',
        'unidic_lite',
        'edge_tts',
        'av',
        'blis',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'pytest',
        'IPython',
        'notebook',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add chatterbox_server if it exists (built separately)
chatterbox_dir = os.path.join(os.path.abspath('..'), 'chatterbox_server_dist')
if os.path.isdir(chatterbox_dir):
    for f in os.listdir(chatterbox_dir):
        src = os.path.join(chatterbox_dir, f)
        if os.path.isfile(src):
            a.datas.append((f, src, 'DATA'))

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='voice-clonner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=os.path.join('..', 'assets', 'icon.ico') if os.path.exists(os.path.join('..', 'assets', 'icon.ico')) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='voice-clonner',
)
