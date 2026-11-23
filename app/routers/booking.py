
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.services.booking_service import get_recommended_options
from app.services.booking_confirmation import confirm_booking

from app.schemas.booking import (
    BookingRecommendationRequest,
    BookingConfirmationRequest
)


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


# ==========================================
# 1. GET BOOKING RECOMMENDATIONS
# ==========================================

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
            "message": "Recommendations generated successfully.",
            "recommendations": recommendations
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate recommendations."
        )


# ==========================================
# 2. CONFIRM USER-SELECTED BOOKING
# ==========================================

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

        return result

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to confirm booking."
        )
