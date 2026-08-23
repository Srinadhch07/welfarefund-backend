from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config.security import decode_access_token
from app.config.database import admin_collection
from bson import ObjectId

security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):

    token = credentials.credentials

    try:

        payload = decode_access_token(token)

    except Exception:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    if payload.get("type") != "access":

        raise HTTPException(
            status_code=401,
            detail="Invalid access token",
        )
    admin_id = payload.get("sub")
    admin_details = await admin_collection.find_one({"_id":ObjectId(admin_id)})
    if not admin_details:
        raise HTTPException(400, "Admin detials not found")

    return admin_details