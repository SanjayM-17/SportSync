
from app.database.connection import SessionLocal
from app.engines.dsa_engine import find_feasible_options


def main():
    db = SessionLocal()

    try:
        print("\n========== SPORTSYNC INTEGRATED DSA ENGINE ==========")

        # Booking request
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

        # Execute integrated DSA engine
        results = find_feasible_options(
            db,
            request["sport"],
            request["participants"],
            request["booking_date"],
            request["start_time"],
            request["end_time"],
            request["equipment_quantity"]
        )

        print("\n========== FEASIBLE OPTIONS ==========")

        if results:
            for index, option in enumerate(results, start=1):

                facility = option["facility"]

                print(f"\nOPTION {index}")
                print("Facility:", facility["facility_name"])
                print("Sport:", facility["sport_type"])
                print("Capacity:", facility["capacity"])
                print("Location:", facility["location"])

                print("\nSuitable Equipment:")

                for equipment in option["equipment_options"]:
                    print(
                        equipment["equipment_name"],
                        "| Total:", equipment["total_quantity"],
                        "| Available:", equipment["available_quantity"],
                        "| Sport:", equipment["sport"]
                    )

                print("\nAvailable Time Slots:")

                for slot in option["available_time_slots"]:
                    print(
                        "Slot ID:", slot["slot_id"],
                        "| Time:", slot["start_time"],
                        "-", slot["end_time"]
                    )

            print("\nFeasible facility options:", len(results))

        else:
            print("No feasible options found.")

        print("\nINTEGRATED DSA TEST COMPLETED!")

    except Exception as error:
        print("\nERROR:", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
