from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.config.database import connect_db, close_connection
from app.core.exceptions import http_exception_handler, global_exception_handler

# Admin routes
from app.routes.auth.admin_auth import router as admin_auth_router
from app.routes.apis.v1.admin.profile_router import router as admin_profile

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

app.include_router(admin_auth_router,prefix="/api/admin/register", tags = ["Admin Authentication"])
app.include_router(admin_profile, prefix="/api/admin/profile", tags = ["Admin Profile"])

if __name__  == "__main__":
    import uvicorn
    uvicorn.run("main:app",port=8080, reload = True)