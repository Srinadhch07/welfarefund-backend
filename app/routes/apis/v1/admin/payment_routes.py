from fastapi import APIRouter, HTTPException, Depends, Request, Query, Form, File, UploadFile
from typing import Literal, Optional
import math
from bson import ObjectId
from datetime import date
from typing import Optional

from app.config.database import payments_collection
from app.dependencies.auth import get_current_admin
from app.services.b2_storage import B2Storage
from app.helpers.helpers import serialize_doc, serialize_docs
from app.schemas.v1.admin.payments_schema import UpdatePayment



router = APIRouter()
b2 = B2Storage()

@router.get("/payments-list")
async def payments_list(
    request: Request,
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, le=10, ge=1),
    size: int = Query(10, le=1000, ge=1),
    search: Optional[str] = Query(None),
    filter: Optional[Literal["pending","approved", "rejected", "returned"]] = Query(None)

):
    skip = (page-1)* size

    query  = {}
    if search:
        query["$or"] = [
            {"user_details.email": {"$regex": search,"$options": "i" }},
            {"user_details.name": {"$regex": search,"$options": "i" } }
        ]
    if filter:
        query["status"] = filter

    payments = await payments_collection.find(query).skip(skip).limit(size).sort({"created_at": -1}).to_list(length=size)
    total_payments = await payments_collection.count_documents(query)

    return  {
        "status": True,
        "message": None,
        "data": {
            "payments": serialize_docs(payments),
            "pagination": {
                "size": size,
                "total_pages": math.ceil(total_payments//size),
                "current_page": page,
                "total_items": total_payments
            }
        }
    }

@router.get("/payment-details/{payment_id}")
async def payment_details(
    request: Request,
    payment_id: str,
    admin: dict = Depends(get_current_admin),
):
    if not ObjectId.is_valid(payment_id):
        raise HTTPException(400, "Invalid payment Id")
    payment_details = await payments_collection.find_one({"_id": ObjectId(payment_id)})
    if not payment_details:
        raise HTTPException(404,"No details found.")
    if payment_details.get("evidence_path"):
        evidence_url = b2.generate_download_url(
            file_key=payment_details.get("evidence_path")
        )
        payment_details["evidence_url"] = evidence_url
    return {
        "status": True,
        "message": None,
        "data": {
            "payment_details": serialize_doc(payment_details)
        }
    }

@router.put("/update-payment/{payment_id}")
async def update_payment(
    request: Request,
    payment_id: str,
    pypayload: UpdatePayment,
    admin: dict = Depends(get_current_admin)
):
    payload = pypayload.dict()
    if not ObjectId.is_valid(payment_id):
        raise HTTPException(400, "Invalid payment id")
    update_payment = await payments_collection.find_one_and_update({"_id": ObjectId(payment_id)}, {"$set": payload})
    return {
        "status": True,
        "message": "Payment status updated.",
        "data": None
    }