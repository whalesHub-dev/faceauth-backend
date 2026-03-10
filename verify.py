"""
routes/verify.py
POST /api/verify  ← called by ESP32-CAM
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from database import get_db, Student, VerificationLog, VerificationResult
from face_utils import verify_faces
from cloudinary_utils import upload_captured_photo
from auth_utils import require_esp32_key

router = APIRouter()


@router.post("/verify")
async def verify_student(
    reg_number: str = Form(...),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_esp32_key)   # validates x-api-key header
):
    """
    ESP32 sends:
      - reg_number (form field)
      - image      (JPEG file)
      - x-api-key  (header)

    Returns:
      {"status": "APPROVED", "confidence": 87.5}
      {"status": "REJECTED", "confidence": 23.1}
      {"status": "REJECTED", "error": "Not enrolled"}
    """
    # 1. Look up student in DB
    result = await db.execute(
        select(Student).where(Student.reg_number == reg_number.strip())
    )
    student = result.scalar_one_or_none()

    if not student:
        # Log the failed attempt
        log = VerificationLog(
            reg_number=reg_number,
            result=VerificationResult.REJECTED,
            confidence=0.0
        )
        db.add(log)
        await db.commit()
        return {"status": "REJECTED", "error": "Not enrolled"}

    # 2. Read captured image bytes
    image_bytes = await image.read()

    # 3. Run face comparison
    face_result = verify_faces(student.face_encoding, image_bytes)

    status = "APPROVED" if face_result["match"] else "REJECTED"
    confidence = face_result["confidence"]

    # 4. Upload captured image to Cloudinary (for audit log)
    captured_url = None
    try:
        captured_url = upload_captured_photo(image_bytes, reg_number)
    except Exception as e:
        print(f"Warning: could not upload captured image: {e}")

    # 5. Save log
    log = VerificationLog(
        reg_number=reg_number,
        result=VerificationResult[status],
        confidence=confidence,
        captured_img_url=captured_url
    )
    db.add(log)
    await db.commit()

    print(f"[VERIFY] {reg_number} → {status} ({confidence}%)")

    return {
        "status": status,
        "confidence": confidence,
        "student_name": student.full_name if status == "APPROVED" else None
    }
