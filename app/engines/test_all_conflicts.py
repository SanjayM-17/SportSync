
from datetime import date

from app.database.connection import SessionLocal
from app.engines.conflict_engine import detect_conflicts


BOOKING_DATE = date(2035, 1, 1)


def run_test(name, test_function):
    print(f"\n{name}")

    try:
        test_function()
        print("PASS")
    except Exception as error:
        print("FAIL:", error)


def get_test_data(db):
    from sqlalchemy import text

    facility = db.execute(
        text("""
            SELECT facility_id, capacity, sport_type
            FROM facilities
            WHERE LOWER(availability) = 'available'
              AND LOWER(facility_status) = 'active'
            ORDER BY facility_id
            LIMIT 1
        """)
    ).mappings().first()

    equipment = db.execute(
        text("""
            SELECT equipment_id, total_quantity, sport
            FROM equipment
            WHERE LOWER(resource_status) = 'available'
            ORDER BY equipment_id
            LIMIT 1
        """)
    ).mappings().first()

    if facility is None:
        raise RuntimeError("No active facility found.")

    if equipment is None:
        raise RuntimeError("No available equipment found.")

    return facility, equipment


def test_invalid_time(db, facility, equipment):
    conflicts = detect_conflicts(
        db=db,
        sport=facility["sport_type"],
        participants=1,
        facility_id=facility["facility_id"],
        booking_date=BOOKING_DATE,
        start_time="09:00",
        end_time="08:00",
        equipment_id=equipment["equipment_id"],
        equipment_quantity=1
    )

    assert any(
        item["type"] == "Time-Slot Conflict"
        for item in conflicts
    )


def test_capacity_conflict(db, facility, equipment):
    conflicts = detect_conflicts(
        db=db,
        sport=facility["sport_type"],
        participants=facility["capacity"] + 1,
        facility_id=facility["facility_id"],
        booking_date=BOOKING_DATE,
        start_time="07:00",
        end_time="08:00",
        equipment_id=equipment["equipment_id"],
        equipment_quantity=1
    )

    assert any(
        item["type"] == "Capacity Conflict"
        for item in conflicts
    )


def test_same_facility_conflict(db, facility, equipment):
    from sqlalchemy import text

    request_id = "TEST_ALL_CONFLICTS_FACILITY"

    try:
        db.execute(
            text("""
                DELETE FROM bookings
                WHERE request_id = :request_id
            """),
            {"request_id": request_id}
        )

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
                    equipment_required,
                    equipment_quantity,
                    facility_id,
                    facility_name,
                    location,
                    booking_status
                )
                SELECT
                    'TEST_ALL_CONFLICTS_BOOKING',
                    :request_id,
                    user_id,
                    :sport,
                    :booking_date,
                    '07:00',
                    '08:00',
                    60,
                    1,
                    :equipment_id,
                    'Yes',
                    1,
                    :facility_id,
                    facility_name,
                    location,
                    'Confirmed'
                FROM facilities
                CROSS JOIN (
                    SELECT user_id
                    FROM users
                    LIMIT 1
                ) AS test_user
                WHERE facility_id = :facility_id
            """),
            {
                "request_id": request_id,
                "sport": facility["sport_type"],
                "booking_date": BOOKING_DATE,
                "equipment_id": equipment["equipment_id"],
                "facility_id": facility["facility_id"]
            }
        )

        db.flush()

        conflicts = detect_conflicts(
            db=db,
            sport=facility["sport_type"],
            participants=1,
            facility_id=facility["facility_id"],
            booking_date=BOOKING_DATE,
            start_time="07:30",
            end_time="08:30",
            equipment_id=equipment["equipment_id"],
            equipment_quantity=1
        )

        assert any(
            item["type"] == "Facility/Resource Conflict"
            for item in conflicts
        )

    finally:
        db.rollback()


def test_different_facility_no_conflict(db):
    from sqlalchemy import text

    facilities = db.execute(
        text("""
            SELECT facility_id, capacity, sport_type
            FROM facilities
            WHERE LOWER(availability) = 'available'
              AND LOWER(facility_status) = 'active'
            ORDER BY facility_id
            LIMIT 2
        """)
    ).mappings().all()

    if len(facilities) < 2:
        print("SKIPPED: Need two active facilities.")
        return

    first, second = facilities

    conflicts = detect_conflicts(
        db=db,
        sport=second["sport_type"],
        participants=1,
        facility_id=second["facility_id"],
        booking_date=BOOKING_DATE,
        start_time="07:00",
        end_time="08:00"
    )

    assert not any(
        item["type"] == "Facility/Resource Conflict"
        for item in conflicts
    )


def main():
    db = SessionLocal()

    try:
        facility, equipment = get_test_data(db)

        run_test(
            "TC01 - Invalid time interval",
            lambda: test_invalid_time(db, facility, equipment)
        )

        run_test(
            "TC02 - Capacity conflict",
            lambda: test_capacity_conflict(db, facility, equipment)
        )

        run_test(
            "TC03 - Same facility overlapping booking",
            lambda: test_same_facility_conflict(
                db, facility, equipment
            )
        )

        run_test(
            "TC04 - Different facilities can share a time",
            lambda: test_different_facility_no_conflict(db)
        )

    finally:
        db.rollback()
        db.close()


if __name__ == "__main__":
    main()
