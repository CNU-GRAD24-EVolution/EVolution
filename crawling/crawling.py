from pymongo import MongoClient
import os
import json
import requests
import schedule
import time

def getSecret(key, secrets):
    '''
    이름이 key인 비공개 key 리턴
    '''
    try:
        return secrets[key]
    except KeyError:
        error_msg = "Set the {} environment variable".format(key)
        raise Exception(error_msg)
    
def connectDB():
    '''
    crawling DB 연결
    '''
    # mongoDB 서버에 연결
    client = MongoClient('mongodb://minsuhan:minsuhan@13.125.236.143', 27017)
    # crawling 데이터베이스에 접근
    db = client['crawling']
    return db

def getEvChargerInfo():
    '''
    공공데이터 API에 전체 전기차 충전소 리스트 요청
    '''

    # 전기차 충전소 정보 요청 base URL
    base_url = 'http://apis.data.go.kr/B552584/EvCharger/getChargerInfo'

    # requests.get() 함수가 parameter를 인코딩해주기 때문에 디코딩된 키를 전달해야함
    # TODO: 서비스키는 secrets.json에서 관리하고 .gitignore 처리
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secret_file = os.path.join(BASE_DIR, 'crawling/secrets.json')
    with open(secret_file) as f:
        secrets = json.loads(f.read())
    
    # 디코딩된 serviceKey
    serviceKey_decoded = getSecret('serviceKeyDecoded', secrets=secrets)

    # TODO: 전체 충전소 검색 시 상세조건 협의 필요
    params = {
        'serviceKey': serviceKey_decoded,
        'pageNo': '1', 'numOfRows': '10', 'zcode': '30', 'dataType': 'JSON',
    }

    # fetch 후 충전소 리스트만 추출하여 리턴
    try:
        response = requests.get(url=base_url, params=params, timeout=30)
        # HTTP 에러가 발생하면 예외 발생
        response.raise_for_status()  
        # 정상적으로 결과를 받은 경우
        if (response.status_code == 200):
            response = response.json()
            return response['items']['item']
        else:
            raise Exception('HTTP Error: ' + response.status_code)
    except requests.exceptions.RequestException as e:
        return f"Error fetching charger info: {e}"
    except Exception as e:
        return f"{e}"

def updateChargers(db):
    '''
    전체 충전소 리스트를 chargers 컬렉션에 업데이트
    '''
    ### Schedule log
    print('Fetching chargers data...')

    collection = db['chargers']
    # 공공데이터로부터 충전소 리스트 가져오기
    chargers = getEvChargerInfo()
    # 컬렉션 기존 문서 제거
    collection.delete_many({})
    # 컬렉션에 추가
    print(len(chargers))
    collection.insert_many(chargers)
    # 추가된 시간 timestamp 추가
    collection.update_many({}, [{"$set": { "timestamp": {"$toDate":"$_id"}}}])
    print('Successfully Fetched and updated!')



if __name__ == "__main__":
    db = connectDB()
     # schedule 라이브러리를 이용하여 일정 주기마다 job 함수 실행
    schedule.every(5).minutes.do(updateChargers, db)

    # 무한 루프를 돌면서 스케줄을 체크 (필수 코드)
    while True:
      schedule.run_pending()
      time.sleep(1)