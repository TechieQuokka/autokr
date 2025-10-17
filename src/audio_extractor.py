"""
AudioExtractor - 동영상에서 오디오 추출
FFmpeg를 사용하여 동영상에서 음성 파일 추출
"""

import subprocess
from pathlib import Path
from typing import Optional


class AudioExtractor:
    """동영상에서 오디오 추출"""

    def __init__(self, output_dir: str = "temp"):
        """
        Args:
            output_dir: 오디오 파일을 저장할 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        audio_format: str = "wav",
        sample_rate: int = 16000,
        channels: int = 1
    ) -> Path:
        """
        동영상에서 오디오 추출

        Args:
            video_path: 입력 동영상 파일 경로
            output_path: 출력 오디오 파일 경로 (None이면 자동 생성)
            audio_format: 출력 오디오 포맷 (wav, mp3)
            sample_rate: 샘플링 레이트 (기본값: 16000Hz - Whisper 권장)
            channels: 오디오 채널 수 (1: mono, 2: stereo)

        Returns:
            추출된 오디오 파일 경로

        Raises:
            FileNotFoundError: 동영상 파일이 존재하지 않을 때
            RuntimeError: FFmpeg 실행 실패 시
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"동영상 파일을 찾을 수 없습니다: {video_path}")

        # 출력 경로 설정
        if output_path is None:
            output_file = self.output_dir / f"audio.{audio_format}"
        else:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg 명령어 구성
        # -i: 입력 파일
        # -vn: 비디오 스트림 제거
        # -acodec: 오디오 코덱 설정
        # -ar: 샘플링 레이트
        # -ac: 채널 수
        # -y: 덮어쓰기 확인 없이 진행
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # 비디오 제거
            '-ar', str(sample_rate),  # 샘플링 레이트
            '-ac', str(channels),  # 채널 수
            '-y',  # 덮어쓰기
            str(output_file)
        ]

        # WAV 포맷인 경우 PCM 코덱 사용
        if audio_format.lower() == 'wav':
            cmd.insert(4, '-acodec')
            cmd.insert(5, 'pcm_s16le')

        try:
            # FFmpeg 실행
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            if not output_file.exists():
                raise RuntimeError("오디오 파일이 생성되지 않았습니다.")

            return output_file

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FFmpeg 실행 실패:\n{e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "FFmpeg를 찾을 수 없습니다. FFmpeg가 설치되어 있고 PATH에 등록되어 있는지 확인하세요.\n"
                "설치: sudo apt-get install ffmpeg (Ubuntu/Debian) 또는 brew install ffmpeg (macOS)"
            )

    def cleanup(self):
        """임시 오디오 파일 삭제"""
        for audio_file in self.output_dir.glob("audio.*"):
            audio_file.unlink()
