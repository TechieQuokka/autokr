"""
AutoKR - CLI Interface
일본어 동영상 자막 자동 생성 시스템
"""

import argparse
import sys
from pathlib import Path

from audio_extractor import AudioExtractor
from transcriber import Transcriber
from translator import Translator
from subtitle_gen import SubtitleGenerator


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description='AutoKR - 일본어 동영상 자막 자동 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        type=str,
        help='입력 동영상 파일 경로'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        type=str,
        help='출력 자막 파일 경로'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['srt', 'smi'],
        default='srt',
        help='자막 포맷 (기본값: srt)'
    )

    parser.add_argument(
        '-w', '--whisper',
        default='large-v3',
        choices=['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3'],
        help='Whisper 모델 크기 (기본값: large-v3)'
    )

    parser.add_argument(
        '-t', '--translate',
        default='facebook/nllb-200-1.3B',
        choices=['facebook/nllb-200-distilled-600M', 'facebook/nllb-200-1.3B', 'facebook/nllb-200-3.3B'],
        help='번역 모델 (기본값: facebook/nllb-200-1.3B)'
    )

    parser.add_argument(
        '--language',
        default='ja',
        help='음성 언어 코드 (기본값: ja=일본어)'
    )

    parser.add_argument(
        '--keep-audio',
        action='store_true',
        help='임시 오디오 파일 유지'
    )

    args = parser.parse_args()

    # 입력 파일 존재 확인
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"오류: 입력 파일을 찾을 수 없습니다: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 출력 경로 검증
    output_path = Path(args.output)
    if output_path.exists():
        response = input(f"파일이 이미 존재합니다: {args.output}. 덮어쓰시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("작업이 취소되었습니다.")
            sys.exit(0)

    print("=" * 60)
    print("AutoKR - 일본어 동영상 자막 자동 생성")
    print("=" * 60)
    print(f"입력 동영상: {args.input}")
    print(f"출력 자막: {args.output}")
    print(f"자막 포맷: {args.format}")
    print(f"Whisper 모델: {args.whisper}")
    print(f"번역 모델: {args.translate}")
    print(f"언어: {args.language}")
    print("=" * 60)

    try:
        # 1. 오디오 추출
        print("\n📹 Step 1/4: 오디오 추출")
        print("-" * 60)
        extractor = AudioExtractor(output_dir="temp")
        audio_path = extractor.extract(
            str(input_path),
            audio_format="wav",
            sample_rate=16000,
            channels=1
        )
        print(f"✅ 오디오 추출 완료: {audio_path}")

        # 2. 음성 → 텍스트 (Whisper)
        print("\n🎤 Step 2/4: 음성 → 텍스트 변환 (Whisper)")
        print("-" * 60)
        transcriber = Transcriber(
            model_name=args.whisper,
            language=args.language
        )
        result = transcriber.transcribe_with_full_text(
            str(audio_path),
            verbose=True
        )
        print(f"✅ 음성 변환 완료: {len(result['segments'])}개 세그먼트")
        transcriber.clear_cache()

        # 3. 번역 (일본어 → 한국어)
        print("\n🌐 Step 3/4: 번역 (일본어 → 한국어)")
        print("-" * 60)
        translator = Translator(
            model_name=args.translate,
            source_lang="jpn_Jpan",
            target_lang="kor_Hang"
        )
        translated_segments = translator.translate_segments(
            result['segments'],
            verbose=True,
            batch_size=8
        )
        print(f"✅ 번역 완료: {len(translated_segments)}개 세그먼트")
        translator.clear_cache()

        # 4. 자막 파일 생성
        print("\n📝 Step 4/4: 자막 파일 생성")
        print("-" * 60)
        generator = SubtitleGenerator()
        subtitle_path = generator.generate(
            translated_segments,
            str(output_path),
            format=args.format,
            verbose=True
        )
        print(f"✅ 자막 파일 생성 완료: {subtitle_path}")

        # 정리
        print("\n🧹 정리 중...")
        if not args.keep_audio:
            extractor.cleanup()
            print("✅ 임시 오디오 파일 삭제됨")
        else:
            print(f"ℹ️  오디오 파일 유지: {audio_path}")        

        print("\n" + "=" * 60)
        print("✅ 모든 작업 완료!")
        print("=" * 60)
        print(f"📄 생성된 자막 파일: {subtitle_path}")
        print(f"📊 통계:")
        print(f"   - 총 세그먼트: {len(translated_segments)}개")
        print(f"   - 자막 포맷: {args.format.upper()}")
        print(f"   - 처리 완료")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
