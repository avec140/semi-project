import time
from crawMain import crawl_bcw_data, initialize_mariadb

# 🔧 최초 1회 DB 및 테이블 생성
initialize_mariadb()

while True:
    print("⏱ 15분마다 크롤링 실행 중...")
    crawl_bcw_data()
    print("✅ 수집 완료. 다음 실행까지 대기 중...\n")
    time.sleep(900)  # 15분 = 900초
