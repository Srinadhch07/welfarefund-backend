from pydantic import BaseModel
from typing import Optional, Literal

class PaymentDetails(BaseModel):
    name: str
    account_number: str
    bank_name: str
    ifsc_code: str
    upi_id: str
    qr_code: Optional[str] = None
class UpdatePayment(BaseModel):
    status: Literal["approved","pending","rejected", "returned"]
    