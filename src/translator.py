"""
Translator - NLLB-200을 사용한 일본어-한국어 번역
Facebook의 NLLB-200 모델을 활용하여 타임스탬프를 보존하며 번역
"""

import torch
from pathlib import Path
from typing import List, Dict, Optional
import warnings

# Transformers 경고 메시지 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)


class Translator:
    """NLLB-200을 사용한 일본어-한국어 번역"""

    def __init__(
        self,
        model_name: str = "facebook/nllb-200-1.3B",
        device: Optional[str] = None,
        source_lang: str = "jpn_Jpan",
        target_lang: str = "kor_Hang"
    ):
        """
        Args:
            model_name: NLLB 모델 이름
                - facebook/nllb-200-distilled-600M (작고 빠름)
                - facebook/nllb-200-1.3B (중간, 권장)
                - facebook/nllb-200-3.3B (크고 정확)
            device: 사용할 디바이스 ('cuda', 'cpu', None=자동감지)
            source_lang: 원본 언어 코드 (jpn_Jpan: 일본어)
            target_lang: 목표 언어 코드 (kor_Hang: 한국어)
        """
        self.model_name = model_name
        self.source_lang = source_lang
        self.target_lang = target_lang

        # 디바이스 설정
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"🔧 Translator 초기화:")
        print(f"   - 모델: {model_name}")
        print(f"   - 디바이스: {self.device}")
        print(f"   - 번역: {source_lang} → {target_lang}")

        # 모델 및 토크나이저 로드
        self.model = None
        self.tokenizer = None
        self._load_model()

    def _load_model(self):
        """NLLB 모델 및 토크나이저 로드"""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

            print(f"📥 NLLB 모델 로딩 중... (최초 실행시 다운로드됨)")

            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                src_lang=self.source_lang
            )

            # 모델 로드
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name
            ).to(self.device)

            # 언어 코드를 토큰 ID로 변환 (NLLB 토크나이저 호환)
            self.target_lang_id = self.tokenizer.convert_tokens_to_ids(self.target_lang)

            print(f"✅ 모델 로드 완료")

            # GPU 메모리 정보 출력
            if self.device == "cuda":
                print(f"🎮 GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

        except ImportError:
            raise ImportError(
                "transformers가 설치되지 않았습니다.\n"
                "설치: pip install transformers sentencepiece"
            )
        except Exception as e:
            raise RuntimeError(f"모델 로드 실패: {e}")

    def translate(
        self,
        text: str,
        max_length: int = 512,
        num_beams: int = 5,
        verbose: bool = False
    ) -> str:
        """
        단일 텍스트 번역

        Args:
            text: 번역할 텍스트
            max_length: 최대 출력 길이
            num_beams: beam search 크기 (높을수록 정확하지만 느림)
            verbose: 진행 상황 출력 여부

        Returns:
            번역된 텍스트

        Raises:
            RuntimeError: 번역 실패 시
        """
        if not text or not text.strip():
            return ""

        try:
            # 토크나이즈
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=max_length
            ).to(self.device)

            # 번역 생성
            translated_tokens = self.model.generate(
                **inputs,
                forced_bos_token_id=self.target_lang_id,
                max_length=max_length,
                num_beams=num_beams,
                early_stopping=True
            )

            # 디코딩
            translated_text = self.tokenizer.batch_decode(
                translated_tokens,
                skip_special_tokens=True
            )[0]

            if verbose:
                print(f"원문: {text}")
                print(f"번역: {translated_text}")

            return translated_text

        except Exception as e:
            raise RuntimeError(f"번역 실패: {e}")

    def translate_segments(
        self,
        segments: List[Dict],
        verbose: bool = True,
        batch_size: int = 8
    ) -> List[Dict]:
        """
        타임스탬프 포함 세그먼트 리스트 번역

        Args:
            segments: Transcriber에서 생성된 세그먼트 리스트
                [
                    {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "こんにちは"
                    },
                    ...
                ]
            verbose: 진행 상황 출력 여부
            batch_size: 배치 처리 크기 (메모리에 따라 조정)

        Returns:
            번역된 세그먼트 리스트
            [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "안녕하세요",
                    "original": "こんにちは"
                },
                ...
            ]

        Raises:
            RuntimeError: 번역 실패 시
        """
        if not segments:
            return []

        if verbose:
            print(f"\n🌏 번역 시작: {len(segments)}개 세그먼트")
            print(f"   - 배치 크기: {batch_size}")

        try:
            translated_segments = []
            total = len(segments)

            # 배치 처리
            for i in range(0, total, batch_size):
                batch = segments[i:i + batch_size]

                if verbose:
                    print(f"   - 진행: {i + 1}-{min(i + batch_size, total)}/{total}")

                # 배치 번역
                texts = [seg["text"] for seg in batch]

                # 토크나이즈
                inputs = self.tokenizer(
                    texts,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512
                ).to(self.device)

                # 번역 생성
                translated_tokens = self.model.generate(
                    **inputs,
                    forced_bos_token_id=self.target_lang_id,
                    max_length=512,
                    num_beams=5,
                    early_stopping=True
                )

                # 디코딩
                translated_texts = self.tokenizer.batch_decode(
                    translated_tokens,
                    skip_special_tokens=True
                )

                # 결과 조합
                for seg, translated in zip(batch, translated_texts):
                    translated_segments.append({
                        "start": seg["start"],
                        "end": seg["end"],
                        "text": translated.strip(),
                        "original": seg["text"]
                    })

            if verbose:
                print(f"\n✅ 번역 완료: {len(translated_segments)}개 세그먼트")

                # GPU 메모리 정보
                if self.device == "cuda":
                    print(f"   - GPU 메모리 사용량: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

                # 샘플 출력
                if translated_segments:
                    print(f"\n📝 샘플:")
                    for seg in translated_segments[:3]:
                        print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s]")
                        print(f"   원문: {seg['original']}")
                        print(f"   번역: {seg['text']}\n")

            return translated_segments

        except Exception as e:
            raise RuntimeError(f"세그먼트 번역 실패: {e}")

    def translate_with_fallback(
        self,
        segments: List[Dict],
        verbose: bool = True,
        batch_size: int = 8
    ) -> List[Dict]:
        """
        번역 실패 시 원문 유지하는 안전한 번역

        Args:
            segments: 원본 세그먼트 리스트
            verbose: 진행 상황 출력 여부
            batch_size: 배치 처리 크기

        Returns:
            번역된 세그먼트 리스트 (실패 시 원문 유지)
        """
        try:
            return self.translate_segments(segments, verbose=verbose, batch_size=batch_size)
        except Exception as e:
            if verbose:
                print(f"⚠️ 번역 실패, 원문 유지: {e}")

            # 원문을 그대로 반환
            return [{
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "original": seg["text"]
            } for seg in segments]

    def get_model_info(self) -> Dict:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
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
def translate_japanese_to_korean(
    segments: List[Dict],
    model_name: str = "facebook/nllb-200-1.3B",
    verbose: bool = True
) -> List[Dict]:
    """
    간단한 일본어-한국어 번역 함수

    Args:
        segments: 원본 세그먼트 리스트
        model_name: NLLB 모델 이름
        verbose: 진행 상황 출력

    Returns:
        번역된 세그먼트 리스트
    """
    translator = Translator(model_name=model_name)
    return translator.translate_segments(segments, verbose=verbose)
