#!/usr/bin/env python3
"""
Whisper 전용 워커 프로세스
별도 프로세스로 실행되어 종료 시 GPU 메모리가 완전히 해제됨
"""

import sys
import json
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from transcriber import Transcriber


def main():
    """Whisper 변환 워커 메인 함수"""
    if len(sys.argv) != 5:
        print("사용법: worker_transcribe.py <audio_path> <model> <language> <output_json>", file=sys.stderr)
        print("예시: worker_transcribe.py temp/audio.wav large-v3 ja temp/transcription.json", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    model_name = sys.argv[2]
    language = sys.argv[3]
    output_json = sys.argv[4]

    # 입력 파일 검증
    audio_file = Path(audio_path)
    if not audio_file.exists():
        print(f"오류: 오디오 파일을 찾을 수 없습니다: {audio_path}", file=sys.stderr)
        sys.exit(1)

    # 출력 디렉토리 생성
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🎤 Whisper 워커 프로세스 시작")
    print(f"   - 오디오: {audio_path}")
    print(f"   - 모델: {model_name}")
    print(f"   - 언어: {language}")
    print(f"   - 출력: {output_json}")

    try:
        # Whisper 변환 실행
        transcriber = Transcriber(
            model_name=model_name,
            language=language
        )

        result = transcriber.transcribe_with_full_text(
            str(audio_file),
            verbose=True
        )

        # 결과를 JSON으로 저장
        output_data = {
            "segments": result["segments"],
            "text": result["text"],
            "language": result["language"],
            "model": model_name
        }

        output_path.write_text(
            json.dumps(output_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"\n✅ Whisper 변환 완료")
        print(f"   - 세그먼트: {len(result['segments'])}개")
        print(f"   - 결과 파일: {output_json}")

        # 메모리 정리
        transcriber.clear_cache()

        # 프로세스 종료 시 자동으로 모든 메모리 해제됨
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Whisper 변환 실패: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
