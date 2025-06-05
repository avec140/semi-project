import time
import requests
from crawMain import crawl_bcw_data  # 실제 크롤링 함수

while True:
    try:
        new_count = crawl_bcw_data()  # 새 게시글 수 받아오기
        if new_count > 0:             # 새 게시글이 있을 때 알림 전송
            requests.post("http://127.0.0.1:5000/notify")
    except Exception as e:
        print(f"[ERROR] {e}")
    time.sleep(900)  # 15분 대기
