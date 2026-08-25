from fastapi import APIRouter, HTTPException, Depends, Request, File, Form, UploadFile
from typing import Optional

from app.config.database import user_collection
from app.dependencies.auth import get_current_user
from app.services.b2_storage import B2Storage
from app.config.security import hash_password
from app.helpers.helpers import serialize_doc

router = APIRouter()
b2 = B2Storage()

@router.get("/view-profile")
async def view_profile(
    request: Request,
    user: dict = Depends(get_current_user)
):
    profile_image = user.get("profile_image")
    if profile_image:
        profile_image_url = b2.generate_download_url(
            file=profile_image
        )
        user["profile_image_url"] = profile_image_url
    
    return {
        "status": True, 
        "message": None,
        "data": {
            "profile_details": serialize_doc(user)
        }
    }

# c40 - checkout the API storage
@router.put("/update-profile", summary="Test this API")
async def update_profile(
    request: Request,
    user: dict = Depends(get_current_user),
    name: Optional[str] = Form(...),
    password: Optional[str] = Form(...),
    profile_file: Optional[UploadFile] = File(...)
):
    payload = {}
    if name:
        payload["name"] = name
    if password:
        payload["password"] = hash_password(password)
    if profile_file:
        profile_image = b2.upload_file(
            file=profile_file,
            folder="welfarefund/images"
        )
        payload["profile_image"] = profile_image
    await user_collection.find_one_and_update({"email": user.get("email")}, {"$set": payload})
    return {
        "status": True,
        "message": "Profile updated successfuly.",
        "data": payload
    }
