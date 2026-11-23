
from sqlalchemy import text


def is_facility_time_available(
    db,
    facility_id,
    booking_date,
    start_time,
    end_time
):
    """
    Check availability for the selected facility only.

    Different facilities may have simultaneous bookings.
    Only Confirmed bookings block availability.
    Adjacent intervals are allowed.
    """

    if start_time >= end_time:
        return False

    query = text("""
        SELECT COUNT(*)
        FROM bookings
        WHERE facility_id = :facility_id
          AND booking_date = :booking_date
          AND LOWER(booking_status) = 'confirmed'
          AND TIME(start_time) < TIME(:end_time)
          AND TIME(end_time) > TIME(:start_time)
    """)

    count = db.execute(
        query,
        {
            "facility_id": facility_id,
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
    Detect booking conflicts.

    1. Capacity Conflict
    2. Facility/Resource Conflict
    3. Equipment Conflict

    Facility conflicts are facility-specific.
    Equipment stock is shared across all facilities.
    Only Confirmed bookings block availability.
    """

    conflicts = []

    # Validate the requested interval first.
    if start_time >= end_time:
        conflicts.append({
            "type": "Time-Slot Conflict",
            "message": "End time must be after start time."
        })
        return conflicts

    # 1. Capacity conflict
    capacity = db.execute(
        text("""
            SELECT capacity
            FROM facilities
            WHERE facility_id = :facility_id
        """),
        {"facility_id": facility_id}
    ).scalar()

    if capacity is None or participants > capacity:
        conflicts.append({
            "type": "Capacity Conflict",
            "message": "Facility capacity is insufficient."
        })

    # 2. Facility-specific time conflict
    if not is_facility_time_available(
        db=db,
        facility_id=facility_id,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time
    ):
        conflicts.append({
            "type": "Facility/Resource Conflict",
            "message": "Facility is already booked during this time."
        })

    # 3. Shared equipment conflict
    if equipment_id and equipment_quantity > 0:

        equipment = db.execute(
            text("""
                SELECT
                    e.total_quantity,
                    COALESCE(SUM(b.equipment_quantity), 0)
                        AS reserved_quantity
                FROM equipment e
                LEFT JOIN bookings b
                    ON b.equipment_id = e.equipment_id
                    AND b.booking_date = :booking_date
                    AND LOWER(b.booking_status) = 'confirmed'
                    AND TIME(b.start_time) < TIME(:end_time)
                    AND TIME(b.end_time) > TIME(:start_time)
                WHERE e.equipment_id = :equipment_id
                GROUP BY e.equipment_id, e.total_quantity
            """),
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
