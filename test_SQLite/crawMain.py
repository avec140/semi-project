def crawl_bcw_data():
    import requests
    from bs4 import BeautifulSoup
    import pandas as pd
    import sqlite3

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

    df = pd.DataFrame(results)
    df.to_csv("bcw_forum_10pages.csv", index=False, encoding="utf-8-sig")
    print("🗂 CSV 저장 완료: bcw_forum_10pages.csv")

    conn = sqlite3.connect("bcw_forum.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        author TEXT,
        date TEXT,
        keywords TEXT,
        summary TEXT,
        UNIQUE(title, author, date)
    )
    """)

    # ✅ 새로 추가된 게시글 개수 추적
    new_posts = 0

    for post in results:
        cur.execute("""
            INSERT OR IGNORE INTO posts (title, author, date, keywords, summary)
            VALUES (?, ?, ?, ?, ?)
        """, (
            post["제목"],
            post["작성자"],
            post["날짜"],
            post["키워드"],
            post["본문 요약"]
        ))
        if cur.rowcount == 1:
            new_posts += 1

    conn.commit()
    conn.close()
    print("✅ SQLite 저장 완료 : bcw_forum.db")

    if new_posts > 0:
        print(f"🔔 새로운 게시글 {new_posts}개 발견!")
        # 추후: 알림
    else:
        print("ℹ️ 새로운 게시글 없음.")
