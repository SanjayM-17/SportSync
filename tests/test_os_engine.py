
import threading
import time

from app.engines.os_engine import ResourceManager


manager = ResourceManager()

passed = 0
total = 2


# TEST 1: MUTEX LOCK
counter = 0
active_threads = 0
max_active = 0

counter_lock = threading.Lock()


def mutex_worker():
    global counter, active_threads, max_active

    with manager.acquire_resources(["F001"]):
        with counter_lock:
            active_threads += 1
            max_active = max(max_active, active_threads)

        time.sleep(0.05)
        counter += 1

        with counter_lock:
            active_threads -= 1


threads = [
    threading.Thread(target=mutex_worker)
    for _ in range(10)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

if counter == 10 and max_active == 1:
    print("PASS: Mutex synchronization")
    passed += 1
else:
    print("FAIL: Mutex synchronization")


# TEST 2: SEMAPHORE LIMIT
active = 0
max_active = 0

state_lock = threading.Lock()


def semaphore_worker():
    global active, max_active

    with manager.acquire_semaphore("E002", 2, timeout=5):
        with state_lock:
            active += 1
            max_active = max(max_active, active)

        time.sleep(0.1)

        with state_lock:
            active -= 1


threads = [
    threading.Thread(target=semaphore_worker)
    for _ in range(6)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

if max_active <= 2 and max_active > 0:
    print("PASS: Semaphore resource limit")
    passed += 1
else:
    print("FAIL: Semaphore resource limit")


print(f"\nOS ENGINE RESULT: {passed}/{total} tests passed")
