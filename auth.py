"""
routes/auth.py
POST /api/admin/login
POST /api/admin/register  (first-time setup only)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

from database import get_db, Admin
from auth_utils import hash_password, verify_password, create_token

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    setup_key: str   # a one-time key to prevent random registrations


SETUP_KEY = "FACEAUTH_SETUP_2025"  # change this after first admin is created


@router.post("/login")
async def admin_login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).where(Admin.email == body.email))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(str(admin.id), admin.email)
    return {
        "token": token,
        "admin": {"name": admin.name, "email": admin.email}
    }


@router.post("/register")
async def admin_register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create first admin account. Protected by a setup key."""
    if body.setup_key != SETUP_KEY:
        raise HTTPException(status_code=403, detail="Invalid setup key")

    existing = await db.execute(select(Admin).where(Admin.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = Admin(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name
    )
    db.add(admin)
    await db.commit()
    return {"message": "Admin created successfully"}
