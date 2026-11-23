
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_equipment_validation():

    db = SessionLocal()

    request_id = "E2_EQUIPMENT_TEST_20261123_01"

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
        "equipment_quantity": 20
    }

    try:
        print("\n========== EQUIPMENT VALIDATION TEST ==========")

        print("\nBOOKING REQUEST")
        for key, value in request.items():
            print(f"{key}: {value}")

        # Step 1: Attempt booking confirmation
        result = confirm_booking(db, request)

        print("\n========== RESULT ==========")
        print(result)

        # Step 2: Verify equipment conflict rejection
        conflicts = result.get("conflicts", [])

        equipment_conflict = any(
            conflict.get("type") == "Equipment Conflict"
            for conflict in conflicts
        )

        if not result.get("success") and equipment_conflict:
            print("\nTEST RESULT: PASS")
            print("Insufficient equipment correctly rejected.")
        else:
            print("\nTEST RESULT: FAIL")
            print("Expected equipment conflict was not detected.")

        # Step 3: Verify no booking was inserted
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
        db.close()

    print("\nEQUIPMENT VALIDATION TEST COMPLETED!")


if __name__ == "__main__":
    test_equipment_validation()
