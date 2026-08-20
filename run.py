"""
EduvisionAI - Smart AI CCTV Attendance System
Developed by Tensor Titans
Single command: python run.py
"""
import os, sys, webbrowser, threading, time
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.seed_data import seed
from backend.config import FRONTEND_DIR
from backend.routers import auth_router, admin, teacher, parent, attendance

app = FastAPI(title="EduvisionAI", description="By Tensor Titans", version="1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
                   allow_headers=["*"])

# API routers
app.include_router(auth_router.router)
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(parent.router)
app.include_router(attendance.router)


@app.get("/")
def home():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


# Serve frontend static files
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


def _open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    print("=" * 55)
    print("   🎓  EduvisionAI  |  Developed by Tensor Titans")
    print("=" * 55)
    try:
        init_db()
        seed()
    except Exception as e:
        print(f"[Startup] ⚠ Init warning (self-healed): {e}")
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)