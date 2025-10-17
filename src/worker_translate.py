#!/usr/bin/env python3
"""
NLLB 번역 전용 워커 프로세스
별도 프로세스로 실행되어 종료 시 GPU 메모리가 완전히 해제됨
"""

import sys
import json
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from translator import Translator


def main():
    """NLLB 번역 워커 메인 함수"""
    if len(sys.argv) != 5:
        print("사용법: worker_translate.py <input_json> <model> <batch_size> <output_json>", file=sys.stderr)
        print("예시: worker_translate.py temp/transcription.json facebook/nllb-200-1.3B 8 temp/translation.json", file=sys.stderr)
        sys.exit(1)

    input_json = sys.argv[1]
    model_name = sys.argv[2]
    batch_size = int(sys.argv[3])
    output_json = sys.argv[4]

    # 입력 파일 검증
    input_file = Path(input_json)
    if not input_file.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {input_json}", file=sys.stderr)
        sys.exit(1)

    # 출력 디렉토리 생성
    output_path = Path(output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🌐 번역 워커 프로세스 시작")
    print(f"   - 입력: {input_json}")
    print(f"   - 모델: {model_name}")
    print(f"   - 배치 크기: {batch_size}")
    print(f"   - 출력: {output_json}")

    try:
        # 입력 데이터 로드
        input_data = json.loads(input_file.read_text(encoding='utf-8'))
        segments = input_data.get("segments", [])

        if not segments:
            print("⚠️ 경고: 변환할 세그먼트가 없습니다", file=sys.stderr)
            output_path.write_text(json.dumps([], ensure_ascii=False), encoding='utf-8')
            sys.exit(0)

        print(f"   - 세그먼트 수: {len(segments)}개")

        # 번역 실행
        translator = Translator(
            model_name=model_name,
            source_lang="jpn_Jpan",
            target_lang="kor_Hang"
        )

        translated_segments = translator.translate_segments(
            segments,
            verbose=True,
            batch_size=batch_size
        )

        # 결과를 JSON으로 저장
        output_path.write_text(
            json.dumps(translated_segments, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        print(f"\n✅ 번역 완료")
        print(f"   - 번역된 세그먼트: {len(translated_segments)}개")
        print(f"   - 결과 파일: {output_json}")

        # 메모리 정리
        translator.clear_cache()

        # 프로세스 종료 시 자동으로 모든 메모리 해제됨
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ 번역 실패: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
