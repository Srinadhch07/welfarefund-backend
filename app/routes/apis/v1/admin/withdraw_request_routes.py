from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Request, Query
from typing import Optional, Literal
import math
from bson import ObjectId

from app.config.database import withdrawal_request_collection
from app.dependencies.auth import get_current_admin
from app.services.b2_storage import B2Storage
from app.helpers.timezone_utils import now_utc
from app.helpers.helpers import serialize_doc, serialize_docs

router = APIRouter()
b2 = B2Storage()

@router.get("/requests")
async def withdraw_request(
    request: Request,
    filter: Literal["pending", "approved", "rejected"] = Query(None), 
    search: str = Query(None),
    page: int = Query(1, le=10, ge=1),
    size: int = Query(10, le=1000, ge=1),
    admin: dict = Depends(get_current_admin)
):
    skip = (page -1 ) * size
    query = {}
    if filter:
        query["status"] = filter
    if search:
        query["$or"] = [
            {"recipient_details.name": { "$regex": search,"$options": "i" }},
            {"recipient_details.contact": { "$regex": search,"$options": "i" }},
            {"admin_details.name": { "$regex": search,"$options": "i" }},
            {"admin_details.email": { "$regex": search,"$options": "i" }},
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
    admin: dict = Depends(get_current_admin)
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
    released_amount:Optional[int] = Form(None),
    evidence: Optional[UploadFile] = File(None),
    status: Optional[Literal["approved","rejected"]] = Form(None),
    rejected_reason: Optional[str] = Form(None),
    admin: dict = Depends(get_current_admin),
):
    if not ObjectId.is_valid(request_id):
        raise HTTPException(404, "Ìnvalid ID")
    withdraw_request = await  withdrawal_request_collection.find_one({"_id": ObjectId(request_id)})
    if not withdraw_request:
        raise HTTPException(404, "No request found.")
    if withdraw_request.get("status") != "pending":
        raise HTTPException(400, "Withdraw request cannot be updated")        
    payload = {}
    if released_amount:
        payload["released_amount"] = released_amount
    if status == "approved" and not released_amount:
        raise HTTPException(400, "Release amount to approve the request")
    if status != "pending":
        raise HTTPException(400, "Request is already reviewed.")
    if status:
        payload["status"] = status
    if rejected_reason:
        payload["rejected_reason"] = rejected_reason
    if evidence:
        release_amount_evidence_path = b2.upload_file(
            file=evidence,
            folder="welfarefund/withdrawals",
        )
        payload["released_amount_evidence_path"] = release_amount_evidence_path
    payload["updated_at"] = now_utc()
    await withdrawal_request_collection.find_one_and_update({"_id": ObjectId(request_id)},{"$set": payload})
    return {
        "status": True,
        "message": "Withdraw request updated.",
        "data": None
    }
    