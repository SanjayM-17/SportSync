from app.database.connection import SessionLocal
from app.services.booking_service import get_recommended_options

db = SessionLocal()

try:
    print("\n========== SPORTSYNC BOOKING SERVICE TEST ==========")

    request = {
        "sport": "Football",
        "participants": 20,
        "facility_id": "F001",
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "equipment_id": "E002",
        "equipment_quantity": 5
    }

    print("\nBOOKING REQUEST")
    for key, value in request.items():
        print(f"{key}: {value}")

    recommendations = get_recommended_options(db, request)

    print("\n========== FINAL RECOMMENDATIONS ==========")

    if recommendations:
        for index, option in enumerate(recommendations, start=1):
            facility = option["facility"]

            print(f"\nRECOMMENDATION {index}")
            print("Facility:", facility["facility_name"])
            print("Capacity:", facility["capacity"])
            print("Location:", facility["location"])

            print("\nConflict-free Equipment:")
            for equipment in option["equipment_options"]:
                print(
                    equipment["equipment_name"],
                    "| Available:",
                    equipment["available_quantity"]
                )

        print("\nWorkflow completed successfully!")

    else:
        print("\nNo conflict-free options available.")

    print("\nBOOKING SERVICE TEST COMPLETED!")

finally:
    db.close()