from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# PostgreSQL 연결 정보 (환경변수 사용)
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': os.getenv('POSTGRES_PORT')
}

# 디버깅: 환경변수 확인
print("=== 환경변수 디버깅 ===")
print(f"POSTGRES_HOST: {os.getenv('POSTGRES_HOST')}")
print(f"POSTGRES_DB: {os.getenv('POSTGRES_DB')}")
print(f"POSTGRES_USER: {os.getenv('POSTGRES_USER')}")
print(f"POSTGRES_PASSWORD: {'***' if os.getenv('POSTGRES_PASSWORD') else 'None'}")
print(f"POSTGRES_PORT: {os.getenv('POSTGRES_PORT')}")
print("======================")

def get_db_connection():
    """PostgreSQL 데이터베이스 연결"""
    try:
        print(f"데이터베이스 연결 시도 중: {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("✓ 데이터베이스 연결 성공!")
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print(f"연결 정보: {POSTGRES_CONFIG}")
        return None
    
def execute_query(query, params=None, fetch=True):
    """쿼리 실행 유틸리티 함수"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return cursor.rowcount
            else:
                conn.commit()
                return cursor.rowcount
    except Exception as e:
        print(f"Query execution error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def convert_charger_to_camel_case(charger):
    """충전기 데이터의 키를 snake_case에서 camelCase로 변환"""
    camel_case_mapping = {
        'chger_id': 'chgerId',
        'chger_type': 'chgerType',
        'stat_upd_dt': 'statUpdDt',
        'last_tsdt': 'lastTsdt',
        'last_tedt': 'lastTedt',
        'now_tsdt': 'nowTsdt',
        'del_yn': 'delYn',
        'del_detail': 'delDetail',
        'busi_id': 'busiId',
        'busi_nm': 'busiNm',
        'busi_call': 'busiCall',
        'kind_detail': 'kindDetail',
        'limit_yn': 'limitYn',
        'limit_detail': 'limitDetail',
        'parking_free': 'parkingFree',
        'traffic_yn': 'trafficYn',
        'use_time': 'useTime',
        'stat_id': 'statId',
        'stat_nm': 'statNm',
        'created_at': 'createdAt',
        'updated_at': 'updatedAt'
    }
    
    converted = {}
    for key, value in charger.items():
        # 매핑에 있는 키면 camelCase로 변환, 없으면 그대로 사용
        new_key = camel_case_mapping.get(key, key)
        converted[new_key] = value
    
    return converted

def create_tables_if_not_exists():
    """필요한 테이블들이 없으면 생성"""
    create_demand_info_table = """
    CREATE TABLE IF NOT EXISTS demand_info (
        id SERIAL PRIMARY KEY,
        stat_id VARCHAR(50) UNIQUE NOT NULL,
        view_num INTEGER DEFAULT 0,
        departs_in_30m TIMESTAMP[],
        hourly_visit_num INTEGER[],
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # 기존 테이블에 컬럼 추가 (이미 존재하면 무시됨)
    add_columns_queries = [
        "ALTER TABLE demand_info ADD COLUMN IF NOT EXISTS departs_in_30m TIMESTAMP[];",
        "ALTER TABLE demand_info ADD COLUMN IF NOT EXISTS hourly_visit_num INTEGER[];"
    ]
    
    try:
        execute_query(create_demand_info_table, fetch=False)
        print("demand_info 테이블 확인/생성 완료")
        
        for query in add_columns_queries:
            execute_query(query, fetch=False)
        print("demand_info 테이블 컬럼 추가 완료")
        
    except Exception as e:
        print(f"테이블 생성 오류: {e}")

# Pydantic 모델 정의
class DepartTimeRequest(BaseModel):
    depart_time: str

######### FastAPI app 설정 #########

app = FastAPI(title="Simple Test API")

# CORS 설정 - 개발 및 프로덕션 환경
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000", 
        "http://localhost:3001", 
        "http://127.0.0.1:3001",
        "https://daejeon-evolution.com",
        "https://www.daejeon-evolution.com",
        "https://api.daejeon-evolution.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# FastAPI 시작 이벤트에서 테이블 생성 실행
@app.on_event("startup")
async def startup():
    try:
        create_tables_if_not_exists()
        print("테이블 생성/확인 완료")
    except Exception as e:
        print(f"테이블 생성 중 오류 (무시하고 계속): {e}")

# 루트 엔드포인트
@app.get("/")
async def root():
    return {"message": "FastAPI 충전소 API 서버가 정상적으로 실행 중입니다!"}

# 주변 충전소 목록 가져오기 (대전시 전체)
@app.get('/api/stations')
async def nearby_stations(
    chargerTypes: Optional[str] = Query(None),
    minOutput: Optional[int] = Query(None),
    parkingFree: Optional[str] = Query(None)
):
    try:
        # 현재 시간 기준으로 30분 전의 시간 계산
        thirty_min_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        
        # 필터 쿼리 처리
        where_conditions = []
        params = []
        
        # 충전기 타입 필터링
        if chargerTypes:
            request_types = chargerTypes.split(',')
            target_types = []
            
            for type_code in request_types:
                if type_code == '01':  # DC차데모
                    target_types.extend(['01', '03', '05', '06'])
                elif type_code == '02':  # AC완속
                    target_types.extend(['02'])
                elif type_code == '04':  # DC콤보
                    target_types.extend(['04', '05', '06', '08'])
                elif type_code == '07':  # AC3상
                    target_types.extend(['03', '06', '07'])
            
            if target_types:
                # PostgreSQL text[] 배열에서 타입 검색
                type_conditions = []
                for target_type in target_types:
                    type_conditions.append("%s = ANY(charger_types)")
                    params.append(target_type)
                
                where_conditions.append(f"({' OR '.join(type_conditions)})")
        
        # 최소속도 필터링
        if minOutput:
            where_conditions.append("CAST(max_output AS INTEGER) >= %s")
            params.append(minOutput)
        
        # 무료주차여부 필터링
        if parkingFree:
            where_conditions.append("parking_free = %s")
            params.append(parkingFree)
        
        # WHERE 절 구성
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 주변 충전소 목록 가져오기 (수요예측 정보 포함)
        query = f"""
            SELECT 
                gc.stat_id,
                gc.stat_nm,
                CAST(gc.lat AS VARCHAR) as lat,
                CAST(gc.lng AS VARCHAR) as lng,
                gc.charger_types,
                gc.parking_free,
                gc.total_chargers,
                gc.usable_chargers,
                gc.using_chargers,
                CAST(gc.max_output AS VARCHAR) as max_output,
                gc.use_time,
                gc.last_update_time,
                COALESCE(di.view_num, 0) as view_num,
                COALESCE(di.departs_in_30m, ARRAY[]::TIMESTAMP[]) as departs_in_30m,
                COALESCE(di.hourly_visit_num, ARRAY[]::INTEGER[]) as hourly_visit_num
            FROM grouped_chargers gc
            LEFT JOIN demand_info di ON gc.stat_id = di.stat_id
            {where_clause}
            ORDER BY gc.stat_nm
        """
        
        stations = execute_query(query, params)
        if stations is None:
            raise HTTPException(status_code=500, detail="Database query failed")
        
        # 응답 형식을 프론트엔드 타입에 맞게 변환
        formatted_stations = []
        for station in stations:
            # 30분 내 출발 데이터에서 오래된 것 필터링
            departs_list = []
            if station['departs_in_30m']:
                current_time = datetime.now(timezone.utc)
                thirty_min_ago = current_time - timedelta(minutes=30)
                
                # timezone naive datetime을 timezone aware로 변환하여 비교
                departs_list = []
                for dep in station['departs_in_30m']:
                    # dep가 timezone naive인 경우 UTC로 간주하여 timezone aware로 변환
                    if dep.tzinfo is None:
                        dep_aware = dep.replace(tzinfo=timezone.utc)
                    else:
                        dep_aware = dep
                    
                    if dep_aware >= thirty_min_ago:
                        departs_list.append(dep_aware.isoformat())
            
            formatted_station = {
                "statId": station['stat_id'],
                "info": {
                    "statNm": station['stat_nm'],
                    "lat": station['lat'],
                    "lng": station['lng'],
                    "chargerTypes": station['charger_types'] if station['charger_types'] else [],
                    "parkingFree": station['parking_free'],
                    "totalChargers": station['total_chargers'],
                    "usableChargers": station['usable_chargers'],
                    "usingChargers": station['using_chargers'],
                    "maxOutput": station['max_output'],
                    "useTime": station['use_time']
                },
                "lastUpdateTime": station['last_update_time'].isoformat() if station['last_update_time'] else None,
                "demandInfo": {
                    "viewNum": station['view_num'],
                    "departsIn30m": departs_list,
                    "hourlyVisitNum": station['hourly_visit_num'] if station['hourly_visit_num'] else []
                } 
            }
            formatted_stations.append(formatted_station)
        
        return formatted_stations
        
    except Exception as e:
        print(f"Error in nearby_stations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 특정 충전소의 정보
@app.get('/api/stations/{stat_id}')
async def station_info(stat_id: str, brief: Optional[str] = Query(None)):
    try:
        if brief == 'no':
            # 상세정보 요청 - 모든 필드 포함
            query = """
                SELECT 
                    gc.stat_id, gc.stat_nm, gc.lat, gc.lng, gc.charger_types, gc.parking_free,
                    gc.total_chargers, gc.usable_chargers, gc.using_chargers, gc.max_output, gc.use_time,
                    gc.addr, gc.location, gc.busi_id, gc.bnm, gc.busi_nm, gc.busi_call, 
                    gc.zcode, gc.zscode, gc.kind, gc.kind_detail, gc.note, gc.limit_yn, 
                    gc.limit_detail, gc.traffic_yn, gc.last_update_time,
                    COALESCE(di.view_num, 0) as view_num,
                    COALESCE(di.departs_in_30m, ARRAY[]::TIMESTAMP[]) as departs_in_30m,
                    COALESCE(di.hourly_visit_num, ARRAY[]::INTEGER[]) as hourly_visit_num
                FROM grouped_chargers gc
                LEFT JOIN demand_info di ON gc.stat_id = di.stat_id
                WHERE gc.stat_id = %s
            """
            
            result = execute_query(query, (stat_id,))
            if not result:
                raise HTTPException(status_code=404, detail="Station not found")
            
            station = result[0]
            
            # 개별 충전기 정보 가져오기
            chargers_query = """
                SELECT * FROM chargers 
                WHERE stat_id = %s 
                ORDER BY chger_id
            """
            chargers = execute_query(chargers_query, (stat_id,))
            
            # 30분 내 출발 데이터에서 오래된 것 필터링
            departs_list = []
            if station['departs_in_30m']:
                current_time = datetime.now(timezone.utc)
                thirty_min_ago = current_time - timedelta(minutes=30)
                
                for dep in station['departs_in_30m']:
                    # dep가 timezone naive인 경우 UTC로 간주하여 timezone aware로 변환
                    if dep.tzinfo is None:
                        dep_aware = dep.replace(tzinfo=timezone.utc)
                    else:
                        dep_aware = dep
                    
                    if dep_aware >= thirty_min_ago:
                        departs_list.append(dep_aware.isoformat())
            
            # 응답 형식 구성 - StationDetailed 타입에 맞춤
            response = {
                "statId": station['stat_id'],
                "info": {
                    "totalChargers": station['total_chargers'],
                    "usableChargers": station['usable_chargers'],
                    "usingChargers": station['using_chargers'],
                    "chargerTypes": station['charger_types'] if station['charger_types'] else [],
                    "maxOutput": str(station['max_output']) if station['max_output'] else "0",
                    "statNm": station['stat_nm'],
                    "addr": station.get('addr', ''),
                    "location": station.get('location', ''),
                    "useTime": station['use_time'],
                    "lat": str(station['lat']) if station['lat'] else "0",
                    "lng": str(station['lng']) if station['lng'] else "0",
                    "busiId": station.get('busi_id', ''),
                    "bnm": station.get('bnm', ''),
                    "busiNm": station.get('busi_nm', ''),
                    "busiCall": station.get('busi_call', ''),
                    "zcode": station.get('zcode', ''),
                    "zscode": station.get('zscode', ''),
                    "kind": station.get('kind', ''),
                    "kindDetail": station.get('kind_detail', ''),
                    "parkingFree": station['parking_free'],
                    "note": station.get('note', ''),
                    "limitYn": station.get('limit_yn', ''),
                    "limitDetail": station.get('limit_detail', ''),
                    "trafficYn": station.get('traffic_yn', '')
                },
                "chargers": [convert_charger_to_camel_case(dict(charger)) for charger in chargers] if chargers else [],
                "lastUpdateTime": station['last_update_time'].isoformat() if station['last_update_time'] else None,
                "demandInfo": {
                    "viewNum": station['view_num'],
                    "departsIn30m": departs_list,
                    "hourlyVisitNum": station['hourly_visit_num'] if station['hourly_visit_num'] else []
                } 
            }
            
        else:
            # 간략정보 요청
            query = """
                SELECT 
                    gc.stat_id, gc.stat_nm, gc.lat, gc.lng, gc.charger_types, gc.parking_free,
                    gc.total_chargers, gc.usable_chargers, gc.using_chargers, 
                    gc.max_output, gc.use_time, gc.last_update_time,
                    COALESCE(di.view_num, 0) as view_num,
                    COALESCE(di.departs_in_30m, ARRAY[]::TIMESTAMP[]) as departs_in_30m,
                    COALESCE(di.hourly_visit_num, ARRAY[]::INTEGER[]) as hourly_visit_num
                FROM grouped_chargers gc
                LEFT JOIN demand_info di ON gc.stat_id = di.stat_id
                WHERE gc.stat_id = %s
            """
            
            result = execute_query(query, (stat_id,))
            if not result:
                raise HTTPException(status_code=404, detail="Station not found")
            
            station = result[0]
            
            # 30분 내 출발 데이터에서 오래된 것 필터링
            departs_list = []
            if station['departs_in_30m']:
                current_time = datetime.now(timezone.utc)
                thirty_min_ago = current_time - timedelta(minutes=30)
                
                for dep in station['departs_in_30m']:
                    # dep가 timezone naive인 경우 UTC로 간주하여 timezone aware로 변환
                    if dep.tzinfo is None:
                        dep_aware = dep.replace(tzinfo=timezone.utc)
                    else:
                        dep_aware = dep
                    
                    if dep_aware >= thirty_min_ago:
                        departs_list.append(dep_aware.isoformat())
            
            response = {
                "statId": station['stat_id'],
                "info": {
                    "statNm": station['stat_nm'],
                    "lat": str(station['lat']) if station['lat'] else "0",
                    "lng": str(station['lng']) if station['lng'] else "0",
                    "chargerTypes": station['charger_types'] if station['charger_types'] else [],
                    "parkingFree": station['parking_free'],
                    "totalChargers": station['total_chargers'],
                    "usableChargers": station['usable_chargers'],
                    "usingChargers": station['using_chargers'],
                    "maxOutput": str(station['max_output']) if station['max_output'] else "0",
                    "useTime": station['use_time']
                },
                "lastUpdateTime": station['last_update_time'].isoformat() if station['last_update_time'] else None,
                "demandInfo": {
                    "viewNum": station['view_num'],
                    "departsIn30m": departs_list,
                    "hourlyVisitNum": station['hourly_visit_num'] if station['hourly_visit_num'] else []
                } if station['view_num'] >= 0 or departs_list or station['hourly_visit_num'] else None
            }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in station_info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 특정 충전소 상세정보 조회수 +1
@app.put('/api/stations/{stat_id}/view-num/up')
async def increase_view_num(stat_id: str):
    try:
        # 조회수 증가 (UPSERT 방식)
        query = """
            INSERT INTO demand_info (stat_id, view_num)
            VALUES (%s, 1)
            ON CONFLICT (stat_id)
            DO UPDATE SET view_num = demand_info.view_num + 1
        """
        
        result = execute_query(query, (stat_id,), fetch=False)
        
        if result is not None and result >= 0:
            return {"message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Station not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in increase_view_num: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 특정 충전소 상세정보 조회수 -1
@app.put('/api/stations/{stat_id}/view-num/down')
async def decrease_view_num(stat_id: str):
    try:
        # 조회수 감소 (0 이하로는 내려가지 않도록)
        query = """
            UPDATE demand_info 
            SET view_num = GREATEST(view_num - 1, 0)
            WHERE stat_id = %s
        """
        
        result = execute_query(query, (stat_id,), fetch=False)
        
        if result is not None and result > 0:
            return {"message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Station not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in decrease_view_num: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 30분내 출발 데이터 추가
@app.post("/api/stations/{stat_id}/departs")
async def add_depart_time(stat_id: str, request: DepartTimeRequest):
    try:
        # 전달받은 출발일시
        depart_time_str = request.depart_time
        if not depart_time_str:
            raise HTTPException(status_code=400, detail="depart_time is required")
        
        depart_time = datetime.fromisoformat(depart_time_str.replace('Z', '+00:00'))
        
        # 기존 출발 시간 배열에 새로운 시간 추가
        query = """
            INSERT INTO demand_info (stat_id, view_num, departs_in_30m)
            VALUES (%s, 0, ARRAY[%s])
            ON CONFLICT (stat_id)
            DO UPDATE SET 
                departs_in_30m = array_append(COALESCE(demand_info.departs_in_30m, ARRAY[]::TIMESTAMP[]), %s),
                updated_at = CURRENT_TIMESTAMP
        """
        
        result = execute_query(query, (stat_id, depart_time, depart_time), fetch=False)
        
        if result is not None and result >= 0:
            return {"message": "success"}
        else:
            raise HTTPException(status_code=404, detail="Station not found")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in add_depart_time: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 헬스체크 엔드포인트
@app.get('/api/health')
async def health_check():
    """API 서버와 데이터베이스 연결 상태 확인"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return {
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'unhealthy',
                'database': 'disconnected',
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

