from flask import Flask, render_template, request
from flask_socketio import SocketIO
import mysql.connector
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app)

# ✅ DB 연결 함수
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="bcw",
        port=3306
    )

@app.route("/")
def index():
    keyword = request.args.get("keyword")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 전체 게시물 모두 조회
    cursor.execute("SELECT * FROM posts")
    all_posts = cursor.fetchall()

    # 키워드 필터링
    if keyword:
        posts = [post for post in all_posts if keyword in (post["keywords"] or "")]
    else:
        posts = all_posts

    # 전체 기준 키워드 빈도수 계산
    keyword_counts = {}
    for post in all_posts:
        if post["keywords"]:
            for kw in post["keywords"].split(", "):
                keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    conn.close()
    return render_template("index.html", posts=posts, selected=keyword, keyword_counts=keyword_counts, total_count=len(all_posts))

# ✅ 실시간 알림용 DB 모니터링
latest_count = 0

def db_monitor():
    global latest_count
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM posts")
            count = cursor.fetchone()[0]
            conn.close()
            if count > latest_count:
                latest_count = count
                socketio.emit("new_data")
        except Exception as e:
            print("❌ 모니터링 오류:", e)
        time.sleep(5)

threading.Thread(target=db_monitor, daemon=True).start()

@app.route("/notify", methods=["POST"])
def notify():
    socketio.emit("new_data")  # 클라이언트에게 실시간 알림 전송
    return "", 200

if __name__ == "__main__":
    socketio.run(app, debug=True)