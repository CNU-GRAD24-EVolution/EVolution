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
    local port
    
    # 색상에 따라 포트 결정
    if [ "$color" = "blue" ]; then
        port="8000"
    else
        port="8001"
    fi
    
    echo "📊 $color 환경 헬스체크 중... (포트: $port)"
    
    for i in $(seq 1 $attempts); do
        # 컨테이너가 실행 중인지 확인
        if ! docker-compose -p ${DOCKER_APP_NAME}-${color} -f docker-compose.yml ps fastapi-${color} | grep -q "Up"; then
            echo "⏳ $color 컨테이너 시작 대기 중... ($i/$attempts)"
            sleep 3
            continue
        fi
        
        # EC2에서 직접 포트로 헬스체크 시도
        if curl -f http://localhost:$port/api/health > /dev/null 2>&1; then
            echo "✅ $color 환경 헬스체크 성공! (포트: $port)"
            return 0
        fi
        echo "⏳ $color 헬스체크 시도 $i/$attempts... (포트: $port)"
        sleep 3
    done
    
    echo "❌ $color 환경 헬스체크 실패! (포트: $port)"
    return 1
}

# Nginx 설정 업데이트 함수
update_nginx_config() {
    local active_color=$1
    local nginx_config="$REPOSITORY/nginx.conf"
    local temp_config="$REPOSITORY/nginx.conf.temp"
    
    echo "🔧 Nginx 설정을 $active_color 환경으로 업데이트 중..."
    
    # 백업 생성
    cp "$nginx_config" "$nginx_config.backup"
    
    # 임시 파일로 복사
    cp "$nginx_config" "$temp_config"
    
    if [ "$active_color" = "blue" ]; then
        # Blue 활성화, Green 비활성화
        sed -i 's/server fastapi-blue:8000.*$/server fastapi-blue:8000 max_fails=3 fail_timeout=30s; # Blue 환경/' "$temp_config"
        sed -i 's/server fastapi-green:8000.*$/# server fastapi-green:8000 max_fails=3 fail_timeout=30s; # Green 환경 (비활성)/' "$temp_config"
    else
        # Green 활성화, Blue 비활성화
        sed -i 's/server fastapi-blue:8000.*$/# server fastapi-blue:8000 max_fails=3 fail_timeout=30s; # Blue 환경 (비활성)/' "$temp_config"
        sed -i 's/.*server fastapi-green:8000.*$/server fastapi-green:8000 max_fails=3 fail_timeout=30s; # Green 환경/' "$temp_config"
    fi
    
    # 편집된 파일을 원래 위치로 복사
    cp "$temp_config" "$nginx_config"
    rm -f "$temp_config"
    
    echo "✅ Nginx 설정 업데이트 완료 ($active_color 활성)"
}

# Nginx 재시작 함수
restart_nginx() {
    echo "🔄 Nginx 재시작 중..."
    
    if docker-compose -f docker-compose.yml restart nginx; then
        echo "✅ Nginx 재시작 성공!"
        sleep 3  # nginx가 완전히 시작될 때까지 대기
        return 0
    else
        echo "❌ Nginx 재시작 실패!"
        return 1
    fi
}

# Nginx 시작 함수
start_nginx_if_needed() {
    if ! docker ps | grep -q "nginx"; then
        echo "🌐 Nginx 로드 밸런서 시작..."
        # nginx만 단독으로 시작
        docker-compose -f docker-compose.yml up -d nginx --no-deps
    else
        echo "✅ Nginx 로드 밸런서가 이미 실행 중입니다."
    fi
}

# Nginx 시작 확인 (한 번만)
start_nginx_if_needed

# 컨테이너 스위칭
if [ -z "$EXIST_BLUE" ]; then
    echo "🔵 Blue 환경으로 배포합니다..."
    
    # Blue 환경 시작
    docker-compose -p ${DOCKER_APP_NAME}-blue -f docker-compose.yml up -d fastapi-blue
    BEFORE_COMPOSE_COLOR="green"
    AFTER_COMPOSE_COLOR="blue"
else
    echo "🟢 Green 환경으로 배포합니다..."
    
    # Green 환경 시작
    docker-compose -p ${DOCKER_APP_NAME}-green -f docker-compose.yml up -d fastapi-green
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
        echo "🔄 Nginx 설정을 $AFTER_COMPOSE_COLOR 환경으로 전환..."
        
        # Nginx 설정 업데이트
        if update_nginx_config $AFTER_COMPOSE_COLOR && restart_nginx; then
            echo "✅ Nginx 설정 전환 완료!"
            
            # 전환 후 최종 헬스체크 (nginx를 통한)
            echo "🔍 Nginx를 통한 최종 헬스체크..."
            if curl -f http://localhost:80/api/health > /dev/null 2>&1; then
                echo "✅ Nginx를 통한 헬스체크 성공!"
            else
                echo "⚠️ Nginx를 통한 헬스체크 실패, 하지만 계속 진행..."
            fi
            
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
            echo "❌ Nginx 설정 전환 실패! 롤백 중..."
            # Nginx 설정 롤백
            cp "$REPOSITORY/nginx.conf.backup" "$REPOSITORY/nginx.conf" 2>/dev/null || true
            restart_nginx
            
            # 컨테이너도 롤백
            docker-compose -p ${DOCKER_APP_NAME}-${AFTER_COMPOSE_COLOR} -f docker-compose.yml down 2>/dev/null || true
            
            if [ "$BEFORE_COMPOSE_COLOR" != "none" ]; then
                echo "🔄 이전 $BEFORE_COMPOSE_COLOR 환경을 복구합니다..."
                docker-compose -p ${DOCKER_APP_NAME}-${BEFORE_COMPOSE_COLOR} -f docker-compose.yml up -d fastapi-${BEFORE_COMPOSE_COLOR}
            fi
            
            echo "❌ 배포 실패! 롤백 완료."
            exit 1
        fi
        
    else
        echo "❌ $AFTER_COMPOSE_COLOR 환경 헬스체크 실패!"
        echo "🔄 $AFTER_COMPOSE_COLOR 환경을 롤백합니다..."
        
        # 실패한 환경 정리
        docker-compose -p ${DOCKER_APP_NAME}-${AFTER_COMPOSE_COLOR} -f docker-compose.yml down 2>/dev/null || true
        
        # 이전 환경이 있다면 다시 시작
        if [ "$BEFORE_COMPOSE_COLOR" != "none" ]; then
            echo "🔄 이전 $BEFORE_COMPOSE_COLOR 환경을 복구합니다..."
            docker-compose -p ${DOCKER_APP_NAME}-${BEFORE_COMPOSE_COLOR} -f docker-compose.yml up -d fastapi-${BEFORE_COMPOSE_COLOR}
        fi
        
        echo "❌ 배포 실패! 롤백 완료."
        exit 1
    fi
else
    echo "❌ $AFTER_COMPOSE_COLOR 환경 시작 실패!"
    echo "❌ 배포 실패!"
    exit 1
fi
