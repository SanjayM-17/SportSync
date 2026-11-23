
import requests
import uuid

from app.database.connection import SessionLocal
from sqlalchemy import text

URL = "http://127.0.0.1:8000/bookings/confirm"
TEST_ID = "TEST-REG-" + uuid.uuid4().hex[:8].upper()

base_payload = {
    "request_id": TEST_ID,
    "user_id": "U0001",
    "sport": "Football",
    "participants": 20,
    "booking_date": "2018-01-01",
    "start_time": "07:00",
    "end_time": "08:00",
    "equipment_quantity": 5,
    "facility_id": "F001",
    "equipment_id": "E002"
}

tests = [
    ("Valid booking", base_payload.copy(), True),
    ("Duplicate identical request", base_payload.copy(), True),
]

changed = base_payload.copy()
changed["participants"] = 30

invalid_facility = base_payload.copy()
invalid_facility["request_id"] = TEST_ID + "-F"
invalid_facility["facility_id"] = "F999"

invalid_equipment = base_payload.copy()
invalid_equipment["request_id"] = TEST_ID + "-E"
invalid_equipment["equipment_id"] = "E999"

capacity = base_payload.copy()
capacity["request_id"] = TEST_ID + "-C"
capacity["participants"] = 100

equipment = base_payload.copy()
equipment["request_id"] = TEST_ID + "-Q"
equipment["equipment_quantity"] = 1000

tests.extend([
    ("Same ID with changed details", changed, False),
    ("Invalid facility", invalid_facility, False),
    ("Invalid equipment", invalid_equipment, False),
    ("Capacity conflict", capacity, False),
    ("Equipment conflict", equipment, False)
])

passed = 0

try:
    print("========== TC24: CONFIRMATION REGRESSION ==========")

    # Check API before testing
    health = requests.get(
        "http://127.0.0.1:8000/health",
        timeout=5
    )
    health.raise_for_status()

    for name, payload, expected in tests:
        response = requests.post(URL, json=payload, timeout=30)
        result = response.json()

        success = result.get("success") is expected

        if success:
            print(f"PASS: {name}")
            passed += 1
        else:
            print(f"FAIL: {name}")
            print(result)

finally:
    # Clean up only this test's records
    db = SessionLocal()

    try:
        db.execute(
            text("""
                DELETE FROM bookings
                WHERE request_id LIKE :pattern
            """),
            {"pattern": TEST_ID + "%"}
        )
        db.commit()
        print("\nTemporary test bookings cleaned up.")

    finally:
        db.close()

print(f"\nFINAL RESULT: {passed}/{len(tests)} tests passed")
