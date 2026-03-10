"""
routes/students.py
POST   /api/students          — enrol a student
GET    /api/students          — list all students
DELETE /api/students/{reg}    — remove a student
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
import json

from database import get_db, Student
from face_utils import get_face_encoding
from cloudinary_utils import upload_student_photo
from auth_utils import require_admin

router = APIRouter()


@router.post("/students")
async def enrol_student(
    reg_number: str = Form(...),
    full_name: str = Form(...),
    photo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    """
    Enrol a new student.
    Accepts multipart form with reg_number, full_name, and a photo file.
    Extracts face encoding and stores it in the DB.
    """
    reg_number = reg_number.strip().upper()

    # Check for duplicate
    existing = await db.execute(
        select(Student).where(Student.reg_number == reg_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"{reg_number} is already enrolled")

    image_bytes = await photo.read()

    # Extract face encoding (raises ValueError if no face detected)
    try:
        encoding = get_face_encoding(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Upload photo to Cloudinary
    try:
        photo_url = upload_student_photo(image_bytes, reg_number)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

    student = Student(
        reg_number=reg_number,
        full_name=full_name.strip(),
        photo_url=photo_url,
        face_encoding=json.dumps(encoding)
    )
    db.add(student)
    await db.commit()

    return {
        "message": "Student enrolled successfully",
        "reg_number": reg_number,
        "full_name": full_name,
        "photo_url": photo_url
    }


@router.get("/students")
async def list_students(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    result = await db.execute(select(Student).order_by(Student.created_at.desc()))
    students = result.scalars().all()

    return {
        "total": len(students),
        "students": [
            {
                "reg_number": s.reg_number,
                "full_name": s.full_name,
                "photo_url": s.photo_url,
                "enrolled_at": s.created_at.isoformat()
            }
            for s in students
        ]
    }


@router.delete("/students/{reg_number}")
async def remove_student(
    reg_number: str,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(require_admin)
):
    reg_number = reg_number.strip().upper()
    result = await db.execute(
        select(Student).where(Student.reg_number == reg_number)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    await db.execute(delete(Student).where(Student.reg_number == reg_number))
    await db.commit()
    return {"message": f"{reg_number} removed successfully"}
