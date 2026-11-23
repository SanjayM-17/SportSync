
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_transaction_rollback():

    db = SessionLocal()

    first_request_id = "E2_ROLLBACK_FIRST_20261123_01"
    second_request_id = "E2_ROLLBACK_SECOND_20261123_01"

    first_booking_id = None

    try:
        print("\n========== FACILITY CONFLICT / ROLLBACK CHECK ==========")

        # STEP 1: Create a valid first booking.

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

        print("\nSTEP 1: Create first booking")

        result1 = confirm_booking(db, first_request)
        print(result1)

        if not result1.get("success"):
            print("\nTEST RESULT: FAIL")
            print("Could not create the first booking.")
            return

        first_booking_id = result1["booking_id"]

        # STEP 2: Attempt another booking at the SAME facility
        # with an overlapping time interval.

        second_request = {
            "request_id": second_request_id,
            "user_id": "U0001",
            "sport": "Football",
            "participants": 20,
            "booking_date": "2018-01-01",
            "start_time": "07:30",
            "end_time": "08:30",
            "facility_id": "F001",
            "equipment_id": "E002",
            "equipment_quantity": 5
        }

        print("\nSTEP 2: Submit overlapping booking")
        print("Facility: F001")
        print("First booking: 07:00 - 08:00")
        print("Second booking: 07:30 - 08:30")

        result2 = confirm_booking(db, second_request)
        print(result2)

        # STEP 3: Verify facility conflict rejection.

        if (
            not result2.get("success")
            and "facility" in result2.get("message", "").lower()
        ):
            print("\nCONFLICT CHECK: PASS")
            print("Overlapping booking at the same facility was rejected.")

        elif not result2.get("success"):
            print("\nCONFLICT CHECK: PASS")
            print("Second booking was rejected.")
            print("Rejection reason:", result2.get("message"))

        else:
            print("\nCONFLICT CHECK: FAIL")
            print("Expected the overlapping booking to be rejected.")

        # STEP 4: Verify no second booking record exists.

        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM bookings
                WHERE request_id = :request_id
            """),
            {"request_id": second_request_id}
        ).scalar()

        print("\nSecond booking database records:", count)

        if count == 0:
            print("DATABASE CHECK: PASS")
            print("No second booking record was inserted.")
        else:
            print("DATABASE CHECK: FAIL")
            print("Unexpected second booking record found.")

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        # STEP 5: Remove temporary test bookings.

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

    print("\nFACILITY CONFLICT TEST COMPLETED!")


if __name__ == "__main__":
    test_transaction_rollback()
