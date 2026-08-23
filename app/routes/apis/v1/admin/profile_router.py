from fastapi import APIRouter, HTTPException, Depends, Request
from app.dependencies.auth import get_current_admin

router = APIRouter()

@router.get("/profile")
async def admin_profile(
    request: Request,
    admin: dict = Depends(get_current_admin)
) -> dict:
    admin.pop("password")
    admin.pop("_id")
    return {
        "status": True,
        "message": None,
        "data": {
            "details": admin
        }
    }