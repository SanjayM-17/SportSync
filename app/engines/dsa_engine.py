
from app.engines.filtering_engine import (
    get_available_facilities,
    get_available_time_slots,
    filter_by_sport,
    filter_by_capacity,
    filter_by_equipment
)


# ==========================================
# 1. GET SUITABLE FACILITIES
# ==========================================

def get_suitable_facilities(db, sport, participants):
    """
    Step 1: Filter facilities by sport.
    Step 2: Filter facilities by participant capacity.
    """

    facilities = get_available_facilities(db)

    sport_facilities = filter_by_sport(
        facilities,
        sport
    )

    capacity_facilities = filter_by_capacity(
        sport_facilities,
        participants
    )

    return capacity_facilities


# ==========================================
# 2. GET FREE TIME SLOTS FOR A FACILITY
# ==========================================

def get_free_time_slots(
    db,
    booking_date,
    facility_id=None,
    start_time=None,
    end_time=None
):
    """
    Return available timeslots.

    When facility_id is provided, overlapping
    confirmed bookings at that facility are excluded.

    Different facilities can use the same timeslot.
    """

    return get_available_time_slots(
        db=db,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        facility_id=facility_id
    )


# ==========================================
# 3. GET AVAILABLE EQUIPMENT
# ==========================================

def get_available_equipment(
    db,
    sport,
    booking_date,
    start_time,
    end_time,
    equipment_quantity=1
):
    """
    Return compatible equipment.

    Equipment stock is shared across all facilities.
    """

    return filter_by_equipment(
        db=db,
        sport=sport,
        required_quantity=equipment_quantity,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    )


# ==========================================
# 4. FIND FEASIBLE BOOKING OPTIONS
# ==========================================

def find_feasible_options(
    db,
    sport,
    participants,
    booking_date,
    start_time,
    end_time,
    equipment_quantity=1
):
    """
    Progressive filtering:

    SPORT
       |
    PARTICIPANTS
       |
    FACILITY
       |
    FACILITY-SPECIFIC TIMESLOT
       |
    SHARED EQUIPMENT
       |
    FEASIBLE OPTIONS

    This function does not automatically book
    or select resources.
    """

    if start_time >= end_time:
        raise ValueError(
            "End time must be after start time."
        )

    if participants <= 0:
        raise ValueError(
            "Participants must be greater than zero."
        )

    if equipment_quantity <= 0:
        raise ValueError(
            "Equipment quantity must be greater than zero."
        )

    # STEP 1: Filter facilities by sport and capacity

    facilities = get_suitable_facilities(
        db,
        sport,
        participants
    )

    if not facilities:
        return []

    # STEP 2: Filter each facility by its own availability

    equipment_options = get_available_equipment(
        db=db,
        sport=sport,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        equipment_quantity=equipment_quantity
    )

    if not equipment_options:
        return []

    feasible_options = []

    for facility in facilities:

        available_slots = get_free_time_slots(
            db=db,
            booking_date=booking_date,
            facility_id=facility["facility_id"],
            start_time=start_time,
            end_time=end_time
        )

        if not available_slots:
            continue

        feasible_options.append({
            "facility": facility,
            "equipment_options": equipment_options,
            "available_time_slots": available_slots
        })

    return feasible_options
