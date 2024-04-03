from pymongo import MongoClient
import os
import json
import requests
import schedule
import time
import traceback

def writeLog(log: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("Log.txt", "a") as f:
        f.write(f"[{current_time}] - {log}\n")

def chargerLog(str: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("fetched_charger_log.txt", "w") as f:
        f.write(f"[{current_time}] - {str}\n")
            
def getSecret(key):
    '''
    이름이 key인 비공개 key 리턴
    '''
    # 서비스키는 secrets.json에서 관리하고 .gitignore 처리
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    secret_file = os.path.join(BASE_DIR, 'crawling/secrets.json')
    with open(secret_file) as f:
        secrets = json.loads(f.read())

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
    client = MongoClient('mongodb://minsuhan:minsuhan@localhost/?authSource=admin', 27017)
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
    # 디코딩된 serviceKey
    serviceKey_decoded = getSecret('serviceKeyDecoded')

    # TODO: 전체 충전소 검색 시 상세조건 협의 필요
    params = {
        'serviceKey': serviceKey_decoded,
        'pageNo': '1', 'numOfRows': '9999', 'zcode': '30', 'dataType': 'JSON',
    }

    # fetch 후 충전소 리스트만 추출하여 리턴
    try:
        response = requests.get(url=base_url, params=params, timeout=30)
        # HTTP 에러가 발생하면 예외 발생
        response.raise_for_status()  
        # 정상적으로 결과를 받은 경우
        if (response.status_code == 200 and ('<errMsg>' not in response.text)):
            # 가져온 리스트 로그 쓰기 (임시 에러확인용)
            chargerLog(response.text)
            response = response.json()
            return response['items']['item']
        else:
            return False
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
    if chargers is not False:
        # 컬렉션 기존 문서 제거
        collection.delete_many({})
        # 컬렉션에 추가
        collection.insert_many(chargers)
        # grouped-chargers 컬렉션 reset
        db['grouped-chargers'].delete_many({})
        # 충전소ID가 같은 것끼리 grouping
        collection.aggregate(
            [
                {
                    '$group': {
                        '_id': '$statId',
                        'chargers': { '$push': '$$ROOT' },
                        'totalChargers': { '$sum': 1 }
                    }
                },
                {
                    '$addFields': {
                        'timestamp': { '$toDate': '$$NOW' }
                    }
                },
                {
                    '$out': "grouped-chargers"
                }
            ],
        )

        writeLog('Successfully Fetched and updated!')
    else:
        writeLog('공공데이터 서버 응답 문제가 발생하여 크롤링을 1회 skip합니다...')



if __name__ == "__main__":
    try:
        db = connectDB()
        # schedule 라이브러리를 이용하여 일정 주기마다 job 함수 실행
        schedule.every(2).minutes.do(updateChargers, db)

        # 무한 루프를 돌면서 스케줄을 체크 (필수 코드)
        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception:
        err = traceback.format_exc()
        writeLog(str('[main process Error] ' + err))
        # 혹시나 프로그램 자체가 뻗는경우 shell에 재실행 명령
        os.system("nohup python crawling.py &") 
