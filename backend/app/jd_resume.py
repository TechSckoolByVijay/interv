from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from shared import models
import os
from fastapi.responses import FileResponse

from shared.common import (
    send_message_to_service_bus,
    FileProcessPayload,
    ServiceBusMessageModel
)
from shared.logger import logger
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads/jd_resume")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload/{user_id}/{file_type}", summary="Upload JD or Resume")
async def upload_file(user_id: int, file_type: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info(f"Received upload request: user_id={user_id}, file_type={file_type}, filename={file.filename}")
    if file_type not in ["jd", "resume"]:
        logger.warning(f"Invalid file type received: {file_type}")
        raise HTTPException(status_code=400, detail="Invalid file type")
    #upload_dir = f"uploads/jd_resume/{user_id}"
    upload_dir = f"{UPLOAD_DIR}/jd_resume/{user_id}"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file_type}_{file.filename}"
    logger.debug(f"Upload directory ensured: {upload_dir}")
    # Remove old file if exists
    for f in os.listdir(upload_dir):
        if f.startswith(file_type + "_"):
            logger.info(f"Removing old file: {os.path.join(upload_dir, f)}")
            os.remove(os.path.join(upload_dir, f))
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    logger.info(f"File saved to: {file_path}")
    # Update file path in User table if such a column exists
    user = db.query(models.User).filter_by(id=user_id).first()
    if user:
        setattr(user, f"{file_type}_path", file_path)
        db.commit()
        logger.info(f"User {user_id} record updated with {file_type}_path: {file_path}")
    else:
        logger.warning(f"User with id {user_id} not found in database.")

    # Enqueue message to Service Bus
    payload = FileProcessPayload(file_path=file_path, file_type=file_type)
    message = ServiceBusMessageModel(
        correlationId=str(uuid.uuid4()),
        session_id=str(user_id),
        action_type="doc_upload",
        user_id=user_id,
        timestamp=datetime.utcnow().isoformat(),
        status="uploaded",
        payload=payload,
    )
    logger.info(f"Enqueuing message to Service Bus for user_id={user_id}, file_type={file_type}")
    logger.info(f"message={message}")
    try:
        send_message_to_service_bus(message.dict())
        logger.info("Message successfully enqueued to Service Bus.")
    except Exception as e:
        logger.error(f"Failed to enqueue message to Service Bus: {e}")

    return {"filename": file.filename, "path": file_path}

@router.get("/preview/{user_id}/{file_type}", summary="Preview JD or Resume")
def preview_file(user_id: int, file_type: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if file_type == "jd":
        if user.jd_text:
            return {"text": user.jd_text}
        else:
            raise HTTPException(status_code=404, detail="JD text not found")
    elif file_type == "resume":
        if user.resume_text:
            return {"text": user.resume_text}
        else:
            raise HTTPException(status_code=404, detail="Resume text not found")
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")

@router.delete("/delete/{user_id}/{file_type}", summary="Delete JD or Resume")
def delete_file(user_id: int, file_type: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    dir_path = f"{UPLOAD_DIR}/{user_id}"
    deleted = False
    if os.path.exists(dir_path):
        for f in os.listdir(dir_path):
            if f.startswith(file_type + "_"):
                os.remove(f"{dir_path}/{f}")
                deleted = True
    # Update DB fields
    if file_type == "jd":
        user.jd_path = None
        user.jd_text = None
        user.jd_status = "NOT_AVAILABLE"
        db.commit()
        return {"detail": "JD deleted"}
    elif file_type == "resume":
        user.resume_path = None
        user.resume_text = None
        user.resume_status = "NOT_AVAILABLE"
        db.commit()
        return {"detail": "Resume deleted"}
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")