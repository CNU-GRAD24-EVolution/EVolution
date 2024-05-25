from pymongo import MongoClient, UpdateOne
import os
import json
import schedule
import time
import traceback
from datetime import datetime, timedelta

def writeErrorLog(log: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("Error-log-update-visitors-num.txt", "a") as f:
        f.write(f"[{current_time}] - {log}\n")

def writeLog(log: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("Log-update-visitors-num.txt", "a") as f:
        f.write(f"[{current_time}] - {log}\n")
            
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
    # client = MongoClient(getSecret('mongoDBConnectionString'))
    # crawling 데이터베이스에 접근
    db = client['crawling']
    return db


def parseDateTime(str):
    year = int(str[0:4])
    month = int(str[4:6])
    day = int(str[6:8])
    hour = int(str[8:10])
    minute = int(str[10:12])
    second = int(str[12:14])

    # datetime 객체 생성
    return datetime(year, month, day, hour, minute, second)

# 각 충전소별 30분간격 방문자수 history를 수집
# 먼저 각 충전기별로 수집한 다음, 같은 충전소끼리 그룹핑
def updateVisitNum(db):
    writeLog("Start: " + time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time())))
    timestamp = datetime.now().replace(second=0, microsecond=0)         # 방문자수 수집시각 (:00분 또는 :30분 정각)
    collection_chargers = db['chargers']                # 충전소별 충전기 상태 Collection
    collection_chargers_visitNum = db['history-chargers']      # 충전기별 30분간격 방문자수 Collection
    collection_chargers_visitNum.create_index([("statId", 1), ("chgerId", 1)])

    
    chargers_data = collection_chargers.find()                          # 충전기 상태 데이터
    # prev_visitNum_data = collection_chargers_visitNum.find()            # 충전기별 30분간격 방문자수 데이터

    updates = []

    # 각 충전기의 30분간격 방문자수 update
    for charger in chargers_data:
        # 해당 충전기에 대해 이전에 수집된 데이터가 없는 경우
        if collection_chargers_visitNum.count_documents({ "statId": charger['statId'], "chgerId": charger['chgerId']}) == 0:
            # 해당 충전기에 대한 첫 방문자수 데이터를 추가
            collection_chargers_visitNum.insert_one({ 
                "statId": charger['statId'],
                "chgerId": charger['chgerId'],
                "history": [
                    {
                        "time": timestamp,
                        # 충전중이면 1명, 그 외 0명
                        "visitNum": 1 if charger['stat'] == '3' else 0,
                        "curStat": charger['stat']
                    }
                ]
            })
        # 해당 충전기에 대해 이전에 수집된 데이터가 있는 경우
        else:
            # 가장 마지막(30분 전)에 수집된 데이터
            prevData = collection_chargers_visitNum.find(
                { "statId": charger['statId'], "chgerId": charger['chgerId']}, 
                { 'history': { '$slice': -1 } }
            )
            for document in prevData:
                if 'history' in document:
                    history = document['history']
                    if len(history) > 0:
                        # curStat(충전기 상태) 확인
                        prevStat = history[0]['curStat']
                        # 새로 추가할 데이터 생성
                        newElement = {
                            "time": timestamp,
                            "curStat": charger['stat']
                        }

                        # [30분 전 충전기 상태와 현재 충전기 상태에 따라 visitNum 설정]
                        # 30분전과 현재 모두 충전중으로 표시되는 경우
                        if prevStat == '3' and charger['stat'] == '3':
                            # 30분전과 현재 사이에 이전 사용자가 충전을 끝내고 새 사용자가 충전을 시작한 경우
                            if (len(charger['lastTsdt']) == 14 
                                and (parseDateTime(charger['lastTsdt']) > timestamp - timedelta(minutes=30) and parseDateTime(charger['lastTsdt']) < timestamp)) or (len(charger['lastTedt']) == 14 
                                and (parseDateTime(charger['lastTedt']) > timestamp - timedelta(minutes=30) and parseDateTime(charger['lastTedt']) < timestamp)) or (len(charger['nowTsdt']) == 14 
                                and (parseDateTime(charger['nowTsdt']) > timestamp - timedelta(minutes=30) and parseDateTime(charger['nowTsdt']) < timestamp)):
                                newElement['visitNum'] = 2
                            # 30분전에 충전중이던 사람이 계속 충전중인 경우
                            else:
                                newElement['visitNum'] = 1
                        # 30분전과 현재 모두 충전대기중인 경우
                        elif prevStat != '3' and charger['stat'] != '3':
                            newElement['visitNum'] = 0
                        # 30분전과 현재 사이에 충전을 끝냈거나 충전을 시작한 경우
                        else:
                            newElement['visitNum'] = 1

                        # 업데이트 리스트에 추가
                        updates.append(
                            UpdateOne(
                                { "statId": charger['statId'], "chgerId": charger['chgerId']},
                                { "$push": {'history': newElement}}
                            )
                        )

    # 배치 업데이트 실행
    if updates:
        collection_chargers_visitNum.bulk_write(updates)    

    # 같은 충전소끼리 그룹핑
    # 결과물은 각 충전소의 30분간격 방문자수 history
    collection_chargers_visitNum.aggregate(
        [
            {
                '$unwind': {
                    'path': "$history",
                },
            },
            {
                '$group': {
                    '_id': "$statId",
                    'chargers': {
                        '$push': "$$ROOT.history",
                    },
                },
            },
            # 파이프라인 결과: 특정 충전소의 모든 충전기들의 히스토리
            {
                '$unwind': {
                    'path': "$chargers",
                },
            },
            {
                '$group': {
                    '_id': {
                        '_id': "$_id",
                        'time': "$chargers.time",
                    },
                    'count': {
                        '$sum': 1,
                    },
                    'visitNum': {
                        '$sum': "$chargers.visitNum",
                    },
                },
            },
            {
                '$project': {
                    '_id': "$_id._id",
                    'time': "$_id.time",
                    'count': 1,
                    'visitNum': 1,
                },
            },
            # 파이프라인 결과: 특정 시간에 집계한 30분 내 충전소의 모든 충전기 사용자수 합을 표시 
            {
                '$group': {
                    '_id': "$_id",
                    'history': {
                        '$push': {
                            'time': "$$ROOT.time",
                            'count': "$$ROOT.count",
                            'visitNum': "$$ROOT.visitNum",
                        },
                    },
                },
            },
            # 파이프라인 결과: { id: '충전소id', history: [집계시각별 방문자수] }
            {
                '$set': {
                    'history': {
                        '$sortArray': {
                            'input': "$history",
                            'sortBy': { 'time': 1 }
                        }
                    }
                }
            },
            # 파이프라인 결과: { id: '충전소id', history: [집계시각별 방문자수(오름차순)] }
            {
                '$out': "history-stations",    # 결과 저장
            },
        ]
    )

    writeLog("End: " + time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time())))         

# 매일 00시 20분에 30일 전 데이터를 삭제
def removeHistoryOver30Days(db):
    thirty_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=30)         # 30일 전 자정
    collection_chargers_visitNum = db['history-chargers']      # 충전기별 30분간격 방문자수 Collection
    collection_stations_visitNum = db['history-stations']      # 충전소별 30분간격 방문자수 Collection

    collection_chargers_visitNum.update_many(
        {},
        { "$pull": { "history": { "time": { "$lt": thirty_days_ago } } } }
    )

    time.sleep(5 / 1000)

    collection_stations_visitNum.update_many(
        {},
        { "$pull": { "history": { "time": { "$lt": thirty_days_ago } } } }
    )


if __name__ == "__main__":
    try:
        db = connectDB()
        # schedule 라이브러리를 이용하여 매시 정각, 30분마다 방문객수 수집 함수 실행
        schedule.every().hour.at(":00").do(updateVisitNum, db)
        schedule.every().hour.at(":30").do(updateVisitNum, db)

        # 매일 00시 20분에 30일 이전 히스토리 삭제
        schedule.every().day.at("00:20").do(removeHistoryOver30Days, db)

        # 무한 루프를 돌면서 스케줄을 체크 (필수 코드)
        while True:
            schedule.run_pending()
            time.sleep(1)

    except Exception:
        err = traceback.format_exc()
        print(err)
        writeErrorLog(str('[main process Error] ' + err))
        # 혹시나 프로그램 자체가 뻗는경우 shell에 재실행 명령
        os.system("nohup python update-visitors-num.py &") 
