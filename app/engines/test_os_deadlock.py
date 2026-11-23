
import threading

from app.engines.os_engine import ResourceManager


def test_deadlock_prevention():

    print("\n========== OS ENGINE TC07 ==========")
    print("TEST: DEADLOCK PREVENTION")

    manager = ResourceManager()

    completed = []

    def worker(thread_name, resources):

        print(thread_name, "requesting:", resources)

        with manager.acquire_resources(resources):
            print(thread_name, "acquired all resources.")
            completed.append(thread_name)

        print(thread_name, "released all resources.")

    # Opposite resource request orders
    t1 = threading.Thread(
        target=worker,
        args=("Thread 1", ["resource_A", "resource_B"])
    )

    t2 = threading.Thread(
        target=worker,
        args=("Thread 2", ["resource_B", "resource_A"])
    )

    t1.start()
    t2.start()

    t1.join(timeout=5)
    t2.join(timeout=5)

    if not t1.is_alive() and not t2.is_alive() and len(completed) == 2:
        print("\nTEST RESULT: PASS")
        print("Both threads completed without deadlock.")
    else:
        print("\nTEST RESULT: FAIL")
        print("Possible deadlock detected.")


if __name__ == "__main__":
    test_deadlock_prevention()
