
from app.engines.os_engine import ResourceManager


def test_semaphore_timeout():

    print("\n========== OS ENGINE TC05 ==========")
    print("TEST: SEMAPHORE TIMEOUT")

    manager = ResourceManager()

    try:
        # Acquire the only available permit
        with manager.acquire_semaphore(
            "limited_equipment", capacity=1
        ):

            print("\nSemaphore acquired by first operation.")

            try:
                # Second acquisition should time out
                with manager.acquire_semaphore(
                    "limited_equipment",
                    capacity=1,
                    timeout=1
                ):
                    print("Unexpectedly acquired semaphore.")

                print("\nTEST RESULT: FAIL")

            except TimeoutError as error:
                print("\nTimeout correctly detected.")
                print("Message:", error)
                print("\nTEST RESULT: PASS")

        print("\nFirst semaphore permit released.")

    except Exception as error:
        print("\nTEST EXECUTION ERROR:", error)


if __name__ == "__main__":
    test_semaphore_timeout()
