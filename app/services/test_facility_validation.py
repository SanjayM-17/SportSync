
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_facility_validation():

    db = SessionLocal()

    request_id = "E2_FACILITY_TEST_20261123_01"

    original_availability = None
    original_status = None
    facility_changed = False

    request = {
        "request_id": request_id,
        "user_id": "U0001",
        "sport": "Football",
        "participants": 20,
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "facility_id": "F001",
        "equipment_id": "E002",
        "equipment_quantity": 5
    }

    try:
        print("\n========== FACILITY AVAILABILITY TEST ==========")

        # STEP 1: Read original facility values
        facility = db.execute(
            text("""
                SELECT availability, facility_status
                FROM facilities
                WHERE facility_id = 'F001'
            """)
        ).mappings().first()

        if facility is None:
            print("TEST CANNOT RUN: F001 not found.")
            return

        original_availability = facility["availability"]
        original_status = facility["facility_status"]

        print("\nOriginal availability:", original_availability)
        print("Original facility status:", original_status)

        # STEP 2: Temporarily mark facility unavailable
        db.execute(
            text("""
                UPDATE facilities
                SET availability = 'Unavailable'
                WHERE facility_id = 'F001'
            """)
        )
        db.commit()
        facility_changed = True

        print("\nFacility F001 temporarily marked Unavailable.")

        # STEP 3: Attempt booking
        print("\nSTEP 1: Attempt booking confirmation")

        result = confirm_booking(db, request)

        print("\n========== RESULT ==========")
        print(result)

        # STEP 4: Verify rejection
        if (
            not result.get("success")
            and result.get("message") ==
            "Selected facility is not available."
        ):
            print("\nTEST RESULT: PASS")
            print("Unavailable facility correctly rejected.")
        else:
            print("\nTEST RESULT: FAIL")
            print("Expected facility availability rejection.")

        # STEP 5: Verify no booking was inserted
        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM bookings
                WHERE request_id = :request_id
            """),
            {"request_id": request_id}
        ).scalar()

        print("\nDatabase records:", count)

        if count == 0:
            print("Database insertion check: PASS")
        else:
            print("Database insertion check: FAIL")

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        # STEP 6: Restore original facility values
        if facility_changed:
            try:
                db.execute(
                    text("""
                        UPDATE facilities
                        SET availability = :availability,
                            facility_status = :status
                        WHERE facility_id = 'F001'
                    """),
                    {
                        "availability": original_availability,
                        "status": original_status
                    }
                )
                db.commit()

                print("\nOriginal facility values restored.")

            except Exception as cleanup_error:
                db.rollback()
                print("\nRESTORATION ERROR:", cleanup_error)
                print("Check F001 availability and status manually.")

        db.close()

    print("\nFACILITY AVAILABILITY TEST COMPLETED!")


if __name__ == "__main__":
    test_facility_validation()

