"""
database.py — Async PostgreSQL with SQLAlchemy
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Float, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime
import enum

from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# ── Models ────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reg_number   = Column(String(50), unique=True, nullable=False, index=True)
    full_name    = Column(String(100), nullable=False)
    photo_url    = Column(Text, nullable=False)       # Cloudinary URL
    face_encoding= Column(Text, nullable=False)       # JSON array of 128 floats
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)


class VerificationResult(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reg_number       = Column(String(50), nullable=False, index=True)
    result           = Column(Enum(VerificationResult), nullable=False)
    confidence       = Column(Float, nullable=True)    # similarity score
    captured_img_url = Column(Text, nullable=True)     # Cloudinary URL
    timestamp        = Column(DateTime, default=datetime.datetime.utcnow, index=True)


class Admin(Base):
    __tablename__ = "admins"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    name          = Column(String(100), nullable=False)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)


# ── DB session dependency ─────────────────────────────────
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ── Create all tables on startup ─────────────────────────
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables ready")
