#!/usr/bin/env python3
"""
AutoKR - 일본어 동영상 자막 자동 생성 시스템
실행 진입점
"""

import sys
import time
from pathlib import Path

# src 디렉토리를 Python 경로에 추가
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from cli import main

if __name__ == '__main__':
    # 전체 경과시간 측정 시작
    start_time = time.time()

    # CLI 실행
    main()

    # 전체 경과시간 계산 및 출력
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = elapsed_time % 60

    print("\n" + "=" * 60)
    print("⏱️  전체 처리 시간")
    print("=" * 60)
    if hours > 0:
        print(f"   총 소요 시간: {hours}시간 {minutes}분 {seconds:.2f}초")
    elif minutes > 0:
        print(f"   총 소요 시간: {minutes}분 {seconds:.2f}초")
    else:
        print(f"   총 소요 시간: {seconds:.2f}초")
    print("=" * 60)
