
from app.engines.filtering_engine import (
    get_available_facilities,
    get_available_time_slots,
    filter_by_sport,
    filter_by_capacity,
    filter_by_equipment
)


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


def get_free_time_slots(db, booking_date):
    """
    Return only free campus-wide timeslots.
    """

    return get_available_time_slots(
        db,
        booking_date
    )


def get_available_equipment(
    db,
    sport,
    booking_date,
    start_time,
    end_time
):
    """
    Return compatible equipment for the selected sport
    and timeslot. Quantity is selected by the user later.
    """

    return filter_by_equipment(
        db=db,
        sport=sport,
        required_quantity=1,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    )


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
    Complete filtering:
    SPORT -> PARTICIPANTS -> FACILITY
    -> TIMESLOT -> EQUIPMENT -> QUANTITY

    Does not automatically book or select resources.
    """

    if start_time >= end_time:
        raise ValueError("End time must be after start time.")

    facilities = get_suitable_facilities(
        db,
        sport,
        participants
    )

    available_slots = get_available_time_slots(
        db,
        booking_date,
        start_time,
        end_time
    )

    if not available_slots:
        return []

    equipment_options = filter_by_equipment(
        db,
        sport,
        equipment_quantity,
        booking_date,
        start_time,
        end_time
    )

    if not facilities or not equipment_options:
        return []

    return [
        {
            "facility": facility,
            "equipment_options": equipment_options,
            "available_time_slots": available_slots
        }
        for facility in facilities
    ]
          