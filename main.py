from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.config.database import connect_db, close_connection
from app.core.exceptions import http_exception_handler, global_exception_handler

# Authentication routes
from app.routes.auth.admin_auth import router as admin_auth_router
from app.routes.auth.user_auth import router as user_auth_router

from app.routes.apis.v1.admin.profile_router import router as admin_profile
from app.routes.apis.v1.admin.payment_setting_routes import  router as admin_payment_settings
from app.routes.apis.v1.admin.payment_routes import router as admin_payments

# User routes
from app.routes.apis.v1.user.profile_router import router as user_profile
from app.routes.apis.v1.user.payments_routes import router as user_payments


@asynccontextmanager
async def lifespan(app:FastAPI):
    await connect_db()
    yield
    await close_connection()

app = FastAPI(
    title="welfarefund application",
    description="Pivot project",
    version="1.0",
    debug=True,
    docs_url="/docs",
    redoc_url="/read-docs",
    lifespan=lifespan
)


app.add_exception_handler(HTTPException, http_exception_handler)

app.add_exception_handler(Exception,global_exception_handler)


@app.get("/health")
async def health():
    return {
        "status": True,
        "message": "APIs are working",
        "data": None,
    }

@app.get("/")
async def home():
    return RedirectResponse(url="/docs")

# Authentication routes
app.include_router(admin_auth_router,prefix="/api/admin/authentication", tags = ["Admin Authentication"])
app.include_router(user_auth_router, prefix="/api/user/authentcation", tags=["User Authentication"])

app.include_router(admin_profile, prefix="/api/admin/profile", tags = ["Admin Profile"])
app.include_router(user_profile, prefix="/api/user/profile", tags = ["User Profile"])

app.include_router(admin_payment_settings, prefix="/api/admin/payments-settings", tags=["Admin Payment settings"])
app.include_router(admin_payments, prefix="/api/admin/payments", tags=["Admin Payments"])


# user
app.include_router(user_payments, prefix="/api/user/payments", tags=["User Payments settings"])

if __name__  == "__main__":
    import uvicorn
    uvicorn.run("main:app",port=8080, reload = True)