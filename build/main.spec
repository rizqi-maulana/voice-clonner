# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the main Voice Clonner GUI (Python 3.9)."""

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_all, collect_data_files, collect_dynamic_libs

block_cipher = None

hiddenimports = [
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
    'sounddevice',
    'soundfile',
    'matplotlib',
    'matplotlib.backends.backend_qt5agg',
    'edge_tts',
    'av',
    'blis',
]

hiddenimports += collect_submodules('numpy')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('librosa')
hiddenimports += collect_submodules('transformers')
hiddenimports += collect_submodules('spacy')
hiddenimports += collect_submodules('cutlet')
hiddenimports += collect_submodules('fugashi')
hiddenimports += collect_submodules('unidic_lite')
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('torchaudio')
hiddenimports += collect_submodules('TTS')

extra_datas = []
extra_binaries = []

# Collect numpy entirely — datas preserve .libs directory structure,
# binaries ensure DLLs are found, hiddenimports cover all submodules
np_datas, np_binaries, np_hidden = collect_all('numpy')
extra_datas += np_datas
extra_binaries += np_binaries
hiddenimports += np_hidden

# Explicitly bundle numpy DLLs — handles both old layout (numpy/.libs/)
# and new layout (numpy.libs/ at site-packages level)
import numpy as _np
_np_dir = os.path.dirname(_np.__file__)
_sp_dir = os.path.dirname(_np_dir)

for _libs_rel, _dest in [
    (os.path.join(_np_dir, '.libs'), os.path.join('numpy', '.libs')),
    (os.path.join(_sp_dir, 'numpy.libs'), 'numpy.libs'),
]:
    if os.path.isdir(_libs_rel):
        for _f in os.listdir(_libs_rel):
            _src = os.path.join(_libs_rel, _f)
            if os.path.isfile(_src):
                extra_datas.append((_src, _dest))
                extra_binaries.append((_src, '.'))

extra_datas += collect_data_files('unidic_lite')
extra_datas += collect_data_files('spacy')
extra_datas += collect_data_files('cutlet')

a = Analysis(
    ['../app.py'],
    pathex=[os.path.abspath('..')],
    binaries=extra_binaries,
    datas=extra_datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(SPECPATH, 'rthook_numpy.py')],
    excludes=[
        'tkinter',
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
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name='voice-clonner',
)
