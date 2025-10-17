#!/bin/bash
# AutoKR 빌드 스크립트

set -e  # 에러 발생시 중단

echo "=========================================="
echo "AutoKR 실행 파일 빌드"
echo "=========================================="

# PyInstaller 설치 확인
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller 설치 중..."
    pip install pyinstaller
fi

# 이전 빌드 결과 정리
echo "이전 빌드 결과 정리 중..."
rm -rf build dist

# PyInstaller 실행
echo "빌드 시작..."
pyinstaller autokr.spec --clean

# 빌드 결과 확인
if [ -f "dist/autokr/autokr" ]; then
    echo ""
    echo "=========================================="
    echo "✅ 빌드 성공!"
    echo "=========================================="
    echo "실행 파일 위치: dist/autokr/autokr"
    echo ""
    echo "사용 방법:"
    echo "  ./dist/autokr/autokr -i <입력동영상> -o <출력자막>"
    echo ""
    echo "주의사항:"
    echo "  - FFmpeg가 시스템에 설치되어 있어야 합니다"
    echo "  - GPU 사용시 CUDA가 설치되어 있어야 합니다"
    echo "  - 모델은 처음 실행시 자동으로 다운로드됩니다"
    echo "=========================================="
else
    echo "❌ 빌드 실패!"
    exit 1
fi
