#!/usr/bin/env python3
"""
AutoKR - 일본어 동영상 자막 자동 생성 시스템
실행 진입점
"""

import sys
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cli import main

if __name__ == '__main__':
    main()
