# -*- mode: python ; coding: utf-8 -*-
"""
AutoKR PyInstaller Specification File
일본어 동영상 자막 자동 생성 시스템 빌드 설정
"""

block_cipher = None

# 분석 설정
a = Analysis(
    ['autokr.py'],  # 진입점
    pathex=[],
    binaries=[],
    datas=[
        ('src/*.py', 'src'),  # 모든 소스 파일 포함
    ],
    hiddenimports=[
        # PyTorch
        'torch',
        'torch.nn',
        'torch.cuda',
        'torchaudio',
        'torchaudio.backend',
        'torchaudio.backend.soundfile_backend',

        # Whisper
        'whisper',
        'whisper.model',
        'whisper.audio',
        'whisper.decoding',
        'whisper.timing',
        'whisper.tokenizer',

        # Transformers
        'transformers',
        'transformers.models',
        'transformers.models.nllb',
        'transformers.models.auto',
        'transformers.tokenization_utils',
        'transformers.tokenization_utils_base',

        # 추가 의존성
        'sentencepiece',
        'numpy',
        'json',
        'subprocess',
        'pathlib',
        'argparse',

        # FFmpeg
        'ffmpeg',

        # Worker 스크립트 임포트
        'audio_extractor',
        'transcriber',
        'translator',
        'subtitle_gen',
        'cli',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 패키지 제외
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'tkinter',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ 압축 아카이브
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# 실행 파일 생성
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='autokr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # CLI 앱이므로 콘솔 모드
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# 바이너리 및 데이터 수집
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='autokr',
)
