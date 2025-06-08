from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from shared import models
import os
from fastapi.responses import FileResponse

router = APIRouter()

UPLOAD_DIR = "uploads/jd_resume"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload/{user_id}/{file_type}", summary="Upload JD or Resume")
def upload_file(user_id: int, file_type: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file_type not in ["jd", "resume"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    upload_dir = f"uploads/jd_resume/{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file_type}_{file.filename}"
    # Remove old file if exists
    for f in os.listdir(upload_dir):
        if f.startswith(file_type + "_"):
            os.remove(os.path.join(upload_dir, f))
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    # Update file path in User table if such a column exists
    user = db.query(models.User).filter_by(id=user_id).first()
    if user:
        setattr(user, f"{file_type}_path", file_path)
        db.commit()
    return {"filename": file.filename, "path": file_path}

@router.get("/preview/{user_id}/{file_type}", response_class=FileResponse, summary="Preview JD or Resume")
def preview_file(user_id: int, file_type: str):
    dir_path = f"{UPLOAD_DIR}/{user_id}"
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="No files found")
    for f in os.listdir(dir_path):
        if f.startswith(file_type + "_"):
            return FileResponse(f"{dir_path}/{f}")
    raise HTTPException(status_code=404, detail="File not found")

@router.delete("/delete/{user_id}/{file_type}", summary="Delete JD or Resume")
def delete_file(user_id: int, file_type: str):
    dir_path = f"{UPLOAD_DIR}/{user_id}"
    if not os.path.exists(dir_path):
        raise HTTPException(status_code=404, detail="No files found")
    deleted = False
    for f in os.listdir(dir_path):
        if f.startswith(file_type + "_"):
            os.remove(f"{dir_path}/{f}")
            deleted = True
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")
    return {"detail": "File deleted"}