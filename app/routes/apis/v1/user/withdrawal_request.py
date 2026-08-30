from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Request, Query
from typing import Optional, Literal
import math
from bson import ObjectId

from app.config.database import withdrawal_request_collection
from app.dependencies.auth import get_current_user
from app.services.b2_storage import B2Storage
from app.helpers.timezone_utils import now_utc
from app.helpers.helpers import serialize_doc, serialize_docs

router = APIRouter()
b2 = B2Storage()

@router.post("/withdraw-request")
async def  withdraw_request(
    request: Request,
    amount: int = Form(...),
    recipient_name: str = Form(...),
    recipient_contact: str = Form(...),
    evidence: Optional[UploadFile] = File(...),
    reason: str = Form(...),
    description: str = Form(...),
    account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    upi_id: Optional[str] = Form(None),
    upi_number: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    payload = {
        "amount": amount,
        "recipient_details": {
            "name": recipient_name,
            "contact": recipient_contact
        },
        "evidence_path": None,
        "reason": reason,
        "description": description,
        "account_details": {
            "account_number": account_number,
            "ifsc_code": ifsc_code,
            "upi_id": upi_id,
            "upi_number": upi_number,
        },
        "user_id": user.get("_id"),
        "user_details": user,
        "status": "pending",
        "created_at": now_utc(),
        "updated_at": now_utc()
    }
    if evidence:
        evidence_path = b2.upload_file(
            file=evidence,
            folder="welfarefund/withdrawals"
        )
        payload["evidence_path"] = evidence_path
    await withdrawal_request_collection.insert_one(payload)
    return {
        "status": True,
        "message": "Withdraw request is successful",
        "data": None
    }

@router.get("/withdraw-requests")
async def withdraw_request(
    request: Request,
    filter: Literal["pending", "approved", "rejected"] = Query(None), 
    search: str = Query(None),
    page: int = Query(1, le=10, ge=1),
    size: int = Query(10, le=1000, ge=1),
    user: dict = Depends(get_current_user)
):
    skip = (page -1 ) * size
    query = {}
    query["user_id"] = user.get("_id")
    if filter:
        query["status"] = filter
    if search:
        query["$or"] = [
            {"recipient_details.name": { "$regex": search,"$options": "i" }},
            {"recipient_details.contact": { "$regex": search,"$options": "i" }},
            {"user_details.name": { "$regex": search,"$options": "i" }},
            {"user_details.email": { "$regex": search,"$options": "i" }},
            {"status": { "$regex": search,"$options": "i" }},
            {"reason": { "$regex": search,"$options": "i" }},
            {"description": { "$regex": search,"$options": "i" }},
        ]
    withdraw_requests = await withdrawal_request_collection.find(query).skip(skip).limit(size).sort({"created_at": -1}).to_list(length=size)
    total_withdrawals = await withdrawal_request_collection.count_documents(query)

    return {
        "status": True,
        "message": None,
        "data": {
            "withdraw_requests": serialize_docs(withdraw_requests),
            "pagination": {
                            "size": size,
                            "total_pages": math.ceil(total_withdrawals//size),
                            "current_page": page,
                            "total_items": total_withdrawals
                        }
        }
    }

@router.get("/view-request/{request_id}")
async def view_request(
    request: Request,
    request_id: str,
    user: dict = Depends(get_current_user)
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(400,"Invalid Id")
    withdraw_request = await withdrawal_request_collection.find_one({"_id": ObjectId(request_id)})
    if withdraw_request.get("evidence_path"):
        evidence_url = b2.generate_download_url(
            file_key= withdraw_request.get("evidence_path")
        )
        withdraw_request["evidence_url"] = evidence_url
    return {
        "status": True,
        "message": None,
        "data": {
            "withdraw_request_details": serialize_doc(withdraw_request)
        }
    }
@router.put("/update-request/{request_id}")
async def update_request(
    request: Request,
    request_id: str,
    amount:Optional[int] = Form(None),
    recipient_name: Optional[str] = Form(None),
    recipient_contact: Optional[str] = Form(None),
    evidence: Optional[UploadFile] = File(None),
    reason: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    account_number: Optional[str] = Form(None),
    ifsc_code: Optional[str] = Form(None),
    upi_id: Optional[str] = Form(None),
    upi_number: Optional[str] = Form(None),
    user: dict = Depends(get_current_user),
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(404, "Ìnvalid ID")
    withdraw_request = await  withdrawal_request_collection.find_one({"_id": ObjectId(request_id)})
    if not withdraw_request:
        raise HTTPException(404, "No request found.")
    if withdraw_request.get("status") != "pending":
        raise HTTPException(400, "Withdraw request cannot be updated")        
    payload = {}
    if amount:
        payload["amount"] = amount
    if recipient_name is not None or recipient_contact is not None:
        payload["recipient_details"] = {}
    if recipient_name:
        payload["recipient_details"]["name"] = recipient_name
    if recipient_contact:
        payload["recipient_details"]["contact"] = recipient_contact
    if evidence:
        evidence_path = b2.upload_file(
            file=evidence,
            folder="welfarefund/withdrawals",
        )
    if reason:
        payload["reason"] = reason
    if description:
        payload["description"] = description
    if account_number:
        payload["account_details"]["account_number"] = account_number
    if ifsc_code:
        payload["account_details"]["ifsc_code"] = ifsc_code
    if upi_id:
        payload["account_details"]["upi_id"] = upi_id
    if upi_number:
        payload["account_details"]["upi_number"] = upi_number
    await withdrawal_request_collection.find_one_and_update({"_id": ObjectId(request_id)},{"$set": payload})
    return {
        "status": True,
        "message": "Withdraw request updated.",
        "data": None
    }
    
    
