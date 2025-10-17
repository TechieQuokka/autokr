# AutoKR - 동영상 자막 자동 생성 시스템

## 시스템 개요
일본어 동영상에서 음성 추출 → 텍스트 변환 → 한국어 번역 → 자막 파일 생성

## 아키텍처

```
[동영상 파일] → [AudioExtractor] → [음성 파일]
                                        ↓
                                   [Whisper STT]
                                        ↓
                                  [일본어 텍스트]
                                        ↓
                                   [Translator]
                                        ↓
                                  [한국어 텍스트]
                                        ↓
                                [SubtitleGenerator]
                                        ↓
                                 [자막 파일 .smi/.srt]
```

## 핵심 컴포넌트

### 1. CLI Interface
- **입력**: 동영상 파일 경로, 자막 저장 경로, 출력 포맷(.smi/.srt)
- **라이브러리**: argparse
- **예시**: `autokr -i video.mp4 -o subtitle.srt`

### 2. AudioExtractor
- **기능**: 동영상에서 오디오 추출
- **라이브러리**: FFmpeg (ffmpeg-python)
- **출력**: WAV/MP3 (16kHz mono 권장)
- **GPU**: 불필요

### 3. Speech-to-Text (Whisper)
- **모델**: OpenAI Whisper (large-v3)
- **GPU 가속**: CUDA (RTX 3060 12GB)
- **라이브러리**: whisper-large - 약 10GB VRAM
- **출력**: 타임스탬프 포함 일본어 텍스트
- **VRAM**: ~4-6GB (large 모델 기준)

### 4. Translator
- **라이브러리**: nllb-200-1.3B - 약 5GB VRAM
- **출력**: 타임스탬프 보존 한국어 텍스트

### 5. SubtitleGenerator
- **기능**: 텍스트 → 자막 포맷 변환
- **지원 포맷**: SRT, SMI
- **라이브러리**: pysrt / 자체 구현

## 디렉토리 구조

```
autokr/
├── src/
│   ├── cli.py              # CLI 진입점
│   ├── audio_extractor.py  # 음성 추출
│   ├── transcriber.py      # STT (Whisper)
│   ├── translator.py       # 번역
│   └── subtitle_gen.py     # 자막 생성
├── models/                 # 다운로드된 모델
├── temp/                   # 임시 파일 (음성)
├── docs/
│   └── architecture.md
├── requirements.txt
└── README.md
```

## 데이터 플로우

1. **CLI 입력**: `autokr -i video.mp4 -o subtitle.srt`
2. **AudioExtractor**: video.mp4 → temp/audio.wav
3. **Transcriber**: audio.wav → [{start: 0.0, end: 2.5, text: "こんにちは"}]
4. **Translator**: 일본어 → 한국어 [{start: 0.0, end: 2.5, text: "안녕하세요"}]
5. **SubtitleGenerator**: JSON → subtitle.srt
6. **Cleanup**: temp/ 정리

## 기술 스택

### 필수
- Python 3.9+
- FFmpeg
- CUDA 11.8+ / cuDNN

### 라이브러리
```
whisper-large    # GPU 가속 Whisper
ffmpeg-python     # 오디오 추출
deep-translator   # 번역 (nllb-200-1.3B)
pysrt            # SRT 생성
```

### 선택적 GPU 활용
- **Whisper**: GPU 필수 (속도 20배↑)
- **번역**: NLLB 사용 시 GPU 권장
- **오디오 추출**: CPU로 충분

## 성능 예상 (RTX 3060 12GB)

- 10분 동영상 기준
  - 오디오 추출: ~10초
  - STT (Whisper large): ~1-2분
  - 번역 (API): ~5-10초
  - 자막 생성: ~1초
- **총 처리 시간**: ~2-3분