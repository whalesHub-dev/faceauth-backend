"""
FaceAuth Exam System — FastAPI Backend
======================================
Endpoints:
  POST /api/verify          ← ESP32 sends image + reg_number
  POST /api/admin/login     ← Admin login, returns JWT
  POST /api/students        ← Enrol a student (admin only)
  GET  /api/students        ← List all students (admin only)
  DELETE /api/students/{reg} ← Remove a student (admin only)
  GET  /api/logs            ← All verification logs (admin only)
  GET  /api/ping            ← Health check
"""

from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

from database import init_db
from routes import verify, students, auth, logs

app = FastAPI(title="FaceAuth API", version="1.0.0")

# ── CORS (allow React frontend on any origin) ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your Vercel URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup: create DB tables ──────────────────────────────
@app.on_event("startup")
async def startup():
    await init_db()

# ── Routers ────────────────────────────────────────────────
app.include_router(verify.router,   prefix="/api")
app.include_router(auth.router,     prefix="/api/admin")
app.include_router(students.router, prefix="/api")
app.include_router(logs.router,     prefix="/api")

@app.get("/api/ping")
async def ping():
    return {"status": "ok", "service": "FaceAuth API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
