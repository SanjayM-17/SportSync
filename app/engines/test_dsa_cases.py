
from app.database.connection import SessionLocal
from app.engines.dsa_engine import find_feasible_options


db = SessionLocal()

test_cases = [
    {
        "name": "TC01 - Valid Football Request",
        "sport": "Football",
        "participants": 20,
        "date": "2018-01-01",
        "start": "07:00",
        "end": "08:00",
        "equipment": 5,
        "expected": "FEASIBLE"
    },
    {
        "name": "TC02 - Unsupported Sport",
        "sport": "Swimming",
        "participants": 20,
        "date": "2018-01-01",
        "start": "07:00",
        "end": "08:00",
        "equipment": 5,
        "expected": "NOT FEASIBLE"
    },
    {
        "name": "TC03 - Capacity Too High",
        "sport": "Football",
        "participants": 1000,
        "date": "2018-01-01",
        "start": "07:00",
        "end": "08:00",
        "equipment": 5,
        "expected": "NOT FEASIBLE"
    },
    {
        "name": "TC04 - Equipment Quantity Too High",
        "sport": "Football",
        "participants": 20,
        "date": "2018-01-01",
        "start": "07:00",
        "end": "08:00",
        "equipment": 1000,
        "expected": "NOT FEASIBLE"
    },
    {
        "name": "TC05 - Invalid Participant Count",
        "sport": "Football",
        "participants": 0,
        "date": "2018-01-01",
        "start": "07:00",
        "end": "08:00",
        "equipment": 5,
        "expected": "INVALID INPUT"
    }
]

try:
    print("\n========== DSA TEST CASE VALIDATION ==========")

    passed = 0

    for case in test_cases:
        print("\n", case["name"])

        try:
            results = find_feasible_options(
                db,
                case["sport"],
                case["participants"],
                case["date"],
                case["start"],
                case["end"],
                case["equipment"]
            )

            actual = "FEASIBLE" if results else "NOT FEASIBLE"

        except ValueError:
            actual = "INVALID INPUT"

        status = "PASS" if actual == case["expected"] else "FAIL"

        print("Expected:", case["expected"])
        print("Actual:", actual)
        print("Test Result:", status)

        if status == "PASS":
            passed += 1

    print("\n========== FINAL TEST SUMMARY ==========")
    print("Total Test Cases:", len(test_cases))
    print("Passed:", passed)
    print("Failed:", len(test_cases) - passed)

finally:
    db.close()
