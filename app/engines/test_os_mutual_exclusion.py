
import threading
import time

from app.engines.os_engine import ResourceManager


def test_mutual_exclusion():

    print("\n========== OS ENGINE TC02 ==========")
    print("TEST: MUTUAL EXCLUSION")

    manager = ResourceManager()

    active_threads = 0
    maximum_active = 0

    counter_lock = threading.Lock()

    def worker(thread_name):

        nonlocal active_threads, maximum_active

        with manager.acquire_resources(["football_ground"]):

            with counter_lock:
                active_threads += 1
                maximum_active = max(
                    maximum_active, active_threads
                )

            print(thread_name, "entered critical section.")

            time.sleep(1)

            with counter_lock:
                active_threads -= 1

            print(thread_name, "exited critical section.")

    t1 = threading.Thread(target=worker, args=("Thread 1",))
    t2 = threading.Thread(target=worker, args=("Thread 2",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("\nMaximum simultaneous threads:", maximum_active)

    if maximum_active == 1:
        print("\nTEST RESULT: PASS")
        print("Mutual exclusion successfully verified.")
    else:
        print("\nTEST RESULT: FAIL")


if __name__ == "__main__":
    test_mutual_exclusion()
