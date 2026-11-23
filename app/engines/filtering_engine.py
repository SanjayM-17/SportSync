
from sqlalchemy import text


# 1. Get active and available facilities
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
    """)

    return [
        dict(row)
        for row in db.execute(query).mappings()
    ]


# 2. Filter facilities by sport
def filter_by_sport(facilities, sport):
    return [
        facility for facility in facilities
        if facility["sport_type"]
        and facility["sport_type"].strip().lower()
        == sport.strip().lower()
    ]


# 3. Filter facilities by participant capacity
def filter_by_capacity(facilities, participants):
    if participants <= 0:
        raise ValueError("Participants must be greater than zero.")

    return [
        facility for facility in facilities
        if facility["capacity"] >= participants
    ]


# 4. Get free campus-wide timeslots
def get_available_time_slots(
    db, booking_date, start_time=None, end_time=None
):
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
          AND NOT EXISTS (
              SELECT 1
              FROM bookings b
              WHERE b.booking_date = t.`date`
                AND LOWER(b.booking_status) = 'confirmed'
                AND b.start_time < t.end_time
                AND b.end_time > t.start_time
          )
          AND (
              :start_time IS NULL
              OR (
                  t.start_time <= :start_time
                  AND t.end_time >= :end_time
              )
          )
        ORDER BY t.start_time
    """)

    result = db.execute(
        query,
        {
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }
    )

    return [dict(row) for row in result.mappings()]


# 5. Filter facilities by campus-wide timeslot availability
def filter_by_time_slot(
    db, facilities, booking_date, start_time, end_time
):
    if start_time >= end_time:
        raise ValueError("End time must be after start time.")

    available_slots = get_available_time_slots(
        db,
        booking_date,
        start_time,
        end_time
    )

    if not available_slots:
        return []

    return facilities


# 6. Filter equipment by sport and available quantity
def filter_by_equipment(
    db,
    sport,
    required_quantity,
    booking_date=None,
    start_time=None,
    end_time=None
):
    if required_quantity <= 0:
        raise ValueError("Equipment quantity must be greater than zero.")

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
                      AND b.start_time < :end_time
                      AND b.end_time > :start_time
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

    return [dict(row) for row in result.mappings()]
