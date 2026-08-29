from fastapi import APIRouter, Depends, File, UploadFile, Form, Request
from typing import Optional

from app.dependencies.auth import get_current_admin
from app.schemas.v1.admin.payments_schema import PaymentDetails
from app.config.database import payment_settings_collection
from app.services.b2_storage import B2Storage
from app.helpers.helpers import serialize_doc


router = APIRouter()
b2 = B2Storage()

@router.post("/update-detials")
async def update_details(
    request: Request,
    pypayload: PaymentDetails,
    admin: dict = Depends(get_current_admin)
):
    payload = pypayload.dict()
    payment_setting = await payment_settings_collection.find_one({})
    if not payment_setting:
        payment_setting = await payment_settings_collection.insert_one(payload)
    else:
        payment_id = payment_setting.get("_id")
        await payment_settings_collection.find_one_and_update({"_id": payment_id}, {"$set": payload})
    return {
        "status": True,
        "message": "Payment settings are updated",
        "data": {
            "details": serialize_doc(payload)
        }
    }

@router.post("/update-qr")
async def update_qr(
    request: Request,
    qr_file: UploadFile = File(...)
):
    qr_code = b2.upload_file(file=qr_file, folder="welfarefund/images")
    await payment_settings_collection.find_one_and_update({}, {"$set": {"qr_code": qr_code}})
    return {
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
    print(f'Payment details : {payment_detials}')
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
