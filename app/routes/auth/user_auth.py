from fastapi import APIRouter,Request, HTTPException, Form, Query
from app.config.database import user_collection, tokens_collections
from app.config.security import hash_password, verify_password, create_access_token, create_refresh_token
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

from app.schemas.v1.admin.auth_schema import RefreshToken
from app.helpers.helpers import generate_random_text, generate_otp
from app.services.send_mail import send_reset_password_mail, send_otp_email

load_dotenv()
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

router = APIRouter()

@router.post("/register-user")
async def register_user(
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
        "password": hash_password(password),
        "is_verified": False,
        "is_blocked": False,
        "otp": None,
        "otp_expires": None
    }
    existing_user = await user_collection.find_one({"email": email, "is_verified": True})
    if existing_user:
        raise HTTPException(400,"user already exists, please login.")
    otp =  generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes = 5)
    payload["otp"] = otp
    payload["otp_expires"] = otp_expires
    user = await user_collection.find_one(payload)
    if not user:
        await user_collection.insert_one(payload)
        user = await user_collection.find_one(payload)
    await send_otp_email(user, otp)
    return {
            "status": True, "message": "user created", "data": None
        }

@router.post("/verify-otp")
async def verify_user(
    request: Request,
    email: str,
    otp: str
):
    user = await user_collection.find({"email": email})
    if not user:
        raise HTTPException(400,"No user found.")
    otp_expires = user.get("otp_expires")
    if otp_expires <= datetime.now(timezone.utc):
        raise HTTPException("OTP is expired")
    original_otp = user.get("otp")
    if original_otp != otp:
        raise HTTPException("Invalid OTP.")
    await user_collection.find_one_and_update({"email": email}, {"$set": {"is_verified": True}})
    return {
                "status": True, "message": "Your acccount is verified", "data": None
            }

@router.post("/resend-otp")
async def resend_otp(request: Request,
                     email: str
                     ):
    if not email:
        raise HTTPException(400, "Invalid email")
    user = await user_collection.find({"email": email})
    if not user:
        raise HTTPException(400,"No user found.")
    otp =  generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes = 5)
    payload = {}
    payload["otp"] = otp
    payload["otp_expires"] = otp_expires
    await user_collection.find_one_and_update({"email": email}, {"$set": payload})
    await send_otp_email(user, otp)
    return {
                "status": True, "message": "user created", "data": None
            }

@router.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    if not all([email, password]):
        raise HTTPException(404,"Missing rquired fields")
    user = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "user not found.")
    if not verify_password(password, user.get("password")):
        raise HTTPException("Incorrect credentials, please check your email or password")
    access_token = create_access_token(user.get("_id"), "user")
    refresh_token = create_refresh_token()
    refresh_token_expires = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    session_payload = {
        "token": refresh_token,
        "expires_at": refresh_token_expires,
        "revoked": False,
        "user_id": user.get("_id"),
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
    user_id = session["user_id"]
    access_token = create_access_token(user_id,"user")

    return {
        "status": True,
        "message": "Access token refreshed",
        "data": {
            "access_token": access_token
        }
    }

@router.post("/forgot-password")
async def forgot_password( email: str) -> dict:
    if not email:
        raise HTTPException(400,"Email required")
    user  = await user_collection.find_one({"email": email})
    if not user:
        raise HTTPException(404, "Email not found.")
    plain_password =  generate_random_text()
    hashed_password = hash_password(plain_password)
    await user_collection.find_one_and_update({"email": email}, {"$set": {"password": hashed_password}})
    await send_reset_password_mail(email, plain_password)
    return {
            "status": True,
            "message": "New password sent to mail.",
            "data": None
        }
