# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Chatterbox Indonesian TTS server (Python 3.11)."""

import sys
import os

block_cipher = None

a = Analysis(
    ['../chatterbox/generate.py'],
    pathex=[os.path.abspath(os.path.join('..', 'chatterbox'))],
    binaries=[],
    datas=[],
    hiddenimports=[
        'chatterbox',
        'chatterbox.tts',
        'safetensors',
        'safetensors.torch',
        'torch',
        'torchaudio',
        'huggingface_hub',
        'soundfile',
        'requests',
        'perth',
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
        'matplotlib',
        'PyQt5',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='chatterbox_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
)
