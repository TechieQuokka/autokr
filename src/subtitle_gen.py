"""
SubtitleGenerator - 타임스탬프 포함 텍스트를 자막 파일로 변환
SRT, SMI 포맷 지원
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import timedelta


class SubtitleGenerator:
    """자막 파일 생성기 (SRT, SMI 포맷 지원)"""

    @staticmethod
    def _format_timestamp_srt(seconds: float) -> str:
        """
        초 단위 시간을 SRT 타임스탬프 형식으로 변환

        Args:
            seconds: 초 단위 시간 (예: 65.5)

        Returns:
            SRT 형식 타임스탬프 (예: "00:01:05,500")
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_timestamp_smi(seconds: float) -> int:
        """
        초 단위 시간을 SMI 타임스탬프 형식으로 변환

        Args:
            seconds: 초 단위 시간 (예: 65.5)

        Returns:
            밀리초 단위 정수 (예: 65500)
        """
        return int(seconds * 1000)

    def generate_srt(
        self,
        segments: List[Dict],
        output_path: str,
        verbose: bool = True
    ) -> Path:
        """
        SRT 자막 파일 생성

        Args:
            segments: 타임스탬프 포함 세그먼트 리스트
                [
                    {
                        "start": 0.0,
                        "end": 2.5,
                        "text": "안녕하세요"
                    },
                    ...
                ]
            output_path: 출력 파일 경로 (.srt)
            verbose: 진행 상황 출력 여부

        Returns:
            생성된 파일의 Path 객체

        Raises:
            ValueError: 잘못된 세그먼트 데이터
            IOError: 파일 쓰기 실패
        """
        if not segments:
            raise ValueError("빈 세그먼트 리스트입니다")

        output_path = Path(output_path)

        if verbose:
            print(f"\n📝 SRT 자막 생성 중...")
            print(f"   - 세그먼트 수: {len(segments)}")
            print(f"   - 출력 경로: {output_path}")

        try:
            # SRT 포맷으로 변환
            srt_content = []

            for idx, segment in enumerate(segments, start=1):
                # 필수 필드 검증
                if not all(key in segment for key in ["start", "end", "text"]):
                    raise ValueError(f"세그먼트 {idx}에 필수 필드가 없습니다: {segment}")

                start_time = self._format_timestamp_srt(segment["start"])
                end_time = self._format_timestamp_srt(segment["end"])
                text = segment["text"].strip()

                # SRT 형식: 번호 → 타임스탬프 → 텍스트 → 빈 줄
                srt_content.append(f"{idx}")
                srt_content.append(f"{start_time} --> {end_time}")
                srt_content.append(text)
                srt_content.append("")  # 빈 줄

            # 파일 쓰기
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(srt_content), encoding="utf-8")

            if verbose:
                print(f"✅ SRT 파일 생성 완료")
                print(f"   - 파일 크기: {output_path.stat().st_size:,} bytes")

                # 샘플 출력
                if segments:
                    print(f"\n📋 샘플:")
                    for seg in segments[:2]:
                        print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")

            return output_path

        except Exception as e:
            raise IOError(f"SRT 파일 생성 실패: {e}")

    def generate_smi(
        self,
        segments: List[Dict],
        output_path: str,
        lang_code: str = "KO",
        verbose: bool = True
    ) -> Path:
        """
        SMI (SAMI) 자막 파일 생성

        Args:
            segments: 타임스탬프 포함 세그먼트 리스트
            output_path: 출력 파일 경로 (.smi)
            lang_code: 언어 코드 (KO: 한국어, EN: 영어, JA: 일본어)
            verbose: 진행 상황 출력 여부

        Returns:
            생성된 파일의 Path 객체

        Raises:
            ValueError: 잘못된 세그먼트 데이터
            IOError: 파일 쓰기 실패
        """
        if not segments:
            raise ValueError("빈 세그먼트 리스트입니다")

        output_path = Path(output_path)

        if verbose:
            print(f"\n📝 SMI 자막 생성 중...")
            print(f"   - 세그먼트 수: {len(segments)}")
            print(f"   - 출력 경로: {output_path}")
            print(f"   - 언어 코드: {lang_code}")

        try:
            # SMI 헤더
            smi_content = [
                "<SAMI>",
                "<HEAD>",
                "<TITLE>AutoKR Subtitle</TITLE>",
                "<STYLE TYPE=\"text/css\">",
                "<!--",
                "P { margin-left:8pt; margin-right:8pt; margin-bottom:2pt;",
                "    margin-top:2pt; font-size:20pt; text-align:center;",
                "    font-family:굴림, Arial; font-weight:normal; color:white; }",
                ".KRCC { Name:한국어; lang:ko-KR; SAMIType:CC; }",
                "-->",
                "</STYLE>",
                "</HEAD>",
                "<BODY>",
                ""
            ]

            # 각 세그먼트를 SMI 형식으로 변환
            for segment in segments:
                # 필수 필드 검증
                if not all(key in segment for key in ["start", "end", "text"]):
                    raise ValueError(f"세그먼트에 필수 필드가 없습니다: {segment}")

                start_ms = self._format_timestamp_smi(segment["start"])
                end_ms = self._format_timestamp_smi(segment["end"])
                text = segment["text"].strip()

                # 자막 시작
                smi_content.append(f"<SYNC Start={start_ms}>")
                smi_content.append(f"<P Class=KRCC>")
                smi_content.append(text)
                smi_content.append("</P>")

                # 자막 종료 (빈 줄로 표시)
                smi_content.append(f"<SYNC Start={end_ms}>")
                smi_content.append("<P Class=KRCC>&nbsp;</P>")
                smi_content.append("")

            # SMI 푸터
            smi_content.append("</BODY>")
            smi_content.append("</SAMI>")

            # 파일 쓰기
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("\n".join(smi_content), encoding="utf-8")

            if verbose:
                print(f"✅ SMI 파일 생성 완료")
                print(f"   - 파일 크기: {output_path.stat().st_size:,} bytes")

                # 샘플 출력
                if segments:
                    print(f"\n📋 샘플:")
                    for seg in segments[:2]:
                        print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")

            return output_path

        except Exception as e:
            raise IOError(f"SMI 파일 생성 실패: {e}")

    def generate(
        self,
        segments: List[Dict],
        output_path: str,
        format: str = "srt",
        verbose: bool = True
    ) -> Path:
        """
        자막 파일 생성 (포맷 자동 선택)

        Args:
            segments: 타임스탬프 포함 세그먼트 리스트
            output_path: 출력 파일 경로
            format: 자막 포맷 ("srt" 또는 "smi", 기본값: "srt")
            verbose: 진행 상황 출력 여부

        Returns:
            생성된 파일의 Path 객체

        Raises:
            ValueError: 지원하지 않는 포맷
        """
        format = format.lower()

        if format == "srt":
            return self.generate_srt(segments, output_path, verbose=verbose)
        elif format == "smi":
            return self.generate_smi(segments, output_path, verbose=verbose)
        else:
            raise ValueError(
                f"지원하지 않는 포맷: {format}\n"
                f"지원 포맷: srt, smi"
            )


# 편의 함수
def create_subtitle(
    segments: List[Dict],
    output_path: str,
    format: str = "srt",
    verbose: bool = True
) -> Path:
    """
    간단한 자막 생성 함수

    Args:
        segments: 타임스탬프 포함 세그먼트 리스트
        output_path: 출력 파일 경로
        format: 자막 포맷 ("srt" 또는 "smi")
        verbose: 진행 상황 출력

    Returns:
        생성된 파일의 Path 객체
    """
    generator = SubtitleGenerator()
    return generator.generate(segments, output_path, format=format, verbose=verbose)
