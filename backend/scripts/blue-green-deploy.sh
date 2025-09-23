#!/bin/bash
set -e

# 기본 설정
REPOSITORY=/home/ubuntu/deploy/api_back
LOG_FILE="$REPOSITORY/deploy.log"

# 로그 파일로 모든 출력 리디렉션
exec > >(tee -a "$LOG_FILE") 2>&1

echo "> 🔵 Blue/Green 무중단 배포 시작 at $(date)"

# 디렉토리 이동
cd $REPOSITORY

echo "DEBUG: 현재 작업 디렉토리: $(pwd)"
echo "DEBUG: 현재 사용자: $(whoami)"

# 앱 이름 설정
DOCKER_APP_NAME="fastapi"

# Blue를 기준으로 현재 떠있는 컨테이너를 체크한다.
EXIST_BLUE=$(docker-compose -p ${DOCKER_APP_NAME}-blue -f docker-compose.yml ps fastapi-blue 2>/dev/null | grep Up || echo "")

echo "현재 Blue 컨테이너 상태 확인..."
if [ -n "$EXIST_BLUE" ]; then
    echo "✅ Blue 컨테이너가 실행 중입니다."
else
    echo "❌ Blue 컨테이너가 실행되지 않고 있습니다."
fi

# 헬스체크 함수
health_check() {
    local color=$1
    local attempts=10
    
    echo "📊 $color 환경 헬스체크 중..."
    
    for i in $(seq 1 $attempts); do
        # 컨테이너가 실행 중인지 확인
        if ! docker-compose -p ${DOCKER_APP_NAME}-${color} -f docker-compose.yml ps fastapi-${color} | grep -q "Up"; then
            echo "⏳ $color 컨테이너 시작 대기 중... ($i/$attempts)"
            sleep 3
            continue
        fi
        
        # API 헬스체크 시도
        if docker-compose -p ${DOCKER_APP_NAME}-${color} -f docker-compose.yml exec -T fastapi-${color} curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
            echo "✅ $color 환경 헬스체크 성공!"
            return 0
        fi
        echo "⏳ $color 헬스체크 시도 $i/$attempts..."
        sleep 3
    done
    
    echo "❌ $color 환경 헬스체크 실패!"
    return 1
}

# 컨테이너 스위칭
if [ -z "$EXIST_BLUE" ]; then
    echo "� Blue 환경으로 배포합니다..."
    
    # Blue 환경 시작
    docker-compose -p ${DOCKER_APP_NAME}-blue -f docker-compose.yml up -d fastapi-blue nginx-lb
    BEFORE_COMPOSE_COLOR="green"
    AFTER_COMPOSE_COLOR="blue"
else
    echo "🟢 Green 환경으로 배포합니다..."
    
    # Green 환경 시작
    docker-compose -p ${DOCKER_APP_NAME}-green -f docker-compose.yml up -d fastapi-green nginx-lb
    BEFORE_COMPOSE_COLOR="blue"
    AFTER_COMPOSE_COLOR="green"
fi

echo "⏳ 새로운 $AFTER_COMPOSE_COLOR 환경 안정화 대기 중..."
sleep 10

# 새로운 컨테이너가 제대로 떴는지 확인
echo "새로운 $AFTER_COMPOSE_COLOR 환경 상태 확인..."
EXIST_AFTER=$(docker-compose -p ${DOCKER_APP_NAME}-${AFTER_COMPOSE_COLOR} -f docker-compose.yml ps fastapi-${AFTER_COMPOSE_COLOR} | grep Up || echo "")

if [ -n "$EXIST_AFTER" ]; then
    echo "✅ $AFTER_COMPOSE_COLOR 환경이 성공적으로 시작되었습니다."
    
    # 헬스체크 수행
    if health_check $AFTER_COMPOSE_COLOR; then
        echo "🔄 이전 $BEFORE_COMPOSE_COLOR 환경을 종료합니다..."
        
        # 이전 컨테이너 종료
        docker-compose -p ${DOCKER_APP_NAME}-${BEFORE_COMPOSE_COLOR} -f docker-compose.yml down 2>/dev/null || true
        echo "✅ $BEFORE_COMPOSE_COLOR 환경이 종료되었습니다."
        
        echo ""
        echo "🎉 Blue/Green 배포 완료!"
        echo "📊 배포 결과:"
        echo "   - 새로운 활성 환경: $AFTER_COMPOSE_COLOR"
        echo "   - 종료된 환경: $BEFORE_COMPOSE_COLOR"
        echo "   - 배포 시간: $(date)"
        
        # 최종 상태 확인
        echo ""
        echo "🔍 최종 컨테이너 상태:"
        docker-compose -p ${DOCKER_APP_NAME}-${AFTER_COMPOSE_COLOR} -f docker-compose.yml ps
        
    else
        echo "❌ $AFTER_COMPOSE_COLOR 환경 헬스체크 실패!"
        echo "🔄 $AFTER_COMPOSE_COLOR 환경을 롤백합니다..."
        
        # 실패한 환경 정리
        docker-compose -p ${DOCKER_APP_NAME}-${AFTER_COMPOSE_COLOR} -f docker-compose.yml down 2>/dev/null || true
        
        # 이전 환경이 있다면 다시 시작
        if [ "$BEFORE_COMPOSE_COLOR" != "none" ]; then
            echo "🔄 이전 $BEFORE_COMPOSE_COLOR 환경을 복구합니다..."
            docker-compose -p ${DOCKER_APP_NAME}-${BEFORE_COMPOSE_COLOR} -f docker-compose.yml up -d
        fi
        
        echo "❌ 배포 실패! 롤백 완료."
        exit 1
    fi
else
    echo "❌ $AFTER_COMPOSE_COLOR 환경 시작 실패!"
    echo "❌ 배포 실패!"
    exit 1
fi
