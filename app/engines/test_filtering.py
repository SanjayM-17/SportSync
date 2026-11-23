
from app.database.connection import SessionLocal

from app.engines.filtering_engine import (
    get_available_facilities,
    filter_by_sport,
    filter_by_capacity,
    filter_by_time_slot,
    filter_by_equipment
)


db = SessionLocal()

try:
    print("\n========== SPORTSYNC DSA ENGINE ==========")

    # STEP 1: Get available facilities
    facilities = get_available_facilities(db)

    print("\nSTEP 1: AVAILABLE FACILITIES")
    print("Total available facilities:", len(facilities))

    # STEP 2: Filter by sport
    sport_results = filter_by_sport(
        facilities,
        "Football"
    )

    print("\nSTEP 2: SPORT FILTERING")

    for facility in sport_results:
        print(facility["facility_name"])

    # STEP 3: Filter by capacity
    capacity_results = filter_by_capacity(
        sport_results,
        20
    )

    print("\nSTEP 3: CAPACITY FILTERING")

    for facility in capacity_results:
        print(
            facility["facility_name"],
            "| Capacity:", facility["capacity"],
            "| Location:", facility["location"]
        )

    # STEP 4: Filter by date and time
    time_results = filter_by_time_slot(
        db,
        capacity_results,
        "2018-01-01",
        "07:00",
        "08:00"
    )

    print("\nSTEP 4: TIME-SLOT FILTERING")

    for facility in time_results:
        print(
            facility["facility_name"],
            "| Capacity:", facility["capacity"],
            "| Location:", facility["location"]
        )

    # STEP 5: Filter equipment
    equipment_results = filter_by_equipment(
        db,
        "Football",
        5
    )

    print("\nSTEP 5: EQUIPMENT FILTERING")

    for item in equipment_results:
        print(
            item["equipment_name"],
            "| Available:", item["quantity_available"],
            "| Sport:", item["sport"]
        )

    # Final result
    print("\n========== DSA TEST SUMMARY ==========")
    print("Available facilities:", len(facilities))
    print("Sport matches:", len(sport_results))
    print("Capacity matches:", len(capacity_results))
    print("Time-slot matches:", len(time_results))
    print("Equipment matches:", len(equipment_results))

    print("\nDSA FILTERING TEST COMPLETED!")

except Exception as error:
    print("\nERROR:", error)

finally:
    db.close()
