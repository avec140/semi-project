# run_all.py
import threading
import subprocess
import time
import webbrowser

def run_flask():
    subprocess.run(["python", "app.py"])

def run_crawler():
    subprocess.run(["python", "crawler.py"])

def run_throw_ela():
    subprocess.run(["python", "throw_ela.py"])

def run_convert_posts():
    subprocess.run(["python", "convert_posts.py"])

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_crawler).start()
    threading.Thread(target=run_convert_posts).start()
    threading.Thread(target=run_throw_ela).start()

     # 잠시 대기 후 브라우저 자동 실행
    time.sleep(5)
    webbrowser.open_new_tab("http://127.0.0.1:5000")
    webbrowser.open_new_tab("http://localhost:5601/app/dashboards#/view/dc3b41a1-9c38-4276-9e93-936aa3d0f1e4?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:'2018-01-30T12:38:04.410Z',to:now))")


