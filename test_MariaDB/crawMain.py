# crawMain.py ver1.0
import requests
from bs4 import BeautifulSoup
import mysql.connector

# ✅ MariaDB 접속 설정
config = {
    "host": "localhost",
    "user": "",
    "password": "",
    "database": "bcw",
    "port": 3306
}

# ✅ DB 및 테이블 자동 생성
def initialize_mariadb():
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            port=config["port"]
        )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS bcw")
        conn.commit()
        cur.close()
        conn.close()

        conn = mysql.connector.connect(**config)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                author VARCHAR(255),
                date VARCHAR(255),
                keywords TEXT,
                summary TEXT,
                UNIQUE(title, author, date)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

        print("✅ MariaDB 초기화 완료 (DB + 테이블)")
    except Exception as e:
        print("❌ DB 초기화 실패:", e)

# ✅ 크롤링된 결과를 MariaDB에 저장
def save_to_mariadb(results):
    inserted = []
    try:
        conn = mysql.connector.connect(**config)
        cur = conn.cursor()

        for post in results:
            try:
                cur.execute("""
                    INSERT INTO posts (title, author, date, keywords, summary)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        keywords = VALUES(keywords),
                        summary = VALUES(summary)
                """, (
                    post["제목"],
                    post["작성자"],
                    post["날짜"],
                    post["키워드"],
                    post["본문 요약"]
                ))
                if cur.rowcount == 1:
                    inserted.append(post)
            except Exception as e:
                print("❌ 삽입 오류:", e)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ MariaDB 저장 완료")
        return inserted

    except Exception as e:
        print("❌ DB 연결 실패:", e)
        return []

# ✅ 크롤링 실행
def crawl_bcw_data():
    proxies = {
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }

    base_url = "http://bestteermb42clir6ux7xm76d4jjodh3fpahjqgbddbmfrgp4skg2wqd.onion/"
    forum_path = "viewforum.php?f=30"
    results = []

    for page in range(10):
        start = page * 25
        url = f"{base_url}{forum_path}" if page == 0 else f"{base_url}{forum_path}&start={start}"
        print(f"📄 페이지 {page+1} 요청 중: {url}")

        try:
            res = requests.get(url, proxies=proxies, timeout=20)
            soup = BeautifulSoup(res.text, "html.parser")
            post_links = soup.select("a.topictitle")

            for post in post_links:
                title = post.text.strip()
                href = post.get("href")
                if not href:
                    continue
                post_url = base_url + href.lstrip("./")

                try:
                    post_res = requests.get(post_url, proxies=proxies, timeout=20)
                    post_soup = BeautifulSoup(post_res.text, "html.parser")

                    author_node = post_soup.select_one("p.author strong")
                    author = author_node.get_text(strip=True) if author_node else "(작성자 없음)"

                    author_tag = post_soup.select_one("p.author")
                    date = author_tag.get_text(strip=True).split("»")[-1].strip() if author_tag else "(날짜 없음)"

                    body_tag = post_soup.select_one("div.postbody")
                    summary = body_tag.get_text(strip=True)[:200] if body_tag else "(본문 없음)"

                    keywords = []
                    for kw in ["USA", "database", "customer", "SSN", "DOB", "fullz", "MEGA", "BIN", "email", "phone", "txt", "leak"]:
                        if kw.lower() in summary.lower():
                            keywords.append(kw)

                    results.append({
                        "제목": title,
                        "작성자": author,
                        "날짜": date,
                        "키워드": ", ".join(keywords),
                        "본문 요약": summary
                    })

                except Exception as e:
                    results.append({
                        "제목": title,
                        "작성자": "(불러오기 실패)",
                        "날짜": "-",
                        "키워드": "-",
                        "본문 요약": f"(본문 로딩 실패: {e})"
                    })

        except Exception as e:
            print(f"❌ 페이지 {page+1} 요청 실패: {e}")

    new_posts = save_to_mariadb(results)
    if new_posts:
        print# 통합된 bcw_crawler_with_telegram.py

import requests
from bs4 import BeautifulSoup
import mysql.connector
import json

# ✅ MariaDB 접속 설정
config = {
    "host": "localhost",
    "user": "root",            # ← 사용자 환경에 맞게 변경
    "password": "1234",        # ← 사용자 환경에 맞게 변경
    "database": "bcw",
    "port": 3306
}

# ✅ 텔레그램 설정
bot_token = "7904703336:AAGnhRjYO42TIF6VuP-sCVfZMZ_OjToPxuI"
chat_id = "7894265954"

def send_message(message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        res = requests.post(url, data=data)
        if res.status_code == 200:
            print("✅ 텔레그램 메시지 전송 성공")
        else:
            print(f"❌ 텔레그램 전송 실패: {res.status_code}")
    except Exception as e:
        print(f"❌ 텔레그램 전송 예외: {e}")

# ✅ MariaDB 초기화
def initialize_mariadb():
    try:
        conn = mysql.connector.connect(
            host=config["host"],
            user=config["user"],
            password=config["password"],
            port=config["port"]
        )
        cur = conn.cursor()
        cur.execute("CREATE DATABASE IF NOT EXISTS bcw")
        conn.commit()
        cur.close()
        conn.close()

        conn = mysql.connector.connect(**config)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255),
                author VARCHAR(255),
                date VARCHAR(255),
                keywords TEXT,
                summary TEXT,
                UNIQUE(title, author, date)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

        print("✅ MariaDB 초기화 완료")
    except Exception as e:
        print("❌ DB 초기화 실패:", e)

# ✅ MariaDB에 결과 저장
def save_to_mariadb(results):
    inserted = []
    try:
        conn = mysql.connector.connect(**config)
        cur = conn.cursor()

        for post in results:
            try:
                cur.execute("""
                    INSERT INTO posts (title, author, date, keywords, summary)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        keywords = VALUES(keywords),
                        summary = VALUES(summary)
                """, (
                    post["제목"],
                    post["작성자"],
                    post["날짜"],
                    post["키워드"],
                    post["본문 요약"]
                ))
                if cur.rowcount == 1:
                    inserted.append(post)
            except Exception as e:
                print("❌ 삽입 오류:", e)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ MariaDB 저장 완료")
        return inserted

    except Exception as e:
        print("❌ DB 연결 실패:", e)
        return []

# ✅ 포럼 크롤링 및 텔레그램 알림
def crawl_bcw_data():
    proxies = {
        "http": "socks5h://127.0.0.1:9050",
        "https": "socks5h://127.0.0.1:9050"
    }

    base_url = "http://bestteermb42clir6ux7xm76d4jjodh3fpahjqgbddbmfrgp4skg2wqd.onion/"
    forum_path = "viewforum.php?f=30"
    results = []

    for page in range(1):  # 테스트를 위해 1페이지만
        start = page * 25
        url = f"{base_url}{forum_path}" if page == 0 else f"{base_url}{forum_path}&start={start}"
        print(f"📄 페이지 {page+1} 요청 중: {url}")

        try:
            res = requests.get(url, proxies=proxies, timeout=20)
            soup = BeautifulSoup(res.text, "html.parser")
            post_links = soup.select("a.topictitle")

            for post in post_links:
                title = post.text.strip()
                href = post.get("href")
                if not href:
                    continue
                post_url = base_url + href.lstrip("./")

                try:
                    post_res = requests.get(post_url, proxies=proxies, timeout=20)
                    post_soup = BeautifulSoup(post_res.text, "html.parser")

                    author_node = post_soup.select_one("p.author strong")
                    author = author_node.get_text(strip=True) if author_node else "(작성자 없음)"

                    author_tag = post_soup.select_one("p.author")
                    date = author_tag.get_text(strip=True).split("»")[-1].strip() if author_tag else "(날짜 없음)"

                    body_tag = post_soup.select_one("div.postbody")
                    summary = body_tag.get_text(strip=True)[:200] if body_tag else "(본문 없음)"

                    keywords = []
                    for kw in ["USA", "database", "customer", "SSN", "DOB", "fullz", "MEGA", "BIN", "email", "phone", "txt", "leak"]:
                        if kw.lower() in summary.lower():
                            keywords.append(kw)

                    results.append({
                        "제목": title,
                        "작성자": author,
                        "날짜": date,
                        "키워드": ", ".join(keywords),
                        "본문 요약": summary
                    })

                except Exception as e:
                    print("❌ 게시글 로딩 실패:", e)

        except Exception as e:
            print(f"❌ 페이지 {page+1} 요청 실패: {e}")

    new_posts = save_to_mariadb(results)

    if new_posts:
        print(f"🔔 새 게시글 {len(new_posts)}건 있음 - 텔레그램 전송 중...")
        for post in new_posts:
            message = (
                f"📌 제목: {post['제목']}\n"
                f"👤 작성자: {post['작성자']}\n"
                f"📅 날짜: {post['날짜']}\n"
                f"🔑 키워드: {post['키워드']}\n"
                f"📝 요약: {post['본문 요약'][:150]}..."
            )
            send_message(message)
    else:
        print("ℹ️ 새 게시글 없음")

# ✅ 실행
if __name__ == "__main__":
    initialize_mariadb()
    crawl_bcw_data()
(f"🔔 새로 삽입된 게시글 {len(new_posts)}건 있음")

if __name__ == "__main__":
    initialize_mariadb()
    crawl_bcw_data()