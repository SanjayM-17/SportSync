
from app.database.connection import SessionLocal
from app.services.booking_service import get_recommended_options


db = SessionLocal()

try:
    print("\n========== SPORTSYNC BOOKING SERVICE TEST ==========")

    # Sample booking request
    request = {
        "sport": "Football",
        "participants": 20,
        "booking_date": "2018-01-01",
        "start_time": "07:00",
        "end_time": "08:00",
        "equipment_quantity": 5
    }

    print("\nBOOKING REQUEST")

    for key, value in request.items():
        print(f"{key}: {value}")

    # Run complete workflow
    recommendations = get_recommended_options(
        db,
        request
    )

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
                    "| Available:", equipment["quantity_available"]
                )

        print("\nWorkflow completed successfully!")

    else:
        print("\nNo conflict-free options available.")

    print("\nBOOKING SERVICE TEST COMPLETED!")

finally:
    db.close()

