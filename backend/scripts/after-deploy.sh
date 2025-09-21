#!/bin/bash
set -e

# 기본 설정
REPOSITORY=/home/ubuntu/deploy
LOG_FILE="$REPOSITORY/deploy.log"

# 로그 파일로 모든 출력 리디렉션
exec > >(tee -a "$LOG_FILE") 2>&1

echo "> 🔵 Deployment script started at $(date)"

# 디렉토리 이동
cd $REPOSITORY/api_back

echo "> 🔵 Stop & Remove docker services."
docker compose down || echo "Failed to stop docker services."

echo "> 🟢 Run new docker services."
docker compose up --build -d || echo "Failed to start docker services."

echo "> 🔵 Deployment script finished at $(date)"