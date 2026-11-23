
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from uuid import uuid4

from app.engines.conflict_engine import (
    detect_conflicts,
    is_facility_time_available
)

from app.engines.os_engine import get_resource_manager


# Shared OS resource manager
resource_manager = get_resource_manager()


def normalize_time(value):
    """Normalize HH:MM and HH:MM:SS into HH:MM."""

    value = str(value)

    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue

    raise ValueError(
        "Invalid time format. Use HH:MM or HH:MM:SS."
    )


def get_existing_booking(db, request_id):
    """Find a previously processed booking."""

    return db.execute(
        text("""
            SELECT
                b.booking_id,
                b.request_id,
                b.user_id,
                b.sport,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.participants,
                b.equipment_id,
                b.equipment_quantity,
                b.facility_id,
                b.facility_name,
                b.booking_status,
                e.equipment_name
            FROM bookings b
            LEFT JOIN equipment e
                ON b.equipment_id = e.equipment_id
            WHERE b.request_id = :request_id
        """),
        {"request_id": request_id}
    ).mappings().first()


def same_request(existing, request):
    """Check whether a repeated request has identical details."""

    return (
        existing["user_id"] == request["user_id"]

        and existing["sport"].lower()
        == request["sport"].lower()

        and str(existing["booking_date"])
        == str(request["booking_date"])

        and normalize_time(existing["start_time"])
        == normalize_time(request["start_time"])

        and normalize_time(existing["end_time"])
        == normalize_time(request["end_time"])

        and existing["participants"]
        == request["participants"]

        and existing["equipment_id"]
        == request["equipment_id"]

        and existing["equipment_quantity"]
        == request["equipment_quantity"]

        and existing["facility_id"]
        == request["facility_id"]
    )


def existing_booking_response(existing, request):
    """Return an existing booking without creating another record."""

    if not same_request(existing, request):
        return {
            "success": False,
            "message": (
                "Request ID has already been used "
                "for different booking details."
            )
        }

    return {
        "success": True,
        "message": "This request has already been processed.",
        "booking_id": existing["booking_id"],
        "facility": existing["facility_name"],
        "equipment": existing["equipment_name"],
        "booking_status": existing["booking_status"]
    }


def confirm_booking(db, request):
    """
    Final SportSync booking confirmation.

    OS ENGINE:
        Facility-specific mutex.
        Equipment-specific mutex.

    DBMS ENGINE:
        READ COMMITTED isolation.
        Facility row locking.
        Equipment row locking.
        Duplicate request prevention.
        Atomic transaction.

    BOOKING RULES:
        Different facilities can be booked at the same time.
        The same facility cannot have overlapping confirmed bookings.
        Shared equipment stock is checked across all facilities.
        Only Confirmed bookings block availability.
    """

    try:

        # ==========================================
        # STEP 1: VALIDATE REQUEST
        # ==========================================

        request_id = request.get("request_id")

        if not request_id or len(request_id) > 64:
            return {
                "success": False,
                "message": "A valid request ID is required."
            }

        required_fields = [
            "user_id",
            "sport",
            "booking_date",
            "start_time",
            "end_time",
            "participants",
            "facility_id",
            "equipment_id",
            "equipment_quantity"
        ]

        for field in required_fields:
            if field not in request or request[field] is None:
                return {
                    "success": False,
                    "message": f"Missing required field: {field}"
                }

        start_time = normalize_time(request["start_time"])
        end_time = normalize_time(request["end_time"])

        if start_time >= end_time:
            return {
                "success": False,
                "message": "End time must be after start time."
            }

        if request["participants"] <= 0:
            return {
                "success": False,
                "message": "Participants must be greater than zero."
            }

        if request["equipment_quantity"] <= 0:
            return {
                "success": False,
                "message": "Equipment quantity must be greater than zero."
            }

        # ==========================================
        # STEP 2: OS MUTEX SYNCHRONIZATION
        # ==========================================

        # No campus-global mutex.
        # Different facilities can process bookings concurrently.
        # Requests sharing a facility or equipment are synchronized.

        resource_ids = [
            "facility:" + str(request["facility_id"]),
            "equipment:" + str(request["equipment_id"])
        ]

        with resource_manager.acquire_resources(resource_ids):

            # ==========================================
            # STEP 3: SET DATABASE ISOLATION
            # ==========================================

            db.execute(
                text(
                    "SET TRANSACTION ISOLATION LEVEL READ COMMITTED"
                )
            )

            # ==========================================
            # STEP 4: DUPLICATE REQUEST CHECK
            # ==========================================

            existing = get_existing_booking(
                db,
                request_id
            )

            if existing:
                result = existing_booking_response(
                    existing,
                    {
                        **request,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                )

                db.rollback()
                return result

            # ==========================================
            # STEP 5: VALIDATE USER
            # ==========================================

            user = db.execute(
                text("""
                    SELECT user_id
                    FROM users
                    WHERE user_id = :user_id
                """),
                {
                    "user_id": request["user_id"]
                }
            ).first()

            if user is None:
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected user does not exist."
                }

            # ==========================================
            # STEP 6: LOCK AND VALIDATE FACILITY
            # ==========================================

            facility = db.execute(
                text("""
                    SELECT
                        facility_id,
                        facility_name,
                        location,
                        capacity,
                        availability,
                        facility_status,
                        sport_type
                    FROM facilities
                    WHERE facility_id = :facility_id
                    FOR UPDATE
                """),
                {
                    "facility_id": request["facility_id"]
                }
            ).mappings().first()

            if facility is None:
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected facility does not exist."
                }

            if (
                str(facility["availability"]).lower() != "available"
                or str(facility["facility_status"]).lower() != "active"
            ):
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected facility is not available."
                }

            if facility["capacity"] < request["participants"]:
                db.rollback()

                return {
                    "success": False,
                    "message": "Facility capacity is insufficient."
                }

            if (
                str(facility["sport_type"]).lower()
                != request["sport"].lower()
            ):
                db.rollback()

                return {
                    "success": False,
                    "message": "Facility does not support the selected sport."
                }

            # ==========================================
            # STEP 7: VALIDATE BASE TIMESLOT
            # ==========================================

            # This is a read-only check.
            # Do not lock a campus-wide timeslot row:
            # unrelated facilities may use the same time.

            slot = db.execute(
                text("""
                    SELECT slot_id
                    FROM timeslots
                    WHERE `date` = :booking_date
                      AND start_time <= :start_time
                      AND end_time >= :end_time
                      AND LOWER(availability_status) = 'available'
                    LIMIT 1
                """),
                {
                    "booking_date": request["booking_date"],
                    "start_time": start_time,
                    "end_time": end_time
                }
            ).first()

            if slot is None:
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected timeslot is no longer available."
                }

            # ==========================================
            # STEP 8: FACILITY-SPECIFIC AVAILABILITY
            # ==========================================

            facility_available = is_facility_time_available(
                db,
                request["facility_id"],
                request["booking_date"],
                start_time,
                end_time
            )

            if not facility_available:
                db.rollback()

                return {
                    "success": False,
                    "message": (
                        "This facility is already booked "
                        "during the selected time."
                    )
                }

            # ==========================================
            # STEP 9: LOCK AND VALIDATE EQUIPMENT
            # ==========================================

            equipment = db.execute(
                text("""
                    SELECT
                        equipment_id,
                        equipment_name,
                        sport,
                        resource_status,
                        total_quantity
                    FROM equipment
                    WHERE equipment_id = :equipment_id
                    FOR UPDATE
                """),
                {
                    "equipment_id": request["equipment_id"]
                }
            ).mappings().first()

            if equipment is None:
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected equipment does not exist."
                }

            if str(equipment["resource_status"]).lower() != "available":
                db.rollback()

                return {
                    "success": False,
                    "message": "Selected equipment is not available."
                }

            if (
                str(equipment["sport"]).lower()
                != request["sport"].lower()
            ):
                db.rollback()

                return {
                    "success": False,
                    "message": "Equipment does not match the selected sport."
                }

            # ==========================================
            # STEP 10: DETECT RESOURCE CONFLICTS
            # ==========================================

            conflicts = detect_conflicts(
                db=db,
                sport=request["sport"],
                participants=request["participants"],
                facility_id=request["facility_id"],
                booking_date=request["booking_date"],
                start_time=start_time,
                end_time=end_time,
                equipment_id=request["equipment_id"],
                equipment_quantity=request["equipment_quantity"]
            )

            if conflicts:
                db.rollback()

                return {
                    "success": False,
                    "message": "Booking rejected due to resource conflicts.",
                    "conflicts": conflicts
                }

            # ==========================================
            # STEP 11: CALCULATE DURATION
            # ==========================================

            start = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            end = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

            duration_minutes = (
                (end.hour * 60 + end.minute)
                -
                (start.hour * 60 + start.minute)
            )

            if duration_minutes <= 0:
                db.rollback()

                return {
                    "success": False,
                    "message": "Invalid booking duration."
                }

            # ==========================================
            # STEP 12: GENERATE BOOKING ID
            # ==========================================

            booking_id = str(uuid4())

            # ==========================================
            # STEP 13: INSERT CONFIRMED BOOKING
            # ==========================================

            db.execute(
                text("""
                    INSERT INTO bookings (
                        booking_id,
                        request_id,
                        user_id,
                        sport,
                        booking_date,
                        start_time,
                        end_time,
                        duration_minutes,
                        participants,
                        equipment_id,
                        equipment_required,
                        equipment_quantity,
                        facility_id,
                        facility_name,
                        location,
                        booking_status
                    )
                    VALUES (
                        :booking_id,
                        :request_id,
                        :user_id,
                        :sport,
                        :booking_date,
                        :start_time,
                        :end_time,
                        :duration_minutes,
                        :participants,
                        :equipment_id,
                        'Yes',
                        :equipment_quantity,
                        :facility_id,
                        :facility_name,
                        :location,
                        'Confirmed'
                    )
                """),
                {
                    "booking_id": booking_id,
                    "request_id": request_id,
                    "user_id": request["user_id"],
                    "sport": request["sport"],
                    "booking_date": request["booking_date"],
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": duration_minutes,
                    "participants": request["participants"],
                    "equipment_id": request["equipment_id"],
                    "equipment_quantity": request["equipment_quantity"],
                    "facility_id": request["facility_id"],
                    "facility_name": facility["facility_name"],
                    "location": facility["location"]
                }
            )

            # ==========================================
            # STEP 14: COMMIT TRANSACTION
            # ==========================================

            db.commit()

            return {
                "success": True,
                "message": "Booking confirmed successfully!",
                "booking_id": booking_id,
                "request_id": request_id,
                "facility": facility["facility_name"],
                "equipment": equipment["equipment_name"],
                "booking_status": "Confirmed"
            }

    except IntegrityError:

        db.rollback()

        try:
            existing = get_existing_booking(
                db,
                request.get("request_id")
            )

            if existing:
                normalized_request = {
                    **request,
                    "start_time": normalize_time(request["start_time"]),
                    "end_time": normalize_time(request["end_time"])
                }

                return existing_booking_response(
                    existing,
                    normalized_request
                )

        except Exception:
            db.rollback()

        return {
            "success": False,
            "message": (
                "Duplicate request or database constraint violation."
            )
        }

    except Exception as error:

        db.rollback()

        return {
            "success": False,
            "message": "Booking confirmation failed.",
            "error": str(error)
        }
