from fastapi import APIRouter, HTTPException, Depends, Request, Form, UploadFile, File
from typing import Optional

from app.dependencies.auth import get_current_admin
from app.services.b2_storage import B2Storage
from app.config.security import hash_password
from app.config.database import admin_collection

router = APIRouter()
b2 = B2Storage()

@router.get("/profile")
async def admin_profile(
    request: Request,
    admin: dict = Depends(get_current_admin)
) -> dict:
    admin.pop("password")
    admin.pop("_id")
    if admin.get("profile_photo_path"):
       profile_photo_url = b2.generate_download_url(
           file_key=admin.get("profile_photo_path")
       ) 
       admin["profile_photo_url"] = profile_photo_url
    return {
        "status": True,
        "message": None,
        "data": {
            "details": admin
        }
    }

@router.put("/update-profile")
async def update_profile(
    request: Request,
    admin: dict = Depends(get_current_admin),
    name: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    profile_photo: Optional[UploadFile] = File(None),
    new_password: Optional[str] = Form(None)
):
    if not any([name, email, profile_photo, new_password]):
        raise HTTPException(400, "No details found to update.")
    payload = {}
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    if profile_photo:
        profile_photo_path = b2.upload_file(
            file=profile_photo,
            folder="welfarefund/images"
        )
        payload["profile_photo_path"] = profile_photo_path
    if new_password:
        hashed_password = hash_password(new_password)
        payload["password"] = hashed_password
    admin_id = admin.get("_id")
    await admin_collection.find_one_and_update({"_id": admin_id}, {"$set": payload})
    return {
        "status": True,
        "message": "Profile is updated.",
        "data": {
            "updated_details": payload
        }
    }
        
