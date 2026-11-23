
from sqlalchemy import text

from app.database.connection import SessionLocal

from app.engines.conflict_engine import (
    detect_conflicts,
    is_facility_time_available
)


TEST_DATE = "2035-01-02"
TEST_BOOKING_ID = "E1_CONFLICT_TEST"
TEST_REQUEST_ID = "E1_CONFLICT_REQUEST"


def main():

    db = SessionLocal()
    passed = 0
    total = 7

    try:
        print("\n========== SPORTSYNC CONFLICT ENGINE TEST ==========")

        # ==========================================
        # GET TEST FACILITY
        # ==========================================

        facility = db.execute(
            text("""
                SELECT facility_id, facility_name,
                       capacity, sport_type, location
                FROM facilities
                WHERE LOWER(sport_type) = 'football'
                  AND LOWER(availability) = 'available'
                  AND LOWER(facility_status) = 'active'
                LIMIT 1
            """)
        ).mappings().first()

        if not facility:
            raise RuntimeError("Football facility not found.")

        facility_id = facility["facility_id"]

        second_facility = db.execute(
            text("""
                SELECT facility_id
                FROM facilities
                WHERE facility_id != :facility_id
                  AND LOWER(availability) = 'available'
                  AND LOWER(facility_status) = 'active'
                LIMIT 1
            """),
            {"facility_id": facility_id}
        ).mappings().first()

        if not second_facility:
            raise RuntimeError("Second facility not found.")

        second_facility_id = second_facility["facility_id"]

        equipment = db.execute(
            text("""
                SELECT equipment_id, total_quantity
                FROM equipment
                WHERE LOWER(sport) = 'football'
                  AND LOWER(resource_status) = 'available'
                LIMIT 1
            """)
        ).mappings().first()

        if not equipment:
            raise RuntimeError("Football equipment not found.")

        equipment_id = equipment["equipment_id"]

        user = db.execute(
            text("SELECT user_id FROM users LIMIT 1")
        ).first()

        if not user:
            raise RuntimeError("No user found in users table.")

        user_id = user[0]

        # ==========================================
        # CLEAN PREVIOUS TEST DATA
        # ==========================================

        db.execute(
            text("""
                DELETE FROM bookings
                WHERE booking_id = :booking_id
                   OR request_id = :request_id
            """),
            {
                "booking_id": TEST_BOOKING_ID,
                "request_id": TEST_REQUEST_ID
            }
        )
        db.commit()

        # ==========================================
        # TC01 - VALID REQUEST
        # ==========================================

        print("\nTC01 - Valid Request")

        conflicts = detect_conflicts(
            db=db,
            sport="Football",
            participants=1,
            facility_id=facility_id,
            booking_date="2035-01-01",
            start_time="07:00",
            end_time="08:00",
            equipment_id=equipment_id,
            equipment_quantity=1
        )

        status = len(conflicts) == 0
        print("Expected no conflicts:", status)
        passed += int(status)

        # ==========================================
        # TC02 - CAPACITY CONFLICT
        # ==========================================

        print("\nTC02 - Capacity Conflict")

        conflicts = detect_conflicts(
            db=db,
            sport="Football",
            participants=facility["capacity"] + 1,
            facility_id=facility_id,
            booking_date="2035-01-01",
            start_time="07:00",
            end_time="08:00",
            equipment_id=equipment_id,
            equipment_quantity=1
        )

        status = any(
            item["type"] == "Capacity Conflict"
            for item in conflicts
        )

        print("Capacity conflict detected:", status)
        passed += int(status)

        # ==========================================
        # INSERT TEMPORARY CONFIRMED BOOKING
        # ==========================================

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
                VALUES (
                    :booking_id,
                    :request_id,
                    :user_id,
                    'Football',
                    :booking_date,
                    '07:00',
                    '08:00',
                    60,
                    1,
                    :equipment_id,
                    'Yes',
                    1,
                    :facility_id,
                    :facility_name,
                    :location,
                    'Confirmed'
                )
            """),
            {
                "booking_id": TEST_BOOKING_ID,
                "request_id": TEST_REQUEST_ID,
                "user_id": user_id,
                "booking_date": TEST_DATE,
                "equipment_id": equipment_id,
                "facility_id": facility_id,
                "facility_name": facility["facility_name"],
                "location": facility["location"]
            }
        )

        db.commit()

        # ==========================================
        # TC03 - SAME FACILITY OVERLAP
        # ==========================================

        print("\nTC03 - Same Facility Overlapping Booking")

        available = is_facility_time_available(
            db,
            facility_id,
            TEST_DATE,
            "07:30",
            "08:30"
        )

        status = available is False
        print("Overlapping booking rejected:", status)
        passed += int(status)

        # ==========================================
        # TC04 - DIFFERENT FACILITY SAME TIME
        # ==========================================

        print("\nTC04 - Different Facility Same Time")

        available = is_facility_time_available(
            db,
            second_facility_id,
            TEST_DATE,
            "07:00",
            "08:00"
        )

        status = available is True
        print("Different facility booking allowed:", status)
        passed += int(status)

        # ==========================================
        # TC05 - ADJACENT SLOT
        # ==========================================

        print("\nTC05 - Adjacent Time Slot")

        available = is_facility_time_available(
            db,
            facility_id,
            TEST_DATE,
            "08:00",
            "09:00"
        )

        status = available is True
        print("Adjacent slot allowed:", status)
        passed += int(status)

        # ==========================================
        # TC06 - INVALID TIME INTERVAL
        # ==========================================

        print("\nTC06 - Invalid Time Interval")

        available = is_facility_time_available(
            db,
            facility_id,
            "2035-01-03",
            "09:00",
            "08:00"
        )

        status = available is False
        print("Invalid interval rejected:", status)
        passed += int(status)

        # ==========================================
        # TC07 - EQUIPMENT CONFLICT
        # ==========================================

        print("\nTC07 - Equipment Conflict")

        conflicts = detect_conflicts(
            db=db,
            sport="Football",
            participants=1,
            facility_id=facility_id,
            booking_date="2035-01-01",
            start_time="07:00",
            end_time="08:00",
            equipment_id=equipment_id,
            equipment_quantity=equipment["total_quantity"] + 1
        )

        status = any(
            item["type"] == "Equipment Conflict"
            for item in conflicts
        )

        print("Equipment conflict detected:", status)
        passed += int(status)

        # ==========================================
        # FINAL SUMMARY
        # ==========================================

        print("\n========== TEST SUMMARY ==========")
        print("Total tests:", total)
        print("Passed:", passed)
        print("Failed:", total - passed)

        if passed == total:
            print("ALL CONFLICT TESTS PASSED.")
        else:
            print("SOME TESTS FAILED.")

    finally:
        db.rollback()

        db.execute(
            text("""
                DELETE FROM bookings
                WHERE booking_id = :booking_id
                   OR request_id = :request_id
            """),
            {
                "booking_id": TEST_BOOKING_ID,
                "request_id": TEST_REQUEST_ID
            }
        )

        db.commit()
        db.close()


if __name__ == "__main__":
    main()
