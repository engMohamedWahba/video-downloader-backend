from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import yt_dlp
import uuid
import os
import shutil

app = FastAPI()

# =========================
# إعداد مجلد التحميلات
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

if os.path.exists(DOWNLOAD_DIR):
    shutil.rmtree(DOWNLOAD_DIR)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# نموذج الطلب
# =========================

class DownloadRequest(BaseModel):
    url: str

# =========================
# Health Check
# =========================

@app.get("/")
def root():
    return {"status": "server running"}

# =========================
# Download Endpoint
# =========================

@app.post("/api/download")
def download_video(data: DownloadRequest):

    try:
        task_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_DIR, f"{task_id}.mp4")

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_path,
            "noplaylist": True,
            "quiet": True,

            # تحسينات بسيطة ضد الحظر
            "geo_bypass": True,
            "nocheckcertificate": True,

            "http_headers": {
                "User-Agent": "Mozilla/5.0",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://www.youtube.com/"
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([data.url])

        return {
            "status": "ready",
            "task_id": task_id,
            "download_url": f"/file/{task_id}.mp4"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# =========================
# File Serving Endpoint
# =========================

@app.get("/file/{filename}")
def get_file(filename: str):

    file_path = os.path.join(DOWNLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "File not found",
                "checked_path": file_path
            }
        )

    try:
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )
