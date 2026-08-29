from fastapi import APIRouter, Depends, File, UploadFile, Form, Request, Query, HTTPException
from typing import Optional
from bson import ObjectId
from app.dependencies.auth import get_current_user
from app.config.database import payment_settings_collection, payments_collection
from app.services.b2_storage import B2Storage
from app.helpers.helpers import serialize_doc, serialize_docs
import math
from datetime import datetime, timezone


router = APIRouter()
b2 = B2Storage()



@router.get("/view-details")
async def view_details(
    request: Request,
    user: dict = Depends(get_current_user)
):
    payment_detials = await payment_settings_collection.find_one({})
    if payment_detials.get("qr_code") is not None:
        qr_code_url = b2.generate_download_url(file_key=payment_detials.get("qr_code"))
        payment_detials["qr_code_url"] = qr_code_url
    return {
        "status": True,
        "message": None,
        "data": {
            "payment_settings": serialize_doc(payment_detials)
        }
    }


@router.post("/payment-form")
async def payment_form(
    request: Request,
    amount: int = Form(...),
    evidence: UploadFile = File(...),
    description: Optional[str] = Form(...),
    transaction_id: Optional[str] = Form(...),
    user: dict = Depends(get_current_user)
):
    payload = {
        "amount": amount,
        "description": description,
        "status": "pending",
        "user_id": user.get("_id"),
        "user_details": {
            "_id": user.get("_id"),
            "name": user.get("name"),
            "email": user.get("email"),
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),

    }
    if evidence:
        evidence_path = b2.upload_file(
            file=evidence,
            folder= "welfarefund/payments"
        )
        payload["evidence_path"] = evidence_path
    if transaction_id:
        payload["transaction_id"] = transaction_id
    await payments_collection.insert_one(payload)
    return {
        "status": True,
        "message": "Thank you for donation.",
        "data": None
    }


@router.get("/payment-history")
async def payment_history(
    request: Request,
    user: dict = Depends(get_current_user),
    page: int = Query(1, le=10, ge=1),
    size: int = Query(10, le=1000, ge=1),
):
    skip = (page - 1) * size

    query = {"user_id": user.get("_id")}

    donations = await (payments_collection.find(query).skip(skip).limit(size).to_list(length=size))

    total_donations = await payments_collection.count_documents(query)

    return {
        "status": True,
        "message": None,
        "data": {
            "donation_details": serialize_docs(donations),
            "pagination": {
                "size": size,
                "current_page": page,
                "total_pages": math.ceil(total_donations / size),
                "total_items": total_donations,
            },
        },
    }

@router.get("/payment-details/{payment_id}")
async def donation_details(
    request: Request,
    payment_id: str,
    user: dict =  Depends(get_current_user),
):
    if not ObjectId.is_valid(payment_id):
        raise HTTPException(400,"Invalid Id")
    payment_details = await payments_collection.find_one({"_id":  ObjectId(payment_id)})
    if not payment_details:
        raise HTTPException(404, "No payment details found.")
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
    
 
    
    