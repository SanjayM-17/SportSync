
import threading
import time

from app.engines.os_engine import ResourceManager


def test_semaphore_capacity():

    print("\n========== OS ENGINE TC04 ==========")
    print("TEST: SEMAPHORE CAPACITY")

    manager = ResourceManager()

    capacity = 2
    active_threads = 0
    maximum_active = 0

    counter_lock = threading.Lock()

    def worker(thread_name):

        nonlocal active_threads, maximum_active

        with manager.acquire_semaphore("sports_equipment", capacity):

            with counter_lock:
                active_threads += 1
                maximum_active = max(
                    maximum_active, active_threads
                )

            print(thread_name, "acquired semaphore.")

            time.sleep(1)

            with counter_lock:
                active_threads -= 1

            print(thread_name, "released semaphore.")

    threads = []

    for i in range(4):
        thread = threading.Thread(
            target=worker,
            args=(f"Thread {i + 1}",)
        )
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print("\nSemaphore capacity:", capacity)
    print("Maximum simultaneous threads:", maximum_active)

    if maximum_active == capacity:
        print("\nTEST RESULT: PASS")
        print("Semaphore capacity successfully enforced.")
    else:
        print("\nTEST RESULT: FAIL")


if __name__ == "__main__":
    test_semaphore_capacity()
