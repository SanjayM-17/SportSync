
from uuid import uuid4

from sqlalchemy import text
from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts


db = SessionLocal()

try:
    print("\n========== FACILITY CONFLICT TEST ==========")

    # STEP 1: Get an existing Football facility
    facility = db.execute(
        text("""
            SELECT facility_id, facility_name, capacity, location
            FROM facilities
            WHERE LOWER(sport_type) = 'football'
            LIMIT 1
        """)
    ).mappings().first()

    # STEP 2: Get an existing user
    user_id = db.execute(
        text("""
            SELECT user_id
            FROM users
            LIMIT 1
        """)
    ).scalar()

    if not facility or not user_id:
        raise Exception("Required test records not found.")

    print("Facility:", facility["facility_name"])

    # STEP 3: Insert a temporary Confirmed booking
    temporary_id = "TEST-" + uuid4().hex[:12]

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
                facility_id,
                facility_name,
                location,
                booking_status
            )
            VALUES (
                :booking_id,
                :request_id,
                :user_id,
                'Football',
                '2018-01-01',
                '07:00',
                '08:00',
                60,
                20,
                :facility_id,
                :facility_name,
                :location,
                'Confirmed'
            )
        """),
        {
            "booking_id": temporary_id,
            "request_id": temporary_id,
            "user_id": user_id,
            "facility_id": facility["facility_id"],
            "facility_name": facility["facility_name"],
            "location": facility["location"]
        }
    )

    print("\nTemporary Confirmed booking created.")

    # STEP 4: Check another request for the same facility and time
    conflicts = detect_conflicts(
        db=db,
        sport="Football",
        participants=20,
        facility_id=facility["facility_id"],
        booking_date="2018-01-01",
        start_time="07:00",
        end_time="08:00"
    )

    print("\nDETECTED CONFLICTS:")

    for conflict in conflicts:
        print(
            conflict["type"],
            "-",
            conflict["message"]
        )

    # STEP 5: Verify the result
    facility_conflict_found = any(
        item["type"] == "Facility/Resource Conflict"
        for item in conflicts
    )

    if facility_conflict_found:
        print("\nTEST RESULT: PASS")
        print("Facility/Resource Conflict detected successfully.")
    else:
        print("\nTEST RESULT: FAIL")

finally:
    # Undo the temporary booking
    db.rollback()
    db.close()

    print("\nTemporary test data rolled back.")
    print("Original dataset remains unchanged.")
