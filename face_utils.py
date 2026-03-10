"""
face_utils.py — Facial recognition helpers using DeepFace
"""
import json
import numpy as np
import io
from PIL import Image
from deepface import DeepFace
from config import settings


def image_bytes_to_array(image_bytes: bytes) -> np.ndarray:
    """Convert raw image bytes → numpy array (RGB)."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


def get_face_encoding(image_bytes: bytes) -> list[float]:
    """
    Extract a face embedding (128-d vector) from image bytes.
    Uses DeepFace with the Facenet model.
    Raises ValueError if no face is detected.
    """
    img_array = image_bytes_to_array(image_bytes)

    try:
        result = DeepFace.represent(
            img_path=img_array,
            model_name="Facenet",
            enforce_detection=True,   # raise error if no face found
            detector_backend="opencv"
        )
        # result is a list; take first face
        embedding = result[0]["embedding"]
        return embedding

    except ValueError as e:
        raise ValueError(f"No face detected in image: {e}")


def cosine_distance(enc1: list[float], enc2: list[float]) -> float:
    """
    Compute cosine distance between two embeddings.
    0.0 = identical face, 1.0 = completely different.
    """
    a = np.array(enc1)
    b = np.array(enc2)
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 1.0
    similarity = dot / norm
    distance = 1.0 - similarity
    return float(distance)


def verify_faces(stored_encoding_json: str, captured_bytes: bytes) -> dict:
    """
    Compare a stored encoding (JSON string) against a freshly captured image.

    Returns:
        {
          "match": True/False,
          "distance": 0.23,          # lower = more similar
          "confidence": 77.0         # percentage similarity
        }
    """
    stored_enc = json.loads(stored_encoding_json)

    try:
        captured_enc = get_face_encoding(captured_bytes)
    except ValueError as e:
        return {"match": False, "distance": 1.0, "confidence": 0.0, "error": str(e)}

    distance = cosine_distance(stored_enc, captured_enc)
    confidence = round((1.0 - distance) * 100, 2)
    match = distance < settings.FACE_THRESHOLD

    return {
        "match": match,
        "distance": round(distance, 4),
        "confidence": confidence
    }
