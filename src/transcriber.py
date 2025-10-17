"""
Transcriber - Whisper를 사용한 음성-텍스트 변환
OpenAI Whisper Large 모델을 활용하여 일본어 음성을 텍스트로 변환
"""

import torch
from pathlib import Path
from typing import List, Dict, Optional
import warnings

# Whisper 경고 메시지 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class Transcriber:
    """Whisper를 사용한 음성-텍스트 변환"""

    def __init__(
        self,
        model_name: str = "large-v3",
        device: Optional[str] = None,
        language: str = "ja"
    ):
        """
        Args:
            model_name: Whisper 모델 이름 (tiny, base, small, medium, large, large-v2, large-v3)
            device: 사용할 디바이스 ('cuda', 'cpu', None=자동감지)
            language: 음성 언어 코드 (ja: 일본어, en: 영어, ko: 한국어)
        """
        self.model_name = model_name
        self.language = language

        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"🔧 Transcriber 초기화:")
        print(f"   - 모델: {model_name}")
        print(f"   - 디바이스: {self.device}")
        print(f"   - 언어: {language}")

        # Whisper 모델 로드
        self.model = None
        self._load_model()

    def _load_model(self):
        """Whisper 모델 로드"""
        try:
            import whisper

            print(f"📥 Whisper 모델 로딩 중... (최초 실행시 다운로드됨)")
            self.model = whisper.load_model(
                self.model_name,
                device=self.device
            )
            print(f"✅ 모델 로드 완료")

            # GPU 메모리 정보 출력
            if self.device == "cuda":
                print(f"🎮 GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

        except ImportError:
            raise ImportError(
                "openai-whisper가 설치되지 않았습니다.\n"
                "설치: pip install openai-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")

    def transcribe(
        self,
        audio_path: str,
        verbose: bool = True,
        temperature: float = 0.0,
        beam_size: int = 5,
        best_of: int = 5
    ) -> List[Dict]:
        """
        음성 파일을 텍스트로 변환

        Args:
            audio_path: 입력 오디오 파일 경로
            verbose: 진행 상황 출력 여부
            temperature: 샘플링 temperature (0.0 = greedy, 높을수록 다양)
            beam_size: beam search 크기 (높을수록 정확하지만 느림)
            best_of: 여러 후보 중 선택 (높을수록 정확하지만 느림)

        Returns:
            타임스탬프 포함 텍스트 세그먼트 리스트
            [
                {
                    "start": 0.0,    # 시작 시간(초)
                    "end": 2.5,      # 종료 시간(초)
                    "text": "こんにちは"  # 텍스트
                },
                ...
            ]

        Raises:
            FileNotFoundError: 오디오 파일이 존재하지 않을 때
            RuntimeError: 변환 실패 시
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

        if verbose:
            print(f"\n🎤 음성 변환 시작: {audio_path.name}")
            print(f"   - 언어: {self.language}")
            print(f"   - Beam size: {beam_size}")
            print(f"   - Temperature: {temperature}")

        try:
            # Whisper 실행
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                verbose=verbose,
                temperature=temperature,
                beam_size=beam_size,
                best_of=best_of,
                fp16=(self.device == "cuda")  # GPU면 FP16 사용
            )

            # 결과 포맷 변환
            segments = []
            for segment in result["segments"]:
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })

            if verbose:
                print(f"\n✅ 변환 완료: {len(segments)}개 세그먼트")
                print(f"   - 전체 텍스트 길이: {len(result['text'])} 문자")

                # GPU 메모리 정보
                if self.device == "cuda":
                    print(f"   - GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

            return segments

        except Exception as e:
            raise RuntimeError(f"음성 변환 실패: {e}")

    def transcribe_with_full_text(
        self,
        audio_path: str,
        verbose: bool = True
    ) -> Dict:
        """
        음성 변환 + 전체 텍스트 반환

        Args:
            audio_path: 입력 오디오 파일 경로
            verbose: 진행 상황 출력 여부

        Returns:
            {
                "segments": [...],  # 세그먼트 리스트
                "text": "...",      # 전체 텍스트
                "language": "ja"    # 감지된 언어
            }
        """
        segments = self.transcribe(audio_path, verbose=verbose)

        # 전체 텍스트 결합
        full_text = " ".join([seg["text"] for seg in segments])

        return {
            "segments": segments,
            "text": full_text,
            "language": self.language
        }

    def get_model_info(self) -> Dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "language": self.language,
            "cuda_available": torch.cuda.is_available(),
            "gpu_memory_gb": torch.cuda.memory_allocated() / 1024**3 if self.device == "cuda" else 0
        }

    def clear_cache(self):
        """캐시와 GPU 메모리 정리"""
        import gc
        
        # 모델과 토크나이저 삭제
        if hasattr(self, 'model'):
            del self.model
        if hasattr(self, 'tokenizer'):
            del self.tokenizer
        
        # Python 가비지 컬렉션 실행
        gc.collect()
        
        # PyTorch CUDA 캐시 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()  # GPU 작업 완료 대기
        
        print("✅ 캐시 및 GPU 메모리 정리 완료")


# 편의 함수
def transcribe_audio(
    audio_path: str,
    model_name: str = "large-v3",
    language: str = "ja",
    verbose: bool = True
) -> List[Dict]:
    """
    간단한 음성 변환 함수

    Args:
        audio_path: 오디오 파일 경로
        model_name: Whisper 모델 이름
        language: 언어 코드
        verbose: 진행 상황 출력

    Returns:
        타임스탬프 포함 텍스트 세그먼트 리스트
    """
    transcriber = Transcriber(model_name=model_name, language=language)
    return transcriber.transcribe(audio_path, verbose=verbose)
