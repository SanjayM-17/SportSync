
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from uuid import uuid4

from app.engines.conflict_engine import (
    detect_conflicts,
    is_campus_time_available
)

from app.engines.os_engine import get_resource_manager


# Shared OS resource manager
resource_manager = get_resource_manager()


def normalize_time(value):
    """
    Normalize HH:MM and HH:MM:SS into HH:MM.
    """

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
        Process-local mutex synchronization.

    DBMS ENGINE:
        Global campus row locking.
        Facility and equipment row locking.
        READ COMMITTED isolation.
        Duplicate request prevention.
        Atomic transaction.

    CAMPUS-WIDE RULE:
        A confirmed booking blocks overlapping
        time intervals across the entire campus.

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

        # Normalize times
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

        # Use one common campus mutex rather than
        # separate mutexes for exact time intervals.
        #
        # This serializes campus booking operations
        # within this Python application process.

        resource_ids = [
            "campus-global-booking",
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
            # STEP 4: GLOBAL CAMPUS DATABASE LOCK
            # ==========================================

            # Every confirmation transaction must lock
            # the same permanent database row.
            #
            # The lock remains held until COMMIT or ROLLBACK.
            # It coordinates separate application processes.

            campus_lock = db.execute(
                text("""
                    SELECT lock_id
                    FROM campus_booking_lock
                    WHERE lock_id = 1
                    FOR UPDATE
                """)
            ).first()

            if campus_lock is None:
                db.rollback()

                return {
                    "success": False,
                    "message": "Campus booking lock is not configured."
                }

            # ==========================================
            # STEP 5: DUPLICATE REQUEST CHECK
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
            # STEP 6: VALIDATE USER
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
            # STEP 7: LOCK AND VALIDATE FACILITY
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
            # STEP 8: LOCK SELECTED TIMESLOT
            # ==========================================

            slot = db.execute(
                text("""
                    SELECT slot_id
                    FROM timeslots
                    WHERE `date` = :booking_date
                      AND start_time <= :start_time
                      AND end_time >= :end_time
                      AND LOWER(availability_status) = 'available'
                    LIMIT 1
                    FOR UPDATE
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
            # STEP 9: CAMPUS-WIDE AVAILABILITY CHECK
            # ==========================================

            # This check occurs after acquiring the global
            # database lock, so a previous confirmation
            # cannot be missed.

            campus_available = is_campus_time_available(
                db,
                request["booking_date"],
                start_time,
                end_time
            )

            if not campus_available:
                db.rollback()

                return {
                    "success": False,
                    "message": (
                        "This campus-wide timeslot has already "
                        "been booked. Please select another slot."
                    )
                }

            # ==========================================
            # STEP 10: LOCK AND VALIDATE EQUIPMENT
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
            # STEP 11: DETECT RESOURCE CONFLICTS
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
            # STEP 12: CALCULATE DURATION
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
            # STEP 13: GENERATE BOOKING ID
            # ==========================================

            booking_id = str(uuid4())

            # ==========================================
            # STEP 14: INSERT CONFIRMED BOOKING
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
            # STEP 15: COMMIT TRANSACTION
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
