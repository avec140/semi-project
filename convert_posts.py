# convert_posts.py
import mysql.connector
import re
from datetime import datetime

# ✅ DB 설정
config = {
    "host": "localhost",
    "user": "root",
    "password": "1234",
    "database": "bcw",
    "port": 3306,
}

# ✅ 이메일 추출 정규식
email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# ✅ 날짜 문자열 파싱 함수
def try_parse_date(date_str):
    try:
        return datetime.strptime(date_str.strip(), "%a %b %d, %Y %I:%M %p")
    except Exception as e:
        print(f"[!] 날짜 파싱 오류: {e} -> 원본: {date_str}")
        return None

# ✅ DB 연결
conn = mysql.connector.connect(**config)
cur = conn.cursor(dictionary=True)

# ✅ posts 테이블에서 데이터 가져오기
cur.execute("SELECT * FROM posts")
posts = cur.fetchall()

# ✅ 테이블 자동 생성
cur.execute("""
CREATE TABLE IF NOT EXISTS parsed_posts (
    id INT PRIMARY KEY,
    title VARCHAR(255),
    author VARCHAR(255),
    post_date DATETIME,
    keywords TEXT,
    raw_body LONGTEXT,
    created_at DATETIME
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS parsed_emails (
    email VARCHAR(255) PRIMARY KEY
)
""")

parsed_emails_set = set()

# ✅ 데이터 변환 및 삽입
for post in posts:
    post_id = post["id"]
    title = post["title"]
    author = post["author"]
    date_str = post.get("date")
    post_date = try_parse_date(date_str)
    if not post_date:
        print(f"⚠️ 날짜 파싱 실패: '{date_str}' → NULL 저장됨")

    keywords = post["keywords"]
    raw_body = post["full_text"]
    created_at = post["created_at"]

    # 이메일 추출
    if raw_body:
        found_emails = re.findall(email_regex, raw_body)
        for email in found_emails:
            parsed_emails_set.add(email.lower())

    # parsed_posts 삽입
    cur.execute("""
        INSERT INTO parsed_posts (id, title, author, post_date, keywords, raw_body, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            keywords = VALUES(keywords),
            raw_body = VALUES(raw_body),
            created_at = VALUES(created_at)
    """, (post_id, title, author, post_date, keywords, raw_body, created_at))

# ✅ parsed_emails 삽입
for email in parsed_emails_set:
    cur.execute("""
        INSERT IGNORE INTO parsed_emails (email)
        VALUES (%s)
    """, (email,))

# ✅ 마무리
conn.commit()
cur.close()
conn.close()

print("✅ posts → parsed_posts, parsed_emails 변환 완료")
