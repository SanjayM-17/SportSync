
from pydantic import BaseModel


class SportSelectionRequest(BaseModel):
    pass


class FacilitySelectionRequest(BaseModel):
    sport: str
    participants: int


class TimeslotSelectionRequest(BaseModel):
    booking_date: str


class EquipmentSelectionRequest(BaseModel):
    sport: str
    booking_date: str
    start_time: str
    end_time: str


class BookingRecommendationRequest(BaseModel):
    sport: str
    participants: int
    facility_id: str
    booking_date: str
    start_time: str
    end_time: str
    equipment_id: str
    equipment_quantity: int


class BookingConfirmationRequest(BookingRecommendationRequest):
    request_id: str
    user_id: str
