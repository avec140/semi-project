# table_reset.py
import mysql.connector

config = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "bcw",
    "port": 3306
}

try:
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("DELETE FROM posts")
    conn.commit()
    cur.close()
    conn.close()
    print("🧹 posts 테이블 초기화 완료")
except Exception as e:
    print("❌ 초기화 실패:", e)
