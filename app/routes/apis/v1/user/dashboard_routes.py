from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile,File, Request, Query
from typing import Literal
import math
from app.config.database import payments_collection, withdrawal_request_collection
from app.helpers.helpers import serialize_doc, serialize_docs
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.get("/view")
async def view_dashboard(
    request: Request,
    page: int = Query(1, ge=1, le=100),
    size: int  = Query(10, ge=1, le=1000),
    # user: dict = Depends(get_current_user),
    filter: Literal["pending","approved"] = Query(None),
    search: str = Query(None)
):
    skip = (page - 1) * size
    query = {}
    if filter:
        query["status"] = filter,
    if search:
        query["$or"] = [
            {"user_details.name":{"$regex": search, "$options": "i"}}, 
            {"user_details.email":{"$regex": search, "$options": "i"}}, 
        ]
    payments = await payments_collection.find(query).sort({"created_at": -1}).skip(skip).limit(size).to_list(length=size)
    total_payments = await payments_collection.count_documents(query)
    withdrawals = await withdrawal_request_collection.find(query).sort({"created_at": -1}).skip(skip).limit(size).to_list(length=size)

    request_amount_pipeline = [
        {
            "$match": {
                "status": "pending"
            }
        },
        {
            "$group": {
                "_id": None,
                "total_amount": {"$sum": "$amount"}
            }
        }
    ]
    approved_amount_pipeline = [{
        "$match": {
            "status": "approved"
        }},
        {
        "$group": {
            "_id": None,
            "total_amount": { "$sum": "$amount" }
        }
    }]
    rejected_amount_pipeline = [{
            "$match": {
                "status": "rejected"
            }},{
            "$group": {
                "_id": None,
                "total_amount": { "$sum": "$amount" }
            }
    }]
    withdrals_amount_pipeline = [{
        "$match": {
            "status": "approved"
        }
    },{
        "$group": {
            "_id": None,
            "total_amount": {"$sum": "$released_amount"}
        }
    }]
    
    cursor = await payments_collection.aggregate(request_amount_pipeline)
    result = await cursor.to_list(length=None)
    total_pending_donation_amount = result[0]["total_amount"] if result else 0

    cursor = await payments_collection.aggregate(approved_amount_pipeline)
    result = await cursor.to_list(length=None)
    total_approved_amount = result[0]["total_amount"] if result else 0
    
    cursor = await payments_collection.aggregate(rejected_amount_pipeline)
    result = await cursor.to_list(length=None)
    total_rejected_amount = result[0]["total_amount"] if result else 0

    cursor = await withdrawal_request_collection.aggregate(withdrals_amount_pipeline)
    result = await cursor.to_list(length=None)
    total_withdrawal_amount = result[0]["total_amount"] if result else 0

    available_amount = total_approved_amount - total_withdrawal_amount
    

    return {
        "status": True,
        "message":None,
        "data": {
            "stats": {
                "pending_donation_amount": total_pending_donation_amount,
                "approved_donation_amount": total_approved_amount,
                "total_rejected_amount": total_rejected_amount,
                "total_withdrawal_amount": total_withdrawal_amount,
                "available_amount": available_amount
            },
            "payments": serialize_docs(payments),
            "withdrawals": serialize_docs(withdrawals),
            "pagination": {
                                "size": size,
                                "current_page": page,
                                "total_pages": math.ceil(total_payments / size),
                                "total_items": total_payments,
            },
        }
    }