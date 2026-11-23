
from app.database.connection import SessionLocal

from app.engines.dsa_engine import (
    get_suitable_facilities,
    get_free_time_slots,
    get_available_equipment
)

from app.engines.conflict_engine import (
    is_facility_time_available,
    detect_conflicts
)

db = SessionLocal()

sport = "Football"
participants = 12
facility_id = "F001"
booking_date = "2018-01-01"
start_time = "10:00:00"
end_time = "11:00:00"
equipment_id = "E002"
equipment_quantity = 5

try:
    print("\n1. FACILITY VALIDATION")

    facilities = get_suitable_facilities(
        db, sport, participants
    )

    print("Facilities:", facilities)

    selected_facility = next(
        (
            f for f in facilities
            if f["facility_id"] == facility_id
        ),
        None
    )

    print("Selected facility:", selected_facility)

    print("\n2. FACILITY-SPECIFIC TIMESLOT VALIDATION")

    slots = get_free_time_slots(
        db,
        booking_date,
        facility_id=facility_id
    )

    print("Number of available slots:", len(slots))

    for slot in slots:
        print("Available slot:", slot)

    selected_slot = next(
        (
            slot for slot in slots
            if str(slot["start_time"])[:5] == start_time[:5]
            and str(slot["end_time"])[:5] == end_time[:5]
        ),
        None
    )

    print("Selected slot:", selected_slot)

    print("\n3. FACILITY AVAILABILITY")

    facility_available = is_facility_time_available(
        db,
        facility_id,
        booking_date,
        start_time,
        end_time
    )

    print("Facility available:", facility_available)

    print("\n4. EQUIPMENT VALIDATION")

    equipment = get_available_equipment(
        db,
        sport,
        booking_date,
        start_time,
        end_time,
        equipment_quantity=equipment_quantity
    )

    print("Equipment:", equipment)

    selected_equipment = next(
        (
            e for e in equipment
            if e["equipment_id"] == equipment_id
        ),
        None
    )

    print("Selected equipment:", selected_equipment)

    print("\n5. CONFLICT VALIDATION")

    if selected_facility and selected_equipment:

        conflicts = detect_conflicts(
            db=db,
            sport=sport,
            participants=participants,
            facility_id=facility_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            equipment_id=equipment_id,
            equipment_quantity=equipment_quantity
        )

        print("Conflicts:", conflicts)

    else:
        print("Facility or equipment selection is invalid.")

finally:
    db.close()
