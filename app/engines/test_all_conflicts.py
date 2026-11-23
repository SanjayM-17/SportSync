
from uuid import uuid4

from sqlalchemy import text
from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts


db = SessionLocal()

try:
    print("\n========== ALL CONFLICTS VALIDATION ==========")

    facility = db.execute(
        text("""
            SELECT facility_id, facility_name, capacity, location
            FROM facilities
            WHERE LOWER(sport_type) = 'football'
            LIMIT 1
        """)
    ).mappings().first()

    equipment = db.execute(
        text("""
            SELECT equipment_id, total_quantity
            FROM equipment
            WHERE LOWER(sport) = 'football'
            LIMIT 1
        """)
    ).mappings().first()

    user_id = db.execute(
        text("SELECT user_id FROM users LIMIT 1")
    ).scalar()

    if not facility or not equipment or not user_id:
        raise Exception("Required test records not found.")

    test_id = "TEST-" + uuid4().hex[:12]

    # Insert temporary Confirmed booking
    db.execute(
        text("""
            INSERT INTO bookings (
                booking_id,
                request_id,
                user_id,
                sport,
                booking_date,
                start_time,
                end_time,
                duration_minutes,
                participants,
                equipment_id,
                equipment_quantity,
                facility_id,
                facility_name,
                location,
                booking_status
            )
            VALUES (
                :id, :id, :user_id, 'Football',
                '2030-01-01', '07:00', '08:00',
                60, 20, :equipment_id, 1,
                :facility_id, :facility_name,
                :location, 'Confirmed'
            )
        """),
        {
            "id": test_id,
            "user_id": user_id,
            "equipment_id": equipment["equipment_id"],
            "facility_id": facility["facility_id"],
            "facility_name": facility["facility_name"],
            "location": facility["location"]
        }
    )

    # Request deliberately violates all four conditions
    conflicts = detect_conflicts(
        db=db,
        sport="Football",
        participants=facility["capacity"] + 1,
        facility_id=facility["facility_id"],
        booking_date="2030-01-01",
        start_time="07:00",
        end_time="08:00",
        equipment_id=equipment["equipment_id"],
        equipment_quantity=equipment["total_quantity"] + 1
    )

    print("\nDETECTED CONFLICTS:")

    for conflict in conflicts:
        print("-", conflict["type"])

    expected = {
        "Time-Slot Conflict",
        "Capacity Conflict",
        "Facility/Resource Conflict",
        "Equipment Conflict"
    }

    actual = {item["type"] for item in conflicts}

    print("\nExpected conflict types:", len(expected))
    print("Detected conflict types:", len(actual))

    if actual == expected:
        print("\nTEST RESULT: PASS")
        print("All four conflict types detected!")
    else:
        print("\nTEST RESULT: FAIL")
        print("Missing:", expected - actual)

finally:
    db.rollback()
    db.close()

    print("\nTemporary test booking rolled back.")
    print("Original dataset unchanged.")
