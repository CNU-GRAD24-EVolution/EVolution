#!/bin/bash

# Blue/Green 무중단 배포 스크립트
set -e

echo "🚀 Blue/Green 무중단 배포를 시작합니다..."

# 환경변수 설정
NGINX_CONFIG="nginx.conf"
BACKUP_CONFIG="nginx.conf.backup"

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
    
    # 백업 생성
    cp $NGINX_CONFIG $BACKUP_CONFIG
    
    if [ "$active_server" = "blue" ]; then
        # blue 활성, green backup
        sed -i.bak 's/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Blue 환경/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s; # Blue 환경/' $NGINX_CONFIG
        sed -i.bak 's/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s; # Green 환경/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Green 환경/' $NGINX_CONFIG
    else
        # green 활성, blue backup
        sed -i.bak 's/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s; # Blue 환경/server fastapi-blue:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Blue 환경/' $NGINX_CONFIG
        sed -i.bak 's/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s backup; # Green 환경/server fastapi-green:8000 weight=1 max_fails=3 fail_timeout=30s; # Green 환경/' $NGINX_CONFIG
    fi
    
    rm -f ${NGINX_CONFIG}.bak
}

# Nginx 리로드
reload_nginx() {
    echo "Nginx 설정을 리로드합니다..."
    if docker-compose exec -T nginx nginx -s reload; then
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
    docker-compose stop $STANDBY_SERVICE
    docker-compose build $STANDBY_SERVICE
    docker-compose up -d $STANDBY_SERVICE
    
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
