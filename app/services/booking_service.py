
from sqlalchemy import text

from app.engines.dsa_engine import (
    get_suitable_facilities,
    get_free_time_slots,
    get_available_equipment
)

from app.engines.conflict_engine import (
    detect_conflicts,
    is_facility_time_available
)

from app.engines.recommendation_engine import recommend_options


# ==========================================
# 1. GET AVAILABLE SPORTS
# ==========================================

def get_sports(db):
    """Return available sports."""

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


# ==========================================
# 2. GET SUITABLE FACILITIES
# ==========================================

def get_facilities(db, sport, participants):
    """Return facilities matching sport and capacity."""

    return get_suitable_facilities(
        db,
        sport,
        participants
    )


# ==========================================
# 3. GET AVAILABLE TIMESLOTS
# ==========================================

def get_timeslots(
    db,
    booking_date,
    facility_id=None,
    start_time=None,
    end_time=None
):
    """
    Return timeslots.

    Pass facility_id to check availability
    specifically for the selected facility.
    """

    return get_free_time_slots(
        db=db,
        booking_date=booking_date,
        facility_id=facility_id,
        start_time=start_time,
        end_time=end_time
    )


# ==========================================
# 4. GET AVAILABLE EQUIPMENT
# ==========================================

def get_equipment(
    db,
    sport,
    booking_date,
    start_time,
    end_time,
    equipment_quantity=1
):
    """Return compatible equipment with shared stock availability."""

    return get_available_equipment(
        db=db,
        sport=sport,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        equipment_quantity=equipment_quantity
    )


# ==========================================
# 5. VALIDATE USER SELECTIONS
# ==========================================

def get_recommended_options(db, request):
    """
    Validate the user's actual selections.

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
    QUANTITY
       |
    REVIEW

    This function validates selections only.
    It does not create a booking.
    """

    # ==========================================
    # STEP 1: VALIDATE FACILITY
    # ==========================================

    facilities = get_suitable_facilities(
        db,
        request["sport"],
        request["participants"]
    )

    selected_facility = next(
        (
            facility
            for facility in facilities
            if str(facility["facility_id"])
            == str(request["facility_id"])
        ),
        None
    )

    if not selected_facility:
        return []

    # ==========================================
    # STEP 2: VALIDATE FACILITY TIMESLOT
    # ==========================================

    if not is_facility_time_available(
        db,
        request["facility_id"],
        request["booking_date"],
        request["start_time"],
        request["end_time"]
    ):
        return []

    free_slots = get_free_time_slots(
        db=db,
        booking_date=request["booking_date"],
        facility_id=request["facility_id"],
        start_time=request["start_time"],
        end_time=request["end_time"]
    )

    selected_slot = next(
        (
            slot
            for slot in free_slots
            if str(slot["start_time"])[:5]
            <= str(request["start_time"])[:5]
            and str(slot["end_time"])[:5]
            >= str(request["end_time"])[:5]
        ),
        None
    )

    if not selected_slot:
        return []

    # ==========================================
    # STEP 3: VALIDATE SHARED EQUIPMENT
    # ==========================================

    equipment_options = get_available_equipment(
        db=db,
        sport=request["sport"],
        booking_date=request["booking_date"],
        start_time=request["start_time"],
        end_time=request["end_time"],
        equipment_quantity=request["equipment_quantity"]
    )

    selected_equipment = next(
        (
            equipment
            for equipment in equipment_options
            if str(equipment["equipment_id"])
            == str(request["equipment_id"])
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

    # ==========================================
    # STEP 4: FINAL CONFLICT VALIDATION
    # ==========================================

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

    # ==========================================
    # STEP 5: RETURN SELECTED OPTIONS
    # ==========================================

    feasible_options = [{
        "facility": selected_facility,
        "equipment_options": [selected_equipment],
        "available_time_slots": [selected_slot]
    }]

    return recommend_options(feasible_options)
