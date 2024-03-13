from flask import Flask

app = Flask(__name__)

# 예시 API: 전체 유저 목록 가져오기
@app.route('/users')
def users():
   return {"users" : ["user1", "user2", "user3"]}

if __name__ == '__main__':
   app.run('0.0.0.0', port=5000, debug=True)