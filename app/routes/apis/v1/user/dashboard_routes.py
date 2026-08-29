from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile,File, Request, Query
from typing import Literal
import math
from app.config.database import payments_collection
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
    payments = await payments_collection.find(query).sort({"updated_at": -1}).skip(skip).limit(size).to_list(length=size)
    total_payments = await payments_collection.count_documents(query)

    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "total_amount": {"$sum": "$amount"}
            }
        }
    ]
    cursor = await payments_collection.aggregate(pipeline)
    result = await cursor.to_list(length=None)
    status_totals = {
        "approved": 0,
        "pending": 0,
        "rejected": 0,
        "returned": 0
    }
    for  item in result:
        status_totals[item["_id"]] = item["total_amount"]

    return {
        "status": True,
        "message":None,
        "data": {
            "payments": serialize_docs(payments),
            "stats": {
                "pending_amount": status_totals.get("pending"),
                "approved_amount": status_totals.get("approved"),
                "rejected_amount": status_totals.get("rejected"),
                "returned_amount": status_totals.get("returned"),
            },
            "pagination": {
                                "size": size,
                                "current_page": page,
                                "total_pages": math.ceil(total_payments / size),
                                "total_items": total_payments,
            },
        }
    }
