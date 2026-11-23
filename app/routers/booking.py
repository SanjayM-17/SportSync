
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.services.booking_service import (
    get_sports,
    get_facilities,
    get_timeslots,
    get_equipment,
    get_recommended_options
)

from app.services.booking_confirmation import confirm_booking

from app.schemas.booking import (
    FacilitySelectionRequest,
    TimeslotSelectionRequest,
    EquipmentSelectionRequest,
    BookingRecommendationRequest,
    BookingConfirmationRequest
)


router = APIRouter(
    prefix="/bookings",
    tags=["SportSync Booking"]
)


# STEP 1: Select sport
@router.get("/sports")
def select_sport(db: Session = Depends(get_db)):
    try:
        sports = get_sports(db)

        return {
            "success": True,
            "sports": sports
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch sports."
        )


# STEP 2 and 3: Select participants and facility
@router.post("/facilities")
def select_facility(
    request: FacilitySelectionRequest,
    db: Session = Depends(get_db)
):
    try:
        facilities = get_facilities(
            db,
            request.sport,
            request.participants
        )

        return {
            "success": True,
            "facilities": facilities
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch suitable facilities."
        )


# STEP 4: Select a free campus-wide timeslot
@router.post("/timeslots")
def select_timeslot(
    request: TimeslotSelectionRequest,
    db: Session = Depends(get_db)
):
    try:
        slots = get_timeslots(
            db,
            request.booking_date
        )

        return {
            "success": True,
            "available_timeslots": slots
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch available timeslots."
        )


# STEP 5: Select compatible equipment
@router.post("/equipment")
def select_equipment(
    request: EquipmentSelectionRequest,
    db: Session = Depends(get_db)
):
    try:
        equipment = get_equipment(
            db,
            request.sport,
            request.booking_date,
            request.start_time,
            request.end_time
        )

        return {
            "success": True,
            "equipment": equipment
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to fetch available equipment."
        )


# STEP 6: Validate complete booking requirements
@router.post("/recommend")
def get_recommendations(
    request: BookingRecommendationRequest,
    db: Session = Depends(get_db)
):
    try:
        recommendations = get_recommended_options(
            db,
            request.model_dump()
        )

        if not recommendations:
            return {
                "success": False,
                "message": "No feasible booking options found.",
                "recommendations": []
            }

        return {
            "success": True,
            "message": "Feasible options generated successfully.",
            "recommendations": recommendations
        }

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate recommendations."
        )


# FINAL STEP: Confirm user-selected booking
@router.post("/confirm")
def confirm_selected_booking(
    request: BookingConfirmationRequest,
    db: Session = Depends(get_db)
):
    try:
        result = confirm_booking(
            db,
            request.model_dump()
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=409,
                detail=result
            )

        return result

    except HTTPException:
        raise

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to confirm booking."
        )
