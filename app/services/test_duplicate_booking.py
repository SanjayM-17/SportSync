
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_duplicate_booking():

    db = SessionLocal()

    request_id = "E2_DUPLICATE_TEST_20261123_01"
    created_booking_id = None

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
        print("\n========== DUPLICATE BOOKING TEST ==========")

        # STEP 1: Submit the first booking request.

        print("\nSTEP 1: First booking request")

        result1 = confirm_booking(db, request)
        print(result1)

        if not result1.get("success"):
            print("\nTEST RESULT: FAIL")
            print("First booking failed:", result1.get("message"))
            return

        created_booking_id = result1["booking_id"]

        # STEP 2: Submit exactly the same request again.

        print("\nSTEP 2: Submit the same request again")

        result2 = confirm_booking(db, request)
        print(result2)

        # STEP 3: Verify idempotency.

        if (
            result2.get("success")
            and result1["booking_id"] == result2["booking_id"]
        ):
            print("\nIDEMPOTENCY CHECK: PASS")
            print("Same booking ID returned for both requests.")
            print("Duplicate booking was prevented.")

        else:
            print("\nIDEMPOTENCY CHECK: FAIL")
            print("Duplicate request handling failed.")

        # STEP 4: Verify only one database record exists.

        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM bookings
                WHERE request_id = :request_id
            """),
            {"request_id": request_id}
        ).scalar()

        print("\nDatabase records for this request ID:", count)

        if count == 1:
            print("DATABASE DUPLICATE CHECK: PASS")
        else:
            print("DATABASE DUPLICATE CHECK: FAIL")

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        # STEP 5: Delete only the temporary booking.

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

        except Exception as cleanup_error:
            db.rollback()
            print("\nCleanup error:", cleanup_error)

        db.close()

    print("\nDUPLICATE BOOKING TEST COMPLETED!")


if __name__ == "__main__":
    test_duplicate_booking()
