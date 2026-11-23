
from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts

db = SessionLocal()

tests = [
    {
        "name": "Time-Slot Conflict",
        "data": {
            "sport": "Football",
            "participants": 10,
            "facility_id": "F001",
            "booking_date": "2030-01-01",
            "start_time": "07:00",
            "end_time": "08:00",
            "equipment_id": "E002",
            "equipment_quantity": 5
        },
        "expected": "Time-Slot Conflict"
    },
    {
        "name": "Capacity Conflict",
        "data": {
            "sport": "Football",
            "participants": 100,
            "facility_id": "F001",
            "booking_date": "2018-01-01",
            "start_time": "07:00",
            "end_time": "08:00",
            "equipment_id": "E002",
            "equipment_quantity": 5
        },
        "expected": "Capacity Conflict"
    },
    {
        "name": "Equipment Conflict",
        "data": {
            "sport": "Football",
            "participants": 10,
            "facility_id": "F001",
            "booking_date": "2018-01-01",
            "start_time": "07:00",
            "end_time": "08:00",
            "equipment_id": "E002",
            "equipment_quantity": 16
        },
        "expected": "Equipment Conflict"
    }
]

try:
    passed = 0

    print("========== TC23: CONFLICT REGRESSION ==========")

    for test in tests:
        conflicts = detect_conflicts(db=db, **test["data"])

        found = any(
            conflict["type"] == test["expected"]
            for conflict in conflicts
        )

        if found:
            print(f"PASS: {test['name']}")
            passed += 1
        else:
            print(f"FAIL: {test['name']}")
            print("Actual conflicts:", conflicts)

    print(f"\nRESULT: {passed}/{len(tests)} tests passed")

finally:
    db.close()
