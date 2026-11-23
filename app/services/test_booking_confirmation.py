
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_successful_booking():

    db = SessionLocal()

    request_id = "E2_SUCCESS_TEST_20261123_01"

    print("\n========== BOOKING CONFIRMATION TEST ==========")

    try:
        # STEP 1: Prepare booking request.

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

        print("\nBOOKING REQUEST")

        for key, value in request.items():
            print(f"{key}: {value}")

        # STEP 2: Confirm booking.

        result = confirm_booking(db, request)

        print("\n========== RESULT ==========")
        print(result)

        # STEP 3: Verify result.

        if result.get("success"):

            print("\nTEST RESULT: PASS")
            print("Booking ID:", result["booking_id"])
            print("Booking Status:", result["booking_status"])

        else:
            print("\nTEST RESULT: FAIL")
            print("Reason:", result.get("message"))

            if result.get("error"):
                print("Error:", result["error"])

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        # STEP 4: Remove only this test booking.

        try:
            db.execute(
                text("""
                    DELETE FROM bookings
                    WHERE request_id = :request_id
                """),
                {"request_id": request_id}
            )

            db.commit()

            print("\nTemporary test booking deleted.")
            print("Original dataset preserved.")

        except Exception as cleanup_error:
            db.rollback()
            print("\nCleanup error:", cleanup_error)

        db.close()

    print("\nBOOKING CONFIRMATION TEST COMPLETED!")


if __name__ == "__main__":
    test_successful_booking()
