
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_different_facilities_same_time():

    db = SessionLocal()

    first_request_id = "E2_DIFFERENT_FACILITY_FIRST_20261123"
    second_request_id = "E2_DIFFERENT_FACILITY_SECOND_20261123"

    first_booking_id = None
    second_booking_id = None

    try:
        print("\n========== DIFFERENT FACILITIES SAME TIME TEST ==========")

        # STEP 1: First booking - Football

        first_request = {
            "request_id": first_request_id,
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

        print("\nSTEP 1: Confirm first booking")
        print("Facility: F001 - Main Football Ground")
        print("Sport: Football")
        print("Time: 07:00 - 08:00")

        result1 = confirm_booking(db, first_request)
        print(result1)

        if not result1.get("success"):
            print("\nTEST RESULT: FAIL")
            print("First booking could not be confirmed.")
            return

        first_booking_id = result1["booking_id"]

        # STEP 2: Second booking - Basketball
        # Different facility, same date and time.

        second_request = {
            "request_id": second_request_id,
            "user_id": "U0001",
            "sport": "Basketball",
            "participants": 20,
            "booking_date": "2018-01-01",
            "start_time": "07:00",
            "end_time": "08:00",
            "facility_id": "F002",
            "equipment_id": "E001",
            "equipment_quantity": 5
        }

        print("\nSTEP 2: Confirm second booking")
        print("Facility: F002 - Basketball Court 1")
        print("Sport: Basketball")
        print("Time: 07:00 - 08:00")

        result2 = confirm_booking(db, second_request)
        print(result2)

        if result2.get("success"):
            second_booking_id = result2["booking_id"]

        # STEP 3: Verify both bookings succeeded.

        if result1.get("success") and result2.get("success"):
            print("\nTEST RESULT: PASS")
            print("Different facilities can be booked at the same time.")
        else:
            print("\nTEST RESULT: FAIL")
            print("Both bookings were expected to succeed.")

        # STEP 4: Verify both records exist.

        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM bookings
                WHERE request_id IN (
                    :first_request_id,
                    :second_request_id
                )
            """),
            {
                "first_request_id": first_request_id,
                "second_request_id": second_request_id
            }
        ).scalar()

        print("\nTemporary booking records:", count)

        if count == 2:
            print("Database insertion check: PASS")
        else:
            print("Database insertion check: FAIL")

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        # STEP 5: Delete temporary bookings.

        try:
            db.execute(
                text("""
                    DELETE FROM bookings
                    WHERE request_id IN (
                        :first_request_id,
                        :second_request_id
                    )
                """),
                {
                    "first_request_id": first_request_id,
                    "second_request_id": second_request_id
                }
            )

            db.commit()
            print("\nTemporary test bookings deleted.")

        except Exception as cleanup_error:
            db.rollback()
            print("\nCleanup error:", cleanup_error)

        db.close()

    print("\nDIFFERENT FACILITIES SAME TIME TEST COMPLETED!")


if __name__ == "__main__":
    test_different_facilities_same_time()
