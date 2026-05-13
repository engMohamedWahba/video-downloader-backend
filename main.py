from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import yt_dlp
import uuid
import os
import shutil

app = FastAPI()

# حذف مجلد التحميلات القديم عند تشغيل السيرفر
if os.path.exists("downloads"):
    shutil.rmtree("downloads")

os.makedirs("downloads", exist_ok=True)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"

class DownloadRequest(BaseModel):
    url: str

@app.get("/")
def root():
    return {"status": "server running"}

@app.post("/api/download")
def download_video(data: DownloadRequest):

    try:
        task_id = str(uuid.uuid4())

        output_path = f"{DOWNLOAD_DIR}/{task_id}.mp4"

        ydl_opts = {
            "format": "mp4",
            "outtmpl": output_path,
            "noplaylist": True,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([data.url])

        return {
            "status": "ready",
            "task_id": task_id,
            "download_url": f"/file/{task_id}.mp4"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/file/{filename}")
def get_file(filename: str):

    file_path = f"{DOWNLOAD_DIR}/{filename}"

    if not os.path.exists(file_path):
        return {
            "status": "error",
            "message": "File not found"
        }

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
