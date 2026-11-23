
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_invalid_booking():

    db = SessionLocal()

    request_id = "E2_INVALID_TEST_20261123_01"

    request = {
        "request_id": request_id,
        "user_id": "U0001",
        "sport": "Football",
        "participants": 100,
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "facility_id": "F001",
        "equipment_id": "E002",
        "equipment_quantity": 5
    }

    try:
        print("\n========== INVALID BOOKING TEST ==========")

        print("\nBOOKING REQUEST")
        for key, value in request.items():
            print(f"{key}: {value}")

        # Attempt booking
        result = confirm_booking(db, request)

        print("\n========== RESULT ==========")
        print(result)

        # Verify rejection
        if not result.get("success"):
            print("\nTEST RESULT: PASS")
            print("Invalid booking correctly rejected.")
            print("Reason:", result.get("message"))
        else:
            print("\nTEST RESULT: FAIL")
            print("Invalid booking was unexpectedly confirmed.")

        # Verify no booking record was inserted
        count = db.execute(
            text("""
                SELECT COUNT(*)
                FROM bookings
                WHERE request_id = :request_id
            """),
            {"request_id": request_id}
        ).scalar()

        print("\nDatabase records for this request ID:", count)

        if count == 0:
            print("Database insertion check: PASS")
        else:
            print("Database insertion check: FAIL")

    except Exception as error:
        db.rollback()
        print("\nTEST EXECUTION ERROR:", error)

    finally:
        db.close()

    print("\nINVALID BOOKING TEST COMPLETED!")


if __name__ == "__main__":
    test_invalid_booking()
