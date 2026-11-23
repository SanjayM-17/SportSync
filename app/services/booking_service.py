
from app.engines.dsa_engine import (
    get_suitable_facilities,
    get_free_time_slots,
    get_available_equipment
)

from app.engines.conflict_engine import (
    detect_conflicts,
    is_campus_time_available
)

from app.engines.recommendation_engine import recommend_options


def get_sports(db):
    """Step 1: Return available sports."""

    from sqlalchemy import text

    query = text("""
        SELECT DISTINCT sport_type
        FROM facilities
        WHERE LOWER(availability) = 'available'
          AND LOWER(facility_status) = 'active'
        ORDER BY sport_type
    """)

    return [
        row["sport_type"]
        for row in db.execute(query).mappings()
    ]


def get_facilities(db, sport, participants):
    """Steps 2 and 3: Return suitable facilities."""

    return get_suitable_facilities(
        db,
        sport,
        participants
    )


def get_timeslots(db, booking_date):
    """Step 4: Return free campus-wide timeslots."""

    return get_free_time_slots(
        db,
        booking_date
    )


def get_equipment(
    db,
    sport,
    booking_date,
    start_time,
    end_time
):
    """Step 5: Return compatible and available equipment."""

    return get_available_equipment(
        db,
        sport,
        booking_date,
        start_time,
        end_time
    )


def get_recommended_options(db, request):
    """
    Validate the user's actual selections.

    SPORT -> PARTICIPANTS -> FACILITY -> TIMESLOT
    -> EQUIPMENT -> QUANTITY -> REVIEW

    This function validates selections only.
    It does not create a booking.
    """

    # Step 1: Validate selected facility and participant capacity.

    facilities = get_suitable_facilities(
        db,
        request["sport"],
        request["participants"]
    )

    selected_facility = next(
        (
            facility for facility in facilities
            if facility["facility_id"] == request["facility_id"]
        ),
        None
    )

    if not selected_facility:
        return []

    # Step 2: Validate the selected timeslot.

    free_slots = get_free_time_slots(
        db,
        request["booking_date"]
    )

    selected_slot = next(
    (
        slot for slot in free_slots
        if str(slot["start_time"])[:5] == str(request["start_time"])[:5]
        and str(slot["end_time"])[:5] == str(request["end_time"])[:5]
    ),
    None
)

    if not selected_slot:
        return []

    # Recheck campus-wide availability.

    if not is_campus_time_available(
        db,
        request["booking_date"],
        request["start_time"],
        request["end_time"]
    ):
        return []

    # Step 3: Validate selected equipment and stock quantity.

    equipment_options = get_available_equipment(
        db,
        request["sport"],
        request["booking_date"],
        request["start_time"],
        request["end_time"]
    )

    selected_equipment = next(
        (
            equipment for equipment in equipment_options
            if equipment["equipment_id"] == request["equipment_id"]
        ),
        None
    )

    if not selected_equipment:
        return []

    if (
        request["equipment_quantity"] <= 0
        or request["equipment_quantity"]
        > selected_equipment["available_quantity"]
    ):
        return []

    # Step 4: Run final conflict checks for the selected resources.

    conflicts = detect_conflicts(
        db=db,
        sport=request["sport"],
        participants=request["participants"],
        facility_id=request["facility_id"],
        booking_date=request["booking_date"],
        start_time=request["start_time"],
        end_time=request["end_time"],
        equipment_id=request["equipment_id"],
        equipment_quantity=request["equipment_quantity"]
    )

    if conflicts:
        return []

    # Step 5: Return only the user's selected facility and equipment.

    feasible_options = [{
        "facility": selected_facility,
        "equipment_options": [selected_equipment]
    }]

    return recommend_options(feasible_options)
