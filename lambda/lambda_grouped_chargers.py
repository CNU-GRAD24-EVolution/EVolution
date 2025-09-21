import json
import os
import urllib3
import psycopg2
from datetime import datetime
import logging

# Lambda에서 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# urllib3 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_secret(key):
    """
    환경변수에서 비밀 키 가져오기
    """
    return os.environ.get(key)

def connect_postgres():
    """
    PostgreSQL 연결
    """
    try:
        logger.info("PostgreSQL 연결 정보 준비 중...")
        host = get_secret('POSTGRES_HOST')
        database = get_secret('POSTGRES_DB')
        user = get_secret('POSTGRES_USER')
        password = get_secret('POSTGRES_PASSWORD')
        port = get_secret('POSTGRES_PORT') or 5432
        
        logger.info(f"연결 시도: {user}@{host}:{port}/{database}")
        
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port,
        )
        
        logger.info("PostgreSQL 연결 테스트 중...")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        logger.info("PostgreSQL 연결 테스트 성공!")
        
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL 연결 실패: {str(e)}")
        logger.error(f"오류 타입: {type(e).__name__}")
        raise

def get_ev_charger_info(page):
    """
    공공데이터 API에서 전기차 충전소 리스트 요청
    """
    base_url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo'
    service_key = get_secret('OPEN_API_SERVICE_KEY_DECODED')
    
    if not service_key:
        raise ValueError("OPEN_API_SERVICE_KEY_DECODED 환경변수가 설정되지 않았습니다.")

    # urllib3 HTTP 클라이언트 생성
    http = urllib3.PoolManager()
    
    # URL 파라미터 준비
    params = {
        'serviceKey': service_key,
        'pageNo': str(page),
        'numOfRows': '9999',
        'zcode': '30',
        'dataType': 'JSON'
    }
    
    try:
        # urllib3로 GET 요청
        response = http.request(
            'GET',
            base_url,
            fields=params,
            timeout=30
        )
        
        if response.status == 200:
            response_data = response.data.decode('utf-8')
            
            if '<errMsg>' not in response_data:
                data = json.loads(response_data)
                items = data.get('items', {}).get('item', [])
                logger.info(f"페이지 {page}에서 {len(items)}개 충전소 데이터 수신")
                return items
            else:
                logger.warning(f"페이지 {page} API 응답 오류: {response_data[:200]}")
                return []
        else:
            logger.warning(f"페이지 {page} HTTP 오류: {response.status}")
            return []
            
    except urllib3.exceptions.HTTPError as e:
        logger.error(f"페이지 {page} HTTP 요청 실패: {str(e)}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"페이지 {page} JSON 파싱 실패: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"페이지 {page} 데이터 처리 실패: {str(e)}")
        return []

def create_tables_if_not_exists(conn):
    """
    필요한 테이블들을 생성
    """
    cursor = conn.cursor()
    
    create_chargers_table = """
    CREATE TABLE IF NOT EXISTS chargers (
        id SERIAL PRIMARY KEY,
        stat_id VARCHAR(50) NOT NULL,
        chger_id VARCHAR(50) NOT NULL,
        stat_nm VARCHAR(200),
        addr TEXT,
        location TEXT,
        use_time TEXT,
        lat DECIMAL(10, 8),
        lng DECIMAL(11, 8),
        chger_type VARCHAR(10),
        stat VARCHAR(2),
        stat_upd_dt VARCHAR(20),
        last_tsdt VARCHAR(20),
        last_tedt VARCHAR(20),
        now_tsdt VARCHAR(20),
        output INT,
        method VARCHAR(10),
        del_yn VARCHAR(1),
        del_detail VARCHAR(200),
        busi_id VARCHAR(50),
        bnm VARCHAR(200),
        busi_nm VARCHAR(200),
        busi_call VARCHAR(20),
        zcode VARCHAR(10),
        zscode VARCHAR(10),
        kind VARCHAR(50),
        kind_detail VARCHAR(100),
        parking_free VARCHAR(1),
        note TEXT,
        limit_yn VARCHAR(1),
        limit_detail TEXT,
        traffic_yn VARCHAR(1),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(stat_id, chger_id)
    );
    """
    
    create_grouped_chargers_table = """
    CREATE TABLE IF NOT EXISTS grouped_chargers (
        stat_id VARCHAR(50) PRIMARY KEY,
        stat_nm VARCHAR(200),
        addr TEXT,
        location TEXT,
        use_time TEXT,
        lat DECIMAL(10, 8),
        lng DECIMAL(11, 8),
        total_chargers INTEGER DEFAULT 0,
        usable_chargers INTEGER DEFAULT 0,
        using_chargers INTEGER DEFAULT 0,
        charger_types TEXT[],
        max_output INTEGER DEFAULT 0,
        busi_id VARCHAR(50),
        bnm VARCHAR(200),
        busi_nm VARCHAR(200),
        busi_call VARCHAR(20),
        zcode VARCHAR(10),
        zscode VARCHAR(10),
        kind VARCHAR(50),
        kind_detail VARCHAR(100),
        parking_free VARCHAR(1),
        note TEXT,
        limit_yn VARCHAR(1),
        limit_detail TEXT,
        traffic_yn VARCHAR(1),
        last_update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    cursor.execute(create_chargers_table)
    cursor.execute(create_grouped_chargers_table)
    conn.commit()
    cursor.close()

def update_chargers(conn):
    """
    전체 충전소 리스트를 DB에 업데이트
    """
    logger.info('충전소 데이터 수집 시작...')
    
    create_tables_if_not_exists(conn)
    
    all_chargers = []
    for page in [1, 2]:
        chargers = get_ev_charger_info(page)
        if chargers:
            all_chargers.extend(chargers)
    
    if not all_chargers:
        logger.error("충전소 데이터를 가져오지 못했습니다.")
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM chargers")
        cursor.execute("DELETE FROM grouped_chargers")
        
        # 데이터 정제: 빈 문자열을 None으로 변환하고 숫자 변환
        logger.info(f"데이터 정제 중... {len(all_chargers)}개 레코드")
        for charger in all_chargers:
            # 숫자 필드들 처리
            numeric_fields = ['lat', 'lng', 'output']
            for field in numeric_fields:
                if field in charger:
                    value = charger[field]
                    if value == '' or value is None:
                        charger[field] = None
                    else:
                        # 문자열을 숫자로 변환 시도
                        try:
                            if field in ['lat', 'lng']:
                                # 위도/경도는 float로 변환
                                charger[field] = float(value)
                            elif field == 'output':
                                # 출력은 integer로 변환
                                charger[field] = int(float(value))  # float를 거쳐서 int로 (소수점 있을 수 있음)
                        except (ValueError, TypeError):
                            # 변환 실패 시 None으로 설정
                            logger.warning(f"숫자 변환 실패: {field}={value}")
                            charger[field] = None
                    
            # 기타 빈 문자열 필드들을 None으로 변환
            for key, value in charger.items():
                if value == '':
                    charger[key] = None
        
        insert_charger_query = """
        INSERT INTO chargers (
            stat_id, chger_id, stat_nm, addr, location, use_time, lat, lng,
            chger_type, stat, stat_upd_dt, last_tsdt, last_tedt, now_tsdt,
            output, method, del_yn, del_detail, busi_id, bnm, busi_nm,
            busi_call, zcode, zscode, kind, kind_detail, parking_free,
            note, limit_yn, limit_detail, traffic_yn
        ) VALUES (
            %(statId)s, %(chgerId)s, %(statNm)s, %(addr)s, %(location)s, %(useTime)s,
            %(lat)s, %(lng)s, %(chgerType)s, %(stat)s, %(statUpdDt)s, %(lastTsdt)s,
            %(lastTedt)s, %(nowTsdt)s, %(output)s, %(method)s, %(delYn)s, %(delDetail)s,
            %(busiId)s, %(bnm)s, %(busiNm)s, %(busiCall)s, %(zcode)s, %(zscode)s,
            %(kind)s, %(kindDetail)s, %(parkingFree)s, %(note)s, %(limitYn)s,
            %(limitDetail)s, %(trafficYn)s
        ) ON CONFLICT (stat_id, chger_id) DO UPDATE SET
            stat_nm = EXCLUDED.stat_nm,
            addr = EXCLUDED.addr,
            stat = EXCLUDED.stat,
            updated_at = CURRENT_TIMESTAMP
        """
        
        logger.info("데이터베이스에 충전소 데이터 삽입 중...")
        cursor.executemany(insert_charger_query, all_chargers)
        
        grouped_query = """
        INSERT INTO grouped_chargers (
            stat_id, stat_nm, addr, location, use_time, lat, lng,
            total_chargers, usable_chargers, using_chargers, charger_types, max_output,
            busi_id, bnm, busi_nm, busi_call, zcode, zscode, kind, kind_detail,
            parking_free, note, limit_yn, limit_detail, traffic_yn
        )
        SELECT 
            stat_id,
            MAX(stat_nm) as stat_nm,
            MAX(addr) as addr,
            MAX(location) as location,
            MAX(use_time) as use_time,
            MAX(lat) as lat,
            MAX(lng) as lng,
            COUNT(*) as total_chargers,
            SUM(CASE WHEN stat = '2' THEN 1 ELSE 0 END) as usable_chargers,
            SUM(CASE WHEN stat = '3' THEN 1 ELSE 0 END) as using_chargers,
            ARRAY_AGG(DISTINCT chger_type) as charger_types,
            MAX(CASE WHEN output IS NULL THEN 0 ELSE output END) as max_output,
            MAX(busi_id) as busi_id,
            MAX(bnm) as bnm,
            MAX(busi_nm) as busi_nm,
            MAX(busi_call) as busi_call,
            MAX(zcode) as zcode,
            MAX(zscode) as zscode,
            MAX(kind) as kind,
            MAX(kind_detail) as kind_detail,
            MAX(parking_free) as parking_free,
            MAX(note) as note,
            MAX(limit_yn) as limit_yn,
            MAX(limit_detail) as limit_detail,
            MAX(traffic_yn) as traffic_yn
        FROM chargers
        GROUP BY stat_id
        ON CONFLICT (stat_id) DO UPDATE SET
            total_chargers = EXCLUDED.total_chargers,
            usable_chargers = EXCLUDED.usable_chargers,
            using_chargers = EXCLUDED.using_chargers,
            last_update_time = CURRENT_TIMESTAMP
        """
        
        cursor.execute(grouped_query)
        
        cursor.execute("SELECT COUNT(*) FROM grouped_chargers")
        grouped_count = cursor.fetchone()[0]
        
        conn.commit()
        logger.info(f'성공적으로 {len(all_chargers)}개 충전소, {grouped_count}개 그룹 데이터 업데이트 완료!')
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f'데이터 업데이트 실패: {str(e)}')
        return False
    finally:
        cursor.close()

def test_network_connection():
    """
    네트워크 연결 상태 테스트 (구글로 핑)
    """
    try:
        logger.info("네트워크 연결 테스트 시작...")
        
        # urllib3로 구글에 간단한 요청
        http = urllib3.PoolManager()
        response = http.request('GET', 'https://www.google.com', timeout=10)
        
        if response.status == 200:
            logger.info("✅ 네트워크 연결 테스트 성공 - 구글 접속 가능")
            return True
        else:
            logger.warning(f"⚠️ 구글 응답 상태 코드: {response.status}")
            return False
            
    except urllib3.exceptions.HTTPError as e:
        logger.error(f"❌ 네트워크 연결 테스트 실패 (HTTP 오류): {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ 네트워크 연결 테스트 실패: {str(e)}")
        logger.error(f"오류 타입: {type(e).__name__}")
        return False

def lambda_handler(event, context):
    """
    Lambda 진입점
    """
    start_time = datetime.now()
    logger.info(f"Lambda 함수 시작 - RequestId: {context.aws_request_id}")
    
    try:
        # 환경변수 확인
        logger.info("환경변수 확인 중...")
        required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD', 'OPEN_API_SERVICE_KEY_DECODED']
        missing_vars = []
        
        for var in required_vars:
            value = os.environ.get(var)
            if not value:
                missing_vars.append(var)
            else:
                logger.info(f"환경변수 {var}: 설정됨 (길이: {len(value)})")
        
        if missing_vars:
            error_msg = f"다음 환경변수들이 설정되지 않았습니다: {', '.join(missing_vars)}"
            logger.error(error_msg)
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': error_msg,
                    'success': False,
                    'missing_vars': missing_vars
                }, ensure_ascii=False)
            }
        
        # 네트워크 연결 테스트
        logger.info("네트워크 연결 상태 확인 중...")
        network_ok = test_network_connection()
        if not network_ok:
            logger.warning("네트워크 연결에 문제가 있을 수 있습니다.")
        
        logger.info("PostgreSQL 연결 시도 중...")
        conn = connect_postgres()
        logger.info("PostgreSQL 연결 성공!")
        
        logger.info("충전소 데이터 업데이트 시작...")
        
        # API 호출 전 네트워크 재확인
        logger.info("공공데이터 API 호출 전 네트워크 재확인...")
        network_ok = test_network_connection()
        if not network_ok:
            logger.error("네트워크 연결 문제로 API 호출이 실패할 수 있습니다.")
        
        success = update_chargers(conn)
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if success:
            message = f'충전소 데이터 크롤링 성공! 실행 시간: {execution_time:.2f}초'
            logger.info(message)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': message,
                    'success': True,
                    'execution_time': execution_time,
                    'timestamp': end_time.isoformat()
                }, ensure_ascii=False)
            }
        else:
            message = f'충전소 데이터 크롤링 실패! 실행 시간: {execution_time:.2f}초'
            logger.error(message)
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': message,
                    'success': False,
                    'execution_time': execution_time,
                    'timestamp': end_time.isoformat()
                }, ensure_ascii=False)
            }
            
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        error_message = f'Lambda 실행 중 오류 발생: {str(e)}'
        logger.error(error_message)
        logger.error(f"오류 타입: {type(e).__name__}")
        logger.error(f"오류 상세: {repr(e)}")
        
        # 스택 트레이스 로깅
        import traceback
        logger.error(f"스택 트레이스: {traceback.format_exc()}")
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': error_message,
                'success': False,
                'execution_time': execution_time,
                'timestamp': end_time.isoformat(),
                'error': str(e),
                'error_type': type(e).__name__
            }, ensure_ascii=False)
        }
    
    finally:
        logger.info("Lambda 함수 정리 작업 시작...")
        try:
            if 'conn' in locals():
                conn.close()
                logger.info("PostgreSQL 연결 종료됨")
        except Exception as cleanup_error:
            logger.error(f"정리 작업 중 오류: {cleanup_error}")
        
        logger.info("Lambda 함수 종료")