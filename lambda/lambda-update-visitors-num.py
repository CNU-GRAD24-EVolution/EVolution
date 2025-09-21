import json
import os
import psycopg2
from datetime import datetime, timedelta
import logging

# Lambda에서 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

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

def parse_datetime(str_datetime):
    """
    YYYYMMDDHHMMSS 형식의 문자열을 datetime 객체로 변환
    """
    if not str_datetime or len(str_datetime) != 14:
        return None
    
    try:
        year = int(str_datetime[0:4])
        month = int(str_datetime[4:6])
        day = int(str_datetime[6:8])
        hour = int(str_datetime[8:10])
        minute = int(str_datetime[10:12])
        second = int(str_datetime[12:14])
        
        return datetime(year, month, day, hour, minute, second)
    except (ValueError, TypeError):
        return None

def create_history_tables_if_not_exists(conn):
    """
    방문자수 히스토리 테이블 생성
    """
    cursor = conn.cursor()
    
    # 충전기별 30분간격 방문자수 히스토리 테이블
    create_chargers_history_table = """
    CREATE TABLE IF NOT EXISTS history_chargers (
        id SERIAL PRIMARY KEY,
        stat_id VARCHAR(50) NOT NULL,
        chger_id VARCHAR(50) NOT NULL,
        visit_num INTEGER DEFAULT 0,
        cur_stat VARCHAR(2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (stat_id, chger_id, updated_at)
    );
    """
    
    # 충전소별 30분간격 방문자수 히스토리 테이블
    create_stations_history_table = """
    CREATE TABLE IF NOT EXISTS history_stations (
        id SERIAL PRIMARY KEY,
        stat_id VARCHAR(50),
        charger_count INTEGER DEFAULT 0,
        visit_num INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (stat_id, updated_at)
    );
    """
    
    # 인덱스 생성
    create_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_history_chargers_stat_chger ON history_chargers(stat_id, chger_id);",
        "CREATE INDEX IF NOT EXISTS idx_history_stations_stat ON history_stations(stat_id);"
    ]
    
    cursor.execute(create_chargers_history_table)
    cursor.execute(create_stations_history_table)
    
    for index_sql in create_indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    cursor.close()

def update_visit_num(conn):
    """
    각 충전소별 방문자수를 업데이트
    """
    logger.info("방문자수 업데이트 시작...")
    timestamp = datetime.now().replace(second=0, microsecond=0)  
    logger.info(f"현재 시각: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    create_history_tables_if_not_exists(conn)
    
    cursor = conn.cursor()
    
    try:
        # chargers 테이블에서 모든 충전기 데이터 가져오기
        cursor.execute("""
            SELECT stat_id, chger_id, stat, stat_upd_dt, last_tsdt, last_tedt, now_tsdt
            FROM chargers
            WHERE stat_id IS NOT NULL AND chger_id IS NOT NULL
        """)
        
        chargers_data = cursor.fetchall()
        logger.info(f"총 {len(chargers_data)}개 충전기 데이터 처리 중...")
        
        for charger in chargers_data:
            stat_id, chger_id, stat, stat_upd_dt, last_tsdt, last_tedt, now_tsdt = charger
            
            # 해당 충전기에 대해 이전에 수집된 데이터가 있는지 확인
            cursor.execute("""
                SELECT visit_num, cur_stat, updated_at
                FROM history_chargers
                WHERE stat_id = %s AND chger_id = %s
                ORDER BY updated_at DESC
                LIMIT 1
            """, (stat_id, chger_id))
            
            prev_data = cursor.fetchone()
            
            # 새로 추가할 방문자수
            visit_num = 0
            
            if prev_data is None:
                # 첫 번째 데이터인 경우
                visit_num = 1 if stat == '3' else 0
            else:
                prev_visit_num, prev_stat, prev_time = prev_data
                
                # 30분 전 충전기 상태와 현재 충전기 상태에 따라 visitNum 설정
                if prev_stat == '3' and stat == '3':
                    # 30분전과 현재 모두 충전중인 경우
                    # 30분 전과 현재 사이에 이전 사용자가 충전을 끝내고 새 사용자가 충전을 시작했는지 확인
                    time_30_min_ago = timestamp - timedelta(minutes=30)
                    
                    last_tsdt_time = parse_datetime(last_tsdt) if last_tsdt else None
                    last_tedt_time = parse_datetime(last_tedt) if last_tedt else None
                    now_tsdt_time = parse_datetime(now_tsdt) if now_tsdt else None
                    
                    # 충전 시작/종료 시간이 30분 사이에 있으면 새로운 방문자가 있었음
                    if ((last_tsdt_time and time_30_min_ago < last_tsdt_time < timestamp) or
                        (last_tedt_time and time_30_min_ago < last_tedt_time < timestamp) or
                        (now_tsdt_time and time_30_min_ago < now_tsdt_time < timestamp)):
                        visit_num = 2  # 이전 사용자 + 새 사용자
                    else:
                        visit_num = 1  # 계속 같은 사용자
                elif prev_stat != '3' and stat != '3':
                    # 30분전과 현재 모두 충전대기중인 경우
                    visit_num = 0
                else:
                    # 30분전과 현재 사이에 충전을 끝냈거나 충전을 시작한 경우
                    visit_num = 1
            
            # 충전기별 히스토리에 데이터 삽입/업데이트
            cursor.execute("""
                INSERT INTO history_chargers (stat_id, chger_id, visit_num, cur_stat, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (stat_id, chger_id, updated_at) DO UPDATE SET
                    visit_num = EXCLUDED.visit_num,
                    cur_stat = EXCLUDED.cur_stat,
                    updated_at = CURRENT_TIMESTAMP
            """, (stat_id, chger_id, visit_num, stat))
        
        # 같은 충전소끼리 그룹핑하여 충전소별 히스토리 생성 (현재 30분 간격 데이터만)
        cursor.execute("""
            INSERT INTO history_stations (stat_id, charger_count, visit_num, updated_at)
            SELECT 
                stat_id,
                COUNT(*) as charger_count,
                SUM(visit_num) as visit_num,
                CURRENT_TIMESTAMP
            FROM history_chargers
            WHERE updated_at >= CURRENT_TIMESTAMP - INTERVAL '1 minutes'
            GROUP BY stat_id
            ON CONFLICT (stat_id, updated_at) DO UPDATE SET
                charger_count = EXCLUDED.charger_count,
                visit_num = EXCLUDED.visit_num,
                updated_at = CURRENT_TIMESTAMP
        """)
        
        conn.commit()
        
        # 결과 확인
        cursor.execute("SELECT COUNT(*) FROM history_chargers")
        charger_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM history_stations")
        station_count = cursor.fetchone()[0]
        
        logger.info(f"방문자수 업데이트 완료!")
        logger.info(f"업데이트된 데이터: 충전기 {charger_count}개, 충전소 {station_count}개")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"방문자수 업데이트 실패: {str(e)}")
        return False
    finally:
        cursor.close()

def remove_history_over_30_days(conn):
    """
    30일 이전 히스토리 데이터 삭제 (updated_at 기준)
    """
    logger.info("30일 이전 히스토리 데이터 삭제 시작...")
    thirty_days_ago = datetime.now() - timedelta(days=30)
    logger.info(f"삭제 기준 날짜: {thirty_days_ago.strftime('%Y-%m-%d %H:%M:%S')} 이전 데이터")
    
    cursor = conn.cursor()
    
    try:
        # 충전기별 히스토리 삭제 (updated_at 기준)
        cursor.execute("DELETE FROM history_chargers WHERE updated_at < %s", (thirty_days_ago,))
        charger_deleted = cursor.rowcount
        
        # 충전소별 히스토리 삭제 (updated_at 기준)
        cursor.execute("DELETE FROM history_stations WHERE updated_at < %s", (thirty_days_ago,))
        station_deleted = cursor.rowcount
        
        conn.commit()
        logger.info(f"30일 이전 데이터 삭제 완료!")
        logger.info(f"삭제된 데이터: 충전기 히스토리 {charger_deleted}개, 충전소 히스토리 {station_deleted}개")
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"30일 이전 데이터 삭제 실패: {str(e)}")
        return False
    finally:
        cursor.close()

def lambda_handler(event, context):
    """
    Lambda 진입점
    """
    start_time = datetime.now()
    logger.info(f"Lambda 함수 시작 - RequestId: {context.aws_request_id}")
    logger.info(f"Lambda 실행 시각: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 환경변수 확인
        logger.info("환경변수 확인 중...")
        required_vars = ['POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
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
        
        # 이벤트에서 작업 타입 확인 (기본값: update_visit_num)
        task = event.get('task', 'update_visit_num')
        logger.info(f"실행할 작업: {task}")
        
        logger.info("PostgreSQL 연결 시도 중...")
        conn = connect_postgres()
        logger.info("PostgreSQL 연결 성공!")
        
        success = False
        message = ""
        
        if task == 'update_visit_num':
            logger.info("방문자수 업데이트 작업 시작...")
            success = update_visit_num(conn)
            message = '방문자수 업데이트'
        elif task == 'cleanup_old_data':
            logger.info("오래된 데이터 정리 작업 시작...")
            success = remove_history_over_30_days(conn)
            message = '30일 이전 데이터 정리'
        else:
            error_msg = f"알 수 없는 작업 타입: {task}"
            logger.error(error_msg)
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': error_msg,
                    'success': False,
                    'task': task
                }, ensure_ascii=False)
            }
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        if success:
            success_msg = f'{message} 성공! 실행 시간: {execution_time:.2f}초'
            logger.info(success_msg)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': success_msg,
                    'success': True,
                    'task': task,
                    'execution_time': execution_time,
                    'timestamp': end_time.isoformat()
                }, ensure_ascii=False)
            }
        else:
            error_msg = f'{message} 실패! 실행 시간: {execution_time:.2f}초'
            logger.error(error_msg)
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': error_msg,
                    'success': False,
                    'task': task,
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
