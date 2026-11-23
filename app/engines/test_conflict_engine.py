
from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts
from sqlalchemy import text


db = SessionLocal()

try:
    print("\n========== SPORTSYNC CONFLICT DETECTION TEST ==========")

    # Get a real Football facility
    facility = db.execute(
        text("""
            SELECT facility_id, capacity
            FROM facilities
            WHERE LOWER(sport_type) = 'football'
            LIMIT 1
        """)
    ).mappings().first()

    if not facility:
        raise Exception("No Football facility found.")

    facility_id = facility["facility_id"]

    # Get one real Football equipment record
    equipment = db.execute(
        text("""
            SELECT equipment_id, total_quantity
            FROM equipment
            WHERE LOWER(sport) = 'football'
            LIMIT 1
        """)
    ).mappings().first()

    if not equipment:
        raise Exception("No Football equipment found.")

    equipment_id = equipment["equipment_id"]

    test_cases = [
        {
            "name": "TC01 - Valid Request",
            "date": "2018-01-01",
            "start": "07:00",
            "end": "08:00",
            "participants": 20,
            "equipment_quantity": 5,
            "expected": 0
        },
        {
            "name": "TC02 - Capacity Conflict",
            "date": "2018-01-01",
            "start": "07:00",
            "end": "08:00",
            "participants": facility["capacity"] + 1,
            "equipment_quantity": 5,
            "expected": 1
        },
        {
            "name": "TC03 - Time-Slot Conflict",
            "date": "2030-01-01",
            "start": "07:00",
            "end": "08:00",
            "participants": 20,
            "equipment_quantity": 5,
            "expected": 1
        },
        {
            "name": "TC04 - Multiple Conflicts",
            "date": "2030-01-01",
            "start": "07:00",
            "end": "08:00",
            "participants": facility["capacity"] + 1,
            "equipment_quantity": equipment["total_quantity"] + 1,
            "expected": 3
        }
    ]

    passed = 0

    for case in test_cases:
        print("\n" + case["name"])

        conflicts = detect_conflicts(
            db=db,
            sport="Football",
            participants=case["participants"],
            facility_id=facility_id,
            booking_date=case["date"],
            start_time=case["start"],
            end_time=case["end"],
            equipment_id=equipment_id,
            equipment_quantity=case["equipment_quantity"]
        )

        for conflict in conflicts:
            print(
                conflict["type"],
                "-",
                conflict["message"]
            )

        actual = len(conflicts)

        status = (
            "PASS"
            if actual == case["expected"]
            else "FAIL"
        )

        print("Expected conflicts:", case["expected"])
        print("Actual conflicts:", actual)
        print("Test result:", status)

        if status == "PASS":
            passed += 1

    print("\n========== FINAL TEST SUMMARY ==========")
    print("Total test cases:", len(test_cases))
    print("Passed:", passed)
    print("Failed:", len(test_cases) - passed)

finally:
    db.close()

