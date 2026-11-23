
from app.engines.os_engine import ResourceManager


def test_semaphore_release():

    print("\n========== OS ENGINE TC06 ==========")
    print("TEST: SEMAPHORE RELEASE AND REACQUISITION")

    manager = ResourceManager()

    # First acquisition
    with manager.acquire_semaphore("sports_equipment", capacity=1):
        print("\nFirst acquisition successful.")

    print("First semaphore permit released.")

    # Second acquisition after release
    try:
        with manager.acquire_semaphore(
            "sports_equipment",
            capacity=1,
            timeout=1
        ):
            print("Second acquisition successful.")

        print("Second semaphore permit released.")

        print("\nTEST RESULT: PASS")
        print("Semaphore release and reacquisition verified.")

    except TimeoutError:
        print("\nTEST RESULT: FAIL")
        print("Semaphore was not released correctly.")


if __name__ == "__main__":
    test_semaphore_release()
