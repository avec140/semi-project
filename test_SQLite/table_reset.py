import sqlite3

conn = sqlite3.connect("bcw_forum.db")
cur = conn.cursor()

# 테이블 내용 전체 삭제
cur.execute("DELETE FROM posts")
conn.commit()
conn.close()

print("🧹 기존 DB 내용 초기화 완료 (posts 테이블 비움)")
