from fastapi import APIRouter,Request, HTTPException, Form, Query
from app.config.database import admin_collection, tokens_collections
from app.config.security import hash_password, verify_password, create_access_token, create_refresh_token
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

from app.schemas.v1.admin.auth_schema import RefreshToken

load_dotenv()
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

router = APIRouter()

@router.post("/register-admin")
async def register_admin(
    reuqest: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
    ):
    if not all([name,email, password]):
        raise HTTPException(400,"Missing required fields")
    payload = {
        "name": name, 
        "email": email,
        "password": hash_password(password)
    }
    existing_admin = await admin_collection.find_one({"email": email})
    if existing_admin:
        raise HTTPException(400,"Admin already exists, please login.")
    await admin_collection.insert_one(payload)
    return {
            "status": True, "message": "Admin created", "data": None
        }
@router.post("/login")
async def login_admin(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    if not all([email, password]):
        raise HTTPException(404,"Missing rquired fields")
    admin = await admin_collection.find_one({"email": email})
    if not admin:
        raise HTTPException(404, "Admin not found.")
    if not verify_password(password, admin.get("password")):
        raise HTTPException("Incorrect credentials, please check your email or password")
    access_token = create_access_token(admin.get("_id"), "admin")
    refresh_token = create_refresh_token()
    refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    session_payload = {
        "token": refresh_token,
        "expires_at": refresh_token_expires,
        "revoked": False,
        "user_id": admin.get("_id"),
        "created_at": datetime.now(timezone.utc)
    }
    await tokens_collections.insert_one(session_payload)
    return {
        "status": True,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    }

@router.post("/refresh")
async def refresh_token(request: Request,
                        pypayload:RefreshToken):
    refresh_token = pypayload.refresh_token
    payload = {
        "token": refresh_token,
        "revoked": False,
    }
    session = await tokens_collections.find_one(payload)
    if not session:
        raise HTTPException(401,"Invalid refresh token")
    if session["expires_at"] <= datetime.now(timezone.utc):
        await tokens_collections.find_one_and_update({"token": refresh_token}, {"$set": {'revoked': True}})
        raise HTTPException(401, "refresh token is expired")
    admin_id = session["user_id"]
    access_token = create_access_token(admin_id,"admin")

    return {
        "status": True,
        "message": "Access token refreshed",
        "data": {
            "access_token": access_token
        }
    }
    