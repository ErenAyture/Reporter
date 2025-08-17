from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter(prefix="/download")

BASE_OUTPUT_DIR = os.path.join(os.getcwd(), "results")

@router.get("/{task_id}")
def download_task_result(task_id: int):
    zip_path = os.path.join(BASE_OUTPUT_DIR, f"{task_id}.zip")

    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Archive not found.")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"task_{task_id}.zip"
    )
