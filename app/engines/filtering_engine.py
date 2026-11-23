
from sqlalchemy import text


# ==========================================
# 1. GET ACTIVE AND AVAILABLE FACILITIES
# ==========================================

def get_available_facilities(db):

    query = text("""
        SELECT
            facility_id,
            facility_name,
            facility_type,
            sport_type,
            capacity,
            location,
            availability,
            facility_status
        FROM facilities
        WHERE LOWER(availability) = 'available'
          AND LOWER(facility_status) = 'active'
        ORDER BY facility_name
    """)

    return [
        dict(row)
        for row in db.execute(query).mappings()
    ]


# ==========================================
# 2. FILTER FACILITIES BY SPORT
# ==========================================

def filter_by_sport(facilities, sport):

    return [
        facility
        for facility in facilities
        if facility["sport_type"]
        and facility["sport_type"].strip().lower()
        == sport.strip().lower()
    ]


# ==========================================
# 3. FILTER FACILITIES BY CAPACITY
# ==========================================

def filter_by_capacity(facilities, participants):

    if participants <= 0:
        raise ValueError(
            "Participants must be greater than zero."
        )

    return [
        facility
        for facility in facilities
        if facility["capacity"] is not None
        and facility["capacity"] >= participants
    ]


# ==========================================
# 4. GET AVAILABLE TIME SLOTS
#    FACILITY-SPECIFIC AVAILABILITY
# ==========================================

def get_available_time_slots(
    db,
    booking_date,
    start_time=None,
    end_time=None,
    facility_id=None
):
    """
    Return available timeslots.

    Different facilities can use the same timeslot.

    Only confirmed bookings for the selected
    facility block overlapping timeslots.

    Adjacent bookings are allowed.
    """

    if (start_time is None) != (end_time is None):
        raise ValueError(
            "Both start_time and end_time must be provided."
        )

    if start_time is not None and start_time >= end_time:
        raise ValueError(
            "End time must be after start time."
        )

    if facility_id is not None:

        query = text("""
            SELECT
                t.slot_id,
                t.`date`,
                t.start_time,
                t.end_time,
                t.time_slot
            FROM timeslots t
            WHERE t.`date` = :booking_date
              AND LOWER(t.availability_status) = 'available'

              AND (
                    :start_time IS NULL
                    OR (
                        TIME(t.start_time) <= TIME(:start_time)
                        AND TIME(t.end_time) >= TIME(:end_time)
                    )
              )

              AND NOT EXISTS (
                    SELECT 1
                    FROM bookings b
                    WHERE b.facility_id = :facility_id
                      AND b.booking_date = t.`date`
                      AND LOWER(b.booking_status) = 'confirmed'
                      AND TIME(b.start_time) < TIME(t.end_time)
                      AND TIME(b.end_time) > TIME(t.start_time)
              )

            ORDER BY TIME(t.start_time)
        """)

        params = {
            "booking_date": booking_date,
            "facility_id": facility_id,
            "start_time": start_time,
            "end_time": end_time
        }

    else:

        query = text("""
            SELECT
                t.slot_id,
                t.`date`,
                t.start_time,
                t.end_time,
                t.time_slot
            FROM timeslots t
            WHERE t.`date` = :booking_date
              AND LOWER(t.availability_status) = 'available'

              AND (
                    :start_time IS NULL
                    OR (
                        TIME(t.start_time) <= TIME(:start_time)
                        AND TIME(t.end_time) >= TIME(:end_time)
                    )
              )

            ORDER BY TIME(t.start_time)
        """)

        params = {
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }

    result = db.execute(query, params)

    return [
        dict(row)
        for row in result.mappings()
    ]


# ==========================================
# 5. FILTER FACILITIES BY TIME SLOT
# ==========================================

def filter_by_time_slot(
    db,
    facilities,
    booking_date,
    start_time,
    end_time
):

    if start_time >= end_time:
        raise ValueError(
            "End time must be after start time."
        )

    available_facilities = []

    for facility in facilities:

        slots = get_available_time_slots(
            db=db,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            facility_id=facility["facility_id"]
        )

        if slots:
            available_facilities.append(facility)

    return available_facilities


# ==========================================
# 6. FILTER EQUIPMENT BY SPORT AND QUANTITY
#    SHARED CAMPUS-WIDE EQUIPMENT STOCK
# ==========================================

def filter_by_equipment(
    db,
    sport,
    required_quantity,
    booking_date=None,
    start_time=None,
    end_time=None
):

    if required_quantity <= 0:
        raise ValueError(
            "Equipment quantity must be greater than zero."
        )

    if (
        booking_date is None
        or start_time is None
        or end_time is None
    ):
        raise ValueError(
            "Booking date, start time and end time are required."
        )

    if start_time >= end_time:
        raise ValueError(
            "End time must be after start time."
        )

    query = text("""
        SELECT
            e.equipment_id,
            e.equipment_name,
            e.equipment_type,
            e.sport,
            e.total_quantity,
            e.resource_status,

            (
                e.total_quantity -
                COALESCE((
                    SELECT SUM(b.equipment_quantity)
                    FROM bookings b
                    WHERE b.equipment_id = e.equipment_id
                      AND b.booking_date = :booking_date
                      AND LOWER(b.booking_status) = 'confirmed'
                      AND TIME(b.start_time) < TIME(:end_time)
                      AND TIME(b.end_time) > TIME(:start_time)
                ), 0)
            ) AS available_quantity

        FROM equipment e

        WHERE LOWER(e.sport) = LOWER(:sport)
          AND LOWER(e.resource_status) = 'available'

        HAVING available_quantity >= :required_quantity

        ORDER BY e.equipment_name
    """)

    result = db.execute(
        query,
        {
            "sport": sport,
            "required_quantity": required_quantity,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }
    )

    return [
        dict(row)
        for row in result.mappings()
    ]
