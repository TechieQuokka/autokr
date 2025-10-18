"""
AutoKR - CLI Interface
일본어 동영상 자막 자동 생성 시스템
"""

__version__ = "1.0.1"

import argparse
import sys
import subprocess
import json
from pathlib import Path

from audio_extractor import AudioExtractor
from subtitle_gen import SubtitleGenerator


def get_python_executable():
    """PyInstaller 환경에서 올바른 Python 실행 파일 경로 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 환경
        # 시스템의 Python 인터프리터를 찾아서 사용
        import shutil
        python_exec = shutil.which('python3') or shutil.which('python')
        if not python_exec:
            raise RuntimeError("시스템에서 Python 인터프리터를 찾을 수 없습니다. Python이 설치되어 있는지 확인하세요.")
        return python_exec
    else:
        # 일반 Python 환경
        return sys.executable


def main():
    """CLI 진입점"""
    parser = argparse.ArgumentParser(
        description='AutoKR - 일본어 동영상 자막 자동 생성',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'AutoKR {__version__}',
        help='버전 정보 출력'
    )

    parser.add_argument(
        '-i', '--input',
        required=True,
        type=str,
        help='입력 동영상 파일 경로'
    )

    parser.add_argument(
        '-o', '--output',
        required=False,
        type=str,
        help='출력 자막 파일 경로 (미지정시 입력 파일명 기반 자동 생성)'
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
        default='facebook/nllb-200-3.3B',
        choices=['facebook/nllb-200-distilled-600M', 'facebook/nllb-200-1.3B', 'facebook/nllb-200-3.3B'],
        help='번역 모델 (기본값: facebook/nllb-200-3.3B)'
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

    # 출력 경로 자동 생성 또는 검증
    if args.output:
        output_path = Path(args.output)
    else:
        # 입력 파일명에서 확장자를 제거하고 format에 맞는 확장자 추가
        output_path = input_path.parent / f"{input_path.stem}.{args.format}"

    if output_path.exists():
        response = input(f"파일이 이미 존재합니다: {output_path}. 덮어쓰시겠습니까? (y/n): ")
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

        # 2. 음성 → 텍스트 (Whisper) - 별도 프로세스
        print("\n🎤 Step 2/4: 음성 → 텍스트 변환 (Whisper)")
        print("-" * 60)

        # 중간 결과 저장 경로
        temp_transcription = Path("temp/transcription.json")
        temp_transcription.parent.mkdir(parents=True, exist_ok=True)

        # Whisper 워커 프로세스 실행
        if getattr(sys, 'frozen', False):
            # PyInstaller 빌드 환경: _internal 디렉토리에서 스크립트 찾기
            base_path = Path(sys._MEIPASS)
            worker_script = base_path / "src" / "worker_transcribe.py"
        else:
            # 일반 Python 환경
            worker_script = Path(__file__).parent / "worker_transcribe.py"

        cmd = [
            get_python_executable(),  # 올바른 Python 인터프리터
            str(worker_script),
            str(audio_path),
            args.whisper,
            args.language,
            str(temp_transcription)
        ]

        print(f"   🚀 Whisper 프로세스 시작 (별도 메모리 공간)")
        result = subprocess.run(cmd, check=True)

        if result.returncode != 0:
            raise RuntimeError("Whisper 변환 프로세스 실패")

        # 결과 로드
        transcription_data = json.loads(temp_transcription.read_text(encoding='utf-8'))
        print(f"✅ 음성 변환 완료: {len(transcription_data['segments'])}개 세그먼트")
        print(f"   💾 중간 결과 저장: {temp_transcription}")

        # 프로세스가 종료되면서 Whisper 모델의 GPU 메모리가 자동으로 해제됨!

        # 3. 번역 (일본어 → 한국어) - 별도 프로세스
        print("\n🌐 Step 3/4: 번역 (일본어 → 한국어)")
        print("-" * 60)

        # 번역 결과 저장 경로
        temp_translation = Path("temp/translation.json")

        # NLLB 워커 프로세스 실행
        if getattr(sys, 'frozen', False):
            # PyInstaller 빌드 환경: _internal 디렉토리에서 스크립트 찾기
            base_path = Path(sys._MEIPASS)
            worker_script = base_path / "src" / "worker_translate.py"
        else:
            # 일반 Python 환경
            worker_script = Path(__file__).parent / "worker_translate.py"

        cmd = [
            get_python_executable(),  # 올바른 Python 인터프리터
            str(worker_script),
            str(temp_transcription),
            args.translate,
            "16",  # batch_size
            str(temp_translation)
        ]

        print(f"   🚀 번역 프로세스 시작 (별도 메모리 공간)")
        result = subprocess.run(cmd, check=True)

        if result.returncode != 0:
            raise RuntimeError("번역 프로세스 실패")

        # 결과 로드
        translated_segments = json.loads(temp_translation.read_text(encoding='utf-8'))
        print(f"✅ 번역 완료: {len(translated_segments)}개 세그먼트")
        print(f"   💾 중간 결과 저장: {temp_translation}")

        # 프로세스가 종료되면서 NLLB 모델의 GPU 메모리가 자동으로 해제됨!

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

        # 중간 JSON 파일 정리
        if temp_transcription.exists():
            temp_transcription.unlink()
            print("✅ 중간 변환 파일 삭제됨")
        if temp_translation.exists():
            temp_translation.unlink()
            print("✅ 중간 번역 파일 삭제됨")        

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
