
from sqlalchemy import text


def is_campus_time_available(
    db,
    booking_date,
    start_time,
    end_time
):
    """
    Check whether the requested time interval is free
    across the entire campus.

    Only Confirmed bookings block availability.
    """

    if start_time >= end_time:
        return False

    query = text("""
        SELECT COUNT(*)
        FROM bookings
        WHERE booking_date = :booking_date
          AND LOWER(booking_status) = 'confirmed'
          AND start_time < :end_time
          AND end_time > :start_time
    """)

    count = db.execute(
        query,
        {
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }
    ).scalar()

    return count == 0


def detect_conflicts(
    db,
    sport,
    participants,
    facility_id,
    booking_date,
    start_time,
    end_time,
    equipment_id=None,
    equipment_quantity=0
):
    """
    Detect resource conflicts.

    Time-slot availability is handled separately through
    is_campus_time_available().

    Conflict types:
    1. Capacity Conflict
    2. Facility/Resource Conflict
    3. Equipment Conflict
    """

    conflicts = []

    # 1. CAPACITY CONFLICT
    capacity_query = text("""
        SELECT capacity
        FROM facilities
        WHERE facility_id = :facility_id
    """)

    capacity = db.execute(
        capacity_query,
        {"facility_id": facility_id}
    ).scalar()

    if capacity is None or participants > capacity:
        conflicts.append({
            "type": "Capacity Conflict",
            "message": "Facility capacity is insufficient."
        })

    # 2. FACILITY/RESOURCE CONFLICT
    facility_query = text("""
        SELECT COUNT(*)
        FROM bookings
        WHERE facility_id = :facility_id
          AND booking_date = :booking_date
          AND LOWER(booking_status) = 'confirmed'
          AND start_time < :end_time
          AND end_time > :start_time
    """)

    facility_conflicts = db.execute(
        facility_query,
        {
            "facility_id": facility_id,
            "booking_date": booking_date,
            "start_time": start_time,
            "end_time": end_time
        }
    ).scalar()

    if facility_conflicts > 0:
        conflicts.append({
            "type": "Facility/Resource Conflict",
            "message": "Facility is already booked during this time."
        })

    # 3. EQUIPMENT CONFLICT
    if equipment_id and equipment_quantity > 0:

        equipment_query = text("""
            SELECT
                e.total_quantity,
                COALESCE(SUM(b.equipment_quantity), 0)
                    AS reserved_quantity
            FROM equipment e
            LEFT JOIN bookings b
                ON b.equipment_id = e.equipment_id
                AND b.booking_date = :booking_date
                AND LOWER(b.booking_status) = 'confirmed'
                AND b.start_time < :end_time
                AND b.end_time > :start_time
            WHERE e.equipment_id = :equipment_id
            GROUP BY e.equipment_id, e.total_quantity
        """)

        equipment = db.execute(
            equipment_query,
            {
                "equipment_id": equipment_id,
                "booking_date": booking_date,
                "start_time": start_time,
                "end_time": end_time
            }
        ).mappings().first()

        if equipment is None or (
            equipment["total_quantity"]
            - equipment["reserved_quantity"]
            < equipment_quantity
        ):
            conflicts.append({
                "type": "Equipment Conflict",
                "message": "Insufficient equipment available."
            })

    return conflicts
