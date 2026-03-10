"""
cloudinary_utils.py — Upload images to Cloudinary
"""
import cloudinary
import cloudinary.uploader
import io
from config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_image(image_bytes: bytes, folder: str, public_id: str) -> str:
    """
    Upload image bytes to Cloudinary.
    Returns the secure URL string.
    """
    result = cloudinary.uploader.upload(
        io.BytesIO(image_bytes),
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image"
    )
    return result["secure_url"]


def upload_student_photo(image_bytes: bytes, reg_number: str) -> str:
    """Upload a student enrolment photo."""
    safe_reg = reg_number.replace("/", "_").replace(" ", "_")
    return upload_image(image_bytes, "faceauth/students", f"student_{safe_reg}")


def upload_captured_photo(image_bytes: bytes, reg_number: str) -> str:
    """Upload a captured (verification attempt) photo."""
    import datetime
    safe_reg = reg_number.replace("/", "_").replace(" ", "_")
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return upload_image(image_bytes, "faceauth/captures", f"cap_{safe_reg}_{ts}")
