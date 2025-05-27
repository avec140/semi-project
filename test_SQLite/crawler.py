import time
from crawMain import crawl_bcw_data  # 크롤링 함수 import

while True:
    print("🕒 30분마다 크롤링 실행 중...")
    crawl_bcw_data()
    print("✅ 수집 완료. 다음 실행까지 대기 중...\n")
    time.sleep(900)  # 900초 = 15분
