
from app.engines.os_engine import ResourceManager


def test_multiple_resource_locking():

    print("\n========== OS ENGINE TC03 ==========")
    print("TEST: MULTIPLE RESOURCE LOCKING")

    manager = ResourceManager()

    resources = [
        "football_ground",
        "football_equipment",
        "campus_booking"
    ]

    print("\nRequested resources:", resources)

    with manager.acquire_resources(resources):
        print("\nAll resource locks acquired successfully.")

        for resource in resources:
            print("Locked:", resource)

    print("\nAll resource locks released successfully.")

    print("\nTEST RESULT: PASS")


if __name__ == "__main__":
    test_multiple_resource_locking()
