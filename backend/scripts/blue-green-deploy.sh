#!/bin/bash

# Blue/Green 무중단 배포 스크립트
set -e

echo "🚀 Blue/Green 무중단 배포를 시작합니다..."

# 환경변수 설정
# CodeDeploy 배포 디렉토리 찾기
DEPLOYMENT_ROOT="/opt/codedeploy-agent/deployment-root"

# 실제 배포된 파일들이 있는 디렉토리 찾기
echo "DEBUG: deployment-root 내용 확인"
find $DEPLOYMENT_ROOT -type f -name "*.yml" -o -name "*.conf" 2>/dev/null | head -5

# 가장 최근 배포 디렉토리에서 실제 파일들 찾기 (수정 시간 기준으로 정렬)
PROJECT_DIR=$(find $DEPLOYMENT_ROOT -type f -name "docker-compose.yml" -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -1 | cut -d' ' -f2- | xargs dirname)

if [ -z "$PROJECT_DIR" ]; then
    # 대안: ls로 가장 최근 디렉토리 찾기
    LATEST_APP_DIR=$(ls -td $DEPLOYMENT_ROOT/*/d-*/deployment-archive 2>/dev/null | head -1)
    if [ -n "$LATEST_APP_DIR" ] && [ -f "$LATEST_APP_DIR/docker-compose.yml" ]; then
        PROJECT_DIR="$LATEST_APP_DIR"
    else
        echo "❌ docker-compose.yml을 찾을 수 없습니다. 배포 실패."
        exit 1
    fi
fi

NGINX_CONFIG="$PROJECT_DIR/nginx.conf"
BACKUP_CONFIG="$PROJECT_DIR/nginx.conf.backup"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

echo "DEBUG: 현재 작업 디렉토리: $(pwd)"
echo "DEBUG: 프로젝트 디렉토리: $PROJECT_DIR"
echo "DEBUG: nginx.conf 경로: $NGINX_CONFIG"

# 프로젝트 디렉토리로 이동
cd "$PROJECT_DIR"

# 디렉토리 권한 확인 및 수정
echo "DEBUG: 현재 사용자: $(whoami)"
echo "DEBUG: 디렉토리 권한 확인"
ls -la "$PROJECT_DIR" || echo "디렉토리 목록 확인 실패"

# 프로젝트 디렉토리 전체 소유자 root로 변경
sudo chown -R root:root "$PROJECT_DIR"
# 디렉토리는 755, 파일은 644로 권한 설정
sudo find "$PROJECT_DIR" -type d -exec chmod 755 {} \;
sudo find "$PROJECT_DIR" -type f -exec chmod 644 {} \;

# 현재 활성 서버 확인
check_active_server() {
    if grep -q "backup" $NGINX_CONFIG; then
        if grep "fastapi-blue:8000" $NGINX_CONFIG | grep -q "backup"; then
            echo "green"
        else
            echo "blue"
        fi
    else
        echo "blue"  # 기본값
    fi
}

# 헬스체크 함수
health_check() {
    local port=$1
    local attempts=5
    
    echo "포트 $port 헬스체크 중..."
    
    for i in $(seq 1 $attempts); do
        if curl -f http://localhost:$port/api/health > /dev/null 2>&1; then
            echo "✅ 포트 $port 헬스체크 성공!"
            return 0
        fi
        echo "⏳ 헬스체크 시도 $i/$attempts..."
        sleep 2
    done
    
    echo "❌ 포트 $port 헬스체크 실패!"
    return 1
}

# Nginx 설정 업데이트
update_nginx_config() {
    local active_server=$1
    
    echo "Nginx 설정을 업데이트합니다. 활성 서버: $active_server"
    
    # 임시 파일 경로 설정
    TEMP_NGINX="/tmp/nginx.conf.temp"
    BACKUP_CONFIG="/tmp/nginx.conf.backup"
    
    # 백업 생성
    cp "$NGINX_CONFIG" "$BACKUP_CONFIG"
    
    # 임시 파일로 복사
    cp "$NGINX_CONFIG" "$TEMP_NGINX"
    
    if [ "$active_server" = "blue" ]; then
        # blue 활성, green backup
        sed 's/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Blue 환경/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s; # Blue 환경/' "$TEMP_NGINX" > "$TEMP_NGINX.1"
        sed 's/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s; # Green 환경/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Green 환경/' "$TEMP_NGINX.1" > "$TEMP_NGINX.2"
        mv "$TEMP_NGINX.2" "$TEMP_NGINX"
    else
        # green 활성, blue backup
        sed 's/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s; # Blue 환경/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Blue 환경/' "$TEMP_NGINX" > "$TEMP_NGINX.1"
        sed 's/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Green 환경/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s; # Green 환경/' "$TEMP_NGINX.1" > "$TEMP_NGINX.2"
        mv "$TEMP_NGINX.2" "$TEMP_NGINX"
    fi
    
    # 편집된 파일을 원래 위치로 복사
    cp "$TEMP_NGINX" "$NGINX_CONFIG"
    
    # 임시 파일 정리
    rm -f "$TEMP_NGINX" "$TEMP_NGINX.1" "$TEMP_NGINX.2"
}

# Nginx 리로드
reload_nginx() {
    echo "Nginx 설정을 리로드합니다..."
    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T nginx nginx -s reload; then
        echo "✅ Nginx 리로드 성공!"
        return 0
    else
        echo "❌ Nginx 리로드 실패!"
        cp $BACKUP_CONFIG $NGINX_CONFIG
        return 1
    fi
}

# 메인 배포 로직
main() {
    # 현재 활성 서버 확인
    ACTIVE_SERVER=$(check_active_server)
    echo "현재 활성 서버: $ACTIVE_SERVER"
    
    # 대기 서버 결정
    if [ "$ACTIVE_SERVER" = "blue" ]; then
        STANDBY_SERVER="green"
        STANDBY_PORT="8001"
        STANDBY_SERVICE="fastapi-green"
    else
        STANDBY_SERVER="blue"
        STANDBY_PORT="8000"
        STANDBY_SERVICE="fastapi-blue"
    fi
    
    echo "배포 대상: $STANDBY_SERVER (포트: $STANDBY_PORT)"
    
    # 1. 대기 서버 재시작
    echo "🔄 $STANDBY_SERVER 서버 재시작 중..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" stop $STANDBY_SERVICE
    docker-compose -f "$DOCKER_COMPOSE_FILE" build $STANDBY_SERVICE
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d $STANDBY_SERVICE
    
    echo "⏳ 컨테이너 시작 대기 중..."
    sleep 10
    
    # 2. 헬스체크
    if ! health_check $STANDBY_PORT; then
        echo "❌ 헬스체크 실패. 배포 중단."
        exit 1
    fi
    
    # 3. 트래픽 전환
    echo "🔀 트래픽을 $STANDBY_SERVER로 전환..."
    update_nginx_config $STANDBY_SERVER
    
    if ! reload_nginx; then
        echo "❌ Nginx 리로드 실패. 배포 중단."
        exit 1
    fi
    
    # 4. 최종 확인
    sleep 3
    if ! health_check 80; then
        echo "❌ 최종 확인 실패. 롤백 중..."
        update_nginx_config $ACTIVE_SERVER
        reload_nginx
        exit 1
    fi
    
    echo "✅ Blue/Green 배포 완료!"
    echo "새로운 활성 서버: $STANDBY_SERVER"
}

# 스크립트 실행
main "$@"