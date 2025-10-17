# AutoKR - 일본어 동영상 자막 자동 생성 시스템

일본어 동영상에서 음성을 추출하여 한국어 자막을 자동으로 생성하는 완전 자동화 시스템

## 주요 기능

✅ **완전 구현된 4단계 파이프라인**
1. **오디오 추출**: FFmpeg를 사용한 고품질 음성 추출
2. **음성-텍스트 변환**: OpenAI Whisper Large-v3 모델로 일본어 음성 인식
3. **번역**: Facebook NLLB-200 모델로 일본어 → 한국어 번역
4. **자막 생성**: SRT, SMI 포맷 자막 파일 생성

## 워크플로우

```
[동영상 파일 (.mp4, .avi, etc)]
         ↓
[Step 1: 오디오 추출]
  - FFmpeg로 WAV 추출 (16kHz mono)
  - GPU: 불필요, CPU 처리
         ↓
[Step 2: 음성 → 텍스트 (Whisper STT)]
  - OpenAI Whisper large-v3 모델
  - 타임스탬프 포함 일본어 텍스트 생성
  - GPU: CUDA 가속 (권장)
  - VRAM: ~10GB (large-v3 기준)
         ↓
[Step 3: 일본어 → 한국어 번역]
  - Facebook NLLB-200-1.3B 모델
  - 배치 처리 (기본 8개씩)
  - 타임스탬프 보존
  - GPU: CUDA 가속 (권장)
  - VRAM: ~5GB
         ↓
[Step 4: 자막 파일 생성]
  - SRT 또는 SMI 포맷 선택
  - 타임스탬프 정확히 매핑
  - UTF-8 인코딩
         ↓
[자막 파일 (.srt/.smi)]
```

## 시스템 요구사항

### 하드웨어
- **최소**: CPU only (매우 느림, 비권장)
- **권장**: NVIDIA GPU 12GB+ (RTX 3060 이상)
  - Whisper large-v3: ~10GB VRAM
  - NLLB-200-1.3B: ~5GB VRAM
  - 동시 실행 시 최대 ~15GB VRAM 사용

### 소프트웨어
- **Python**: 3.9 이상
- **FFmpeg**: 오디오 추출용
- **CUDA**: 11.8+ (GPU 사용 시)
- **cuDNN**: CUDA에 맞는 버전

## 설치

### 1. 저장소 클론
```bash
git clone <repository-url>
cd autokr
```

### 2. FFmpeg 설치

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
[FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드 후 PATH 등록

### 3. Python 의존성 설치

```bash
pip install -r requirements.txt
```

주요 라이브러리:
- `openai-whisper`: Whisper STT 모델
- `transformers`: NLLB 번역 모델
- `torch`: PyTorch (GPU 가속)
- `sentencepiece`: NLLB 토크나이저

### 4. GPU 설정 확인 (선택사항, 강력 권장)

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

## 사용 방법

### 기본 사용법

```bash
python autokr.py -i <입력_동영상> -o <출력_자막>
```

**예시:**
```bash
python autokr.py -i video.mp4 -o subtitle.srt
```

### 명령어 옵션

```
필수 인자:
  -i, --input INPUT       입력 동영상 파일 경로
  -o, --output OUTPUT     출력 자막 파일 경로

선택 인자:
  -f, --format {srt,smi}  자막 포맷 (기본값: srt)
  -m, --model MODEL       Whisper 모델 크기 (기본값: large-v3)
                          선택: tiny, base, small, medium, large, large-v2, large-v3
  --language LANG         음성 언어 코드 (기본값: ja)
  --keep-audio            임시 오디오 파일 유지
  -h, --help              도움말 표시
```

### 사용 예시

**1. 기본 사용 (SRT 자막, large-v3 모델)**
```bash
python autokr.py -i anime.mp4 -o anime.srt
```

**2. SMI 포맷 자막 생성**
```bash
python autokr.py -i video.mp4 -o video.smi -f smi
```

**3. 빠른 테스트 (small 모델, 낮은 VRAM)**
```bash
python autokr.py -i video.mp4 -o subtitle.srt -m small
```

**4. 중간 품질 (medium 모델)**
```bash
python autokr.py -i video.mp4 -o subtitle.srt -m medium
```

**5. 오디오 파일 보관**
```bash
python autokr.py -i video.mp4 -o subtitle.srt --keep-audio
```

**6. 한국어 음성 처리 (언어 변경)**
```bash
python autokr.py -i korean_video.mp4 -o subtitle.srt --language ko
```

## 실행 화면

```
============================================================
AutoKR - 일본어 동영상 자막 자동 생성
============================================================
입력 동영상: video.mp4
출력 자막: subtitle.srt
자막 포맷: srt
Whisper 모델: large-v3
언어: ja
============================================================

📹 Step 1/4: 오디오 추출
------------------------------------------------------------
✅ 오디오 추출 완료: temp/audio.wav

🎤 Step 2/4: 음성 → 텍스트 변환 (Whisper)
------------------------------------------------------------
🔧 Transcriber 초기화:
   - 모델: large-v3
   - 디바이스: cuda
   - 언어: ja
📥 Whisper 모델 로딩 중...
✅ 모델 로드 완료
🎮 GPU 메모리 사용량: 9.87 GB
✅ 음성 변환 완료: 42개 세그먼트

🌐 Step 3/4: 번역 (일본어 → 한국어)
------------------------------------------------------------
🔧 Translator 초기화:
   - 모델: facebook/nllb-200-1.3B
   - 디바이스: cuda
   - 번역: jpn_Jpan → kor_Hang
📥 NLLB 모델 로딩 중...
✅ 모델 로드 완료
🌏 번역 시작: 42개 세그먼트
   - 배치 크기: 8
✅ 번역 완료: 42개 세그먼트

📝 Step 4/4: 자막 파일 생성
------------------------------------------------------------
📝 SRT 자막 생성 중...
   - 세그먼트 수: 42
✅ 자막 파일 생성 완료: subtitle.srt

🧹 정리 중...
✅ 임시 오디오 파일 삭제됨
✅ 캐시 및 GPU 메모리 정리 완료

============================================================
✅ 모든 작업 완료!
============================================================
📄 생성된 자막 파일: subtitle.srt
📊 통계:
   - 총 세그먼트: 42개
   - 자막 포맷: SRT
   - 처리 완료
============================================================
```

## 성능 벤치마크

### 모델별 특성 비교

| 모델 | VRAM | 상대 속도 | 정확도 | 권장 용도 |
|------|------|----------|--------|----------|
| tiny | ~1GB | 32x | ⭐⭐ | 빠른 테스트, 프로토타입 |
| base | ~1GB | 16x | ⭐⭐⭐ | 개발 테스트 |
| small | ~2GB | 6x | ⭐⭐⭐⭐ | 일반 작업, 균형 |
| medium | ~5GB | 2x | ⭐⭐⭐⭐⭐ | 높은 품질 |
| large | ~10GB | 1x | ⭐⭐⭐⭐⭐ | 최고 품질 |
| large-v3 | ~10GB | 1x | ⭐⭐⭐⭐⭐⭐ | 최신, 최고 품질 (권장) |

### 처리 시간 예상 (RTX 3060 12GB)

**10분 동영상 기준:**
- 오디오 추출: ~10초 (CPU)
- STT (small): ~30초 (GPU)
- STT (large-v3): ~1-2분 (GPU)
- 번역: ~10-15초 (GPU)
- 자막 생성: ~1초 (CPU)

**총 처리 시간:**
- small 모델: ~1분
- large-v3 모델: ~2-3분

## 프로젝트 구조

```
autokr/
├── autokr.py               # 실행 진입점
├── src/
│   ├── cli.py              # CLI 인터페이스
│   ├── audio_extractor.py  # 오디오 추출 (FFmpeg)
│   ├── transcriber.py      # 음성-텍스트 (Whisper)
│   ├── translator.py       # 번역 (NLLB)
│   └── subtitle_gen.py     # 자막 생성 (SRT/SMI)
├── models/                 # 다운로드된 AI 모델 (자동 생성)
├── temp/                   # 임시 오디오 파일
├── docs/
│   └── architecture.md     # 아키텍처 문서
├── test_*.py               # 단위 테스트 스크립트
├── requirements.txt        # Python 의존성
└── README.md
```

## 문제 해결

### 1. FFmpeg 관련 오류

**증상**: `FFmpeg를 찾을 수 없습니다`

**해결:**
```bash
# FFmpeg 설치 확인
ffmpeg -version

# PATH 확인
which ffmpeg  # Linux/macOS
where ffmpeg  # Windows
```

### 2. GPU 메모리 부족 (CUDA Out of Memory)

**증상**: `RuntimeError: CUDA out of memory`

**해결 방법:**
1. 더 작은 Whisper 모델 사용
   ```bash
   python autokr.py -i video.mp4 -o subtitle.srt -m small
   ```

2. 다른 GPU 프로그램 종료
   ```bash
   nvidia-smi  # GPU 사용량 확인
   ```

3. CPU 모드로 실행 (자동 전환, 매우 느림)
   - CUDA 미설치 시 자동으로 CPU 모드 사용

### 3. 모델 다운로드 오류

**증상**: 첫 실행 시 모델 다운로드 실패

**해결:**
- 인터넷 연결 확인
- Whisper 모델: `~/.cache/whisper/`
- NLLB 모델: `~/.cache/huggingface/`
- 방화벽/프록시 설정 확인

### 4. 번역 품질이 낮음

**원인**: STT 단계에서 정확도가 낮으면 번역도 부정확

**해결:**
- 더 큰 Whisper 모델 사용 (`-m large-v3`)
- 음성이 명확한 고품질 동영상 사용

### 5. 자막 타이밍이 안 맞음

**원인**: Whisper의 타임스탬프 예측 오차

**해결:**
- 현재는 Whisper 자동 타임스탬프 사용
- 수동 조정 필요 시 SRT 파일 직접 편집

## 개발 및 테스트

### 컴포넌트별 단위 테스트

**오디오 추출 테스트:**
```bash
python test_audio_extractor.py video.mp4
```

**음성 변환 테스트:**
```bash
python test_transcriber.py audio.wav
python test_transcriber.py --full video.mp4  # 전체 파이프라인
```

**번역 테스트:**
```bash
python test_translator.py
```

**자막 생성 테스트:**
```bash
python test_subtitle_gen.py
```

## 향후 개선 계획

- [ ] 실시간 자막 생성 (스트리밍)
- [ ] 다국어 지원 확장 (중국어, 영어 등)
- [ ] 자막 타이밍 자동 최적화
- [ ] GUI 인터페이스 추가
- [ ] 배치 처리 (여러 동영상 동시 처리)
- [ ] 자막 품질 자동 검증

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 참고 자료

- [OpenAI Whisper](https://github.com/openai/whisper)
- [NLLB-200 Model](https://huggingface.co/facebook/nllb-200-1.3B)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
