from fastapi import APIRouter, Depends, File, UploadFile, Form, Request
from typing import Optional

from app.dependencies.auth import get_current_admin
from app.schemas.v1.admin.payments_schema import PaymentDetails
from app.config.database import payment_settings_collection
from app.services.b2_storage import B2Storage


router = APIRouter()
b2 = B2Storage()

@router.post("/update-detials")
async def update_details(
    request: Request,
    admin: dict = Depends(get_current_admin),
    payload : dict = PaymentDetails
):
    await payment_settings_collection.find_one_and_update({}, {"$set":payload})
    return {
        "status": True,
        "message": "Payment settings are updated",
        "data": {
            "details": payload
        }
    }

@router.post("/update-qr")
async def update_qr(
    request: Request,
    qr_file: UploadFile = File(...)
):
    qr_code = b2.upload_file(file=qr_file)
    await payment_settings_collection.find_one_and_update({}, {"$set": {"qr_code": qr_code}})
    {
        "status": True, 
        "message": "QR code upload successfully.",
        "data": None
    }


@router.get("/view-details")
async def view_details(
    request: Request,
    admin: dict = Depends(get_current_admin)
):
    payment_detials = await payment_settings_collection.find_one({})
    if payment_detials.get("qr_code"):
        qr_code_url = b2.generate_download_url(file=payment_detials.get("qr_code"))
        payment_detials["qr_code_url"] = qr_code_url
    return {
        "status": True,
        "message": None,
        "data": {
            "payment_settings": payment_detials
        }
    }
