"""
routes/logs.py
GET /api/logs              — all logs (optional ?date=YYYY-MM-DD)
GET /api/logs/{reg_number} — logs for one student
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import datetime

from database import get_db, VerificationLog
from auth_utils import require_admin

router = APIRouter()


@router.get("/logs")
async def get_logs(
    date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    query = select(VerificationLog).order_by(VerificationLog.timestamp.desc())

    if date:
        try:
            day = datetime.date.fromisoformat(date)
            start = datetime.datetime.combine(day, datetime.time.min)
            end   = datetime.datetime.combine(day, datetime.time.max)
            query = query.where(
                VerificationLog.timestamp >= start,
                VerificationLog.timestamp <= end
            )
        except ValueError:
            pass  # invalid date format, ignore filter

    result = await db.execute(query)
    logs = result.scalars().all()

    approved = sum(1 for l in logs if l.result.value == "APPROVED")
    rejected = len(logs) - approved

    return {
        "total": len(logs),
        "approved": approved,
        "rejected": rejected,
        "logs": [
            {
                "reg_number": l.reg_number,
                "result": l.result.value,
                "confidence": l.confidence,
                "captured_image": l.captured_img_url,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ]
    }


@router.get("/logs/{reg_number}")
async def get_student_logs(
    reg_number: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(
        select(VerificationLog)
        .where(VerificationLog.reg_number == reg_number.strip().upper())
        .order_by(VerificationLog.timestamp.desc())
    )
    logs = result.scalars().all()

    return {
        "reg_number": reg_number,
        "total_attempts": len(logs),
        "logs": [
            {
                "result": l.result.value,
                "confidence": l.confidence,
                "captured_image": l.captured_img_url,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ]
    }
