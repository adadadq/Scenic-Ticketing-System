from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, Field


class ProductPublicDTO(BaseModel):
    product_id: int = Field(alias="productId")
    ticket_type_id: int = Field(alias="ticketTypeId")
    scenic_spot_name: str = Field(alias="scenicSpotName")
    product_name: str = Field(alias="productName")
    ticket_name: str = Field(alias="ticketName")
    ticket_category: str = Field(alias="ticketCategory")
    original_price: Decimal = Field(alias="originalPrice")
    sale_price: Decimal = Field(alias="salePrice")
    description: str | None = None
    refund_rule: str | None = Field(default=None, alias="refundRule")
    real_name_required: bool = Field(alias="realNameRequired")
    trip_type: str = Field(alias="tripType")
    raft_capacity: int = Field(alias="raftCapacity")
    start_pier_name: str = Field(alias="startPierName")
    end_pier_name: str = Field(alias="endPierName")
    window_phone: str = Field(alias="windowPhone")

    model_config = {"populate_by_name": True}


class TimeSlotPublicDTO(BaseModel):
    time_slot_id: int = Field(alias="timeSlotId")
    product_id: int = Field(alias="productId")
    ticket_type_id: int = Field(alias="ticketTypeId")
    visit_date: date = Field(alias="visitDate")
    slot_start_time: time = Field(alias="slotStartTime")
    slot_end_time: time = Field(alias="slotEndTime")
    quota_remaining: int = Field(alias="quotaRemaining")

    model_config = {"populate_by_name": True}
