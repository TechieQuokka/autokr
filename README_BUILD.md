# AutoKR 실행 파일 빌드 가이드

## 빌드 준비

### 1. 필수 요구사항
```bash
# PyInstaller 설치
pip install pyinstaller

# 프로젝트 의존성 설치
pip install -r requirements.txt
```

### 2. FFmpeg 설치 (필수)
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# https://ffmpeg.org/download.html 에서 다운로드
```

## 빌드 방법

### 방법 1: 빌드 스크립트 사용 (추천)
```bash
./build.sh
```

### 방법 2: 수동 빌드
```bash
# 이전 빌드 결과 삭제
rm -rf build dist

# PyInstaller 실행
pyinstaller autokr.spec --clean
```

## 빌드 결과

빌드 성공시 다음 구조로 생성됩니다:
```
dist/
└── autokr/
    ├── autokr          # 실행 파일
    ├── src/            # 소스 파일들
    └── _internal/      # 필요한 라이브러리들
```

## 실행 방법

```bash
# 기본 사용법
./dist/autokr/autokr -i input.mp4 -o output.srt

# 전체 옵션
./dist/autokr/autokr \
  -i input.mp4 \
  -o output.srt \
  -f srt \
  -w large-v3 \
  -t facebook/nllb-200-3.3B \
  --language ja
```

## 배포

배포시 `dist/autokr/` 전체 디렉토리를 압축하여 배포하세요:
```bash
cd dist
tar -czf autokr-linux-x64.tar.gz autokr/
```

## 주의사항

### 1. 모델 다운로드
- 처음 실행시 Whisper와 NLLB 모델이 자동으로 다운로드됩니다
- 인터넷 연결이 필요합니다
- 모델 용량: 약 3-10GB

### 2. GPU 지원
- CUDA가 설치된 경우 자동으로 GPU 사용
- CPU만 사용시에도 정상 작동하지만 속도가 느립니다

### 3. 메모리 요구사항
- 최소 8GB RAM 권장
- GPU 사용시 최소 6GB VRAM 권장

### 4. FFmpeg 의존성
- 실행 파일은 FFmpeg를 포함하지 않습니다
- 대상 시스템에 FFmpeg가 설치되어 있어야 합니다

## 트러블슈팅

### "ModuleNotFoundError" 발생시
`autokr.spec` 파일의 `hiddenimports` 항목에 누락된 모듈을 추가하세요.

### "FFmpeg not found" 발생시
시스템에 FFmpeg를 설치하세요.

### GPU 메모리 부족 시
더 작은 Whisper 모델을 사용하세요:
```bash
./dist/autokr/autokr -i input.mp4 -w medium  # large-v3 대신 medium 사용
```

## 크로스 플랫폼 빌드

각 플랫폼에서 빌드해야 합니다:
- Linux: Linux에서 빌드
- macOS: macOS에서 빌드
- Windows: Windows에서 빌드

## 원스텝 빌드 (Single File)

단일 실행 파일로 빌드하려면 `autokr.spec`을 수정:
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # 이 줄 추가
    a.zipfiles,  # 이 줄 추가
    a.datas,     # 이 줄 추가
    [],
    name='autokr',
    debug=False,
    strip=False,
    upx=True,
    console=True,
    onefile=True,  # 이 줄 추가
)
```

**주의**: 단일 파일 모드는 시작 시간이 느리고 용량이 매우 큽니다 (1GB+).
