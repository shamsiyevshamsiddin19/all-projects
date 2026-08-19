# -*- mode: python ; coding: utf-8 -*-
#
# Cloud-first build: end users provide their own API keys inside the app, so
# the packaged processor targets the Groq/OpenAI/Gemini cloud services. The
# heavy local-ML stack (torch / faster-whisper / onnxruntime) is excluded to
# keep the installer small. Local transcription still works from the Python
# source version for power users.

excludes = [
    'torch', 'torchaudio', 'torchvision',
    'faster_whisper', 'ctranslate2', 'onnxruntime',
    'whisper', 'transformers', 'tokenizers',
    'numpy.random._examples',
    'tkinter', 'matplotlib', 'scipy', 'pandas',
    'PyQt5', 'PySide2', 'PIL',
]

hiddenimports = [
    'groq', 'openai', 'google.genai', 'anthropic',
    'docx', 'dotenv',
]

a = Analysis(
    ['desktop_processor.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='desktop_processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
