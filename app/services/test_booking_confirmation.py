
from app.database.connection import SessionLocal
from app.services.booking_confirmation import confirm_booking
from sqlalchemy import text


def test_successful_booking():

    db = SessionLocal()

    try:
        request = {
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

        print("\n========== BOOKING CONFIRMATION TEST ==========")
        print("User ID: U0001")
        print("Facility: F001 - Main Football Ground")
        print("Equipment: E002 - Football")
        print("Participants: 20")
        print("Date: 2018-01-01")
        print("Time: 07:00 - 08:00")
        print("Equipment Quantity: 5")

        result = confirm_booking(db, request)

        print("\n========== RESULT ==========")
        print(result)

        if result["success"]:

            print("\nTEST RESULT: PASS")

            db.execute(
                text("""
                    DELETE FROM bookings
                    WHERE booking_id = :booking_id
                """),
                {"booking_id": result["booking_id"]}
            )

            db.commit()

            print("Temporary test booking deleted.")
            print("Original dataset preserved.")

        else:
            print("\nTEST RESULT: FAILED")
            print("Reason:", result["message"])

    finally:
        db.close()


if __name__ == "__main__":
    test_successful_booking()
