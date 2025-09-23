#!/bin/bash

# 권한 수정 스크립트
echo "🔧 배포 디렉토리 권한 수정 중..."

DEPLOY_DIR="/home/ubuntu/deploy/api_back"

# 배포 디렉토리가 존재하면 권한 수정
if [ -d "$DEPLOY_DIR" ]; then
    echo "기존 배포 디렉토리 권한 수정: $DEPLOY_DIR"
    chown -R ubuntu:ubuntu "$DEPLOY_DIR"
    chmod -R 755 "$DEPLOY_DIR"
    find "$DEPLOY_DIR" -type f -exec chmod 644 {} \;
    find "$DEPLOY_DIR" -name "*.sh" -exec chmod 755 {} \;
fi

echo "✅ 권한 수정 완료"
