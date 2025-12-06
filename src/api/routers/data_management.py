from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from src.services.data_service import data_service
from src.services.qdrant_service import qdrant_service
from src.schemas.user import UserSession, UserRole
from src.api import deps
import os

router = APIRouter()

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Upload Excel file, process it, and index to Qdrant (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        content = await file.read()
        # Process Excel
        result = data_service.process_excel_upload(content, file.filename)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
            
        json_path = result["json_file"]
        
        # Upload to Qdrant
        upload_result = qdrant_service.upload_from_json(json_path)
        
        if not upload_result["success"]:
             raise HTTPException(status_code=500, detail=upload_result.get("error", "Unknown Qdrant error"))
             
        return {
            "message": "Upload successful",
            "processed_records": result["total_records"],
            "uploaded_records": upload_result["uploaded"],
            "collection": upload_result["collection"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get data statistics (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    try:
        collection_name = qdrant_service.collection_name
        count = qdrant_service.client.count(collection_name).count
        return {
            "collection": collection_name,
            "count": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_upload_history(
    current_user: UserSession = Depends(deps.get_current_user)
) -> Any:
    """
    Get upload history (Admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
        
    history_data = []
    if data_service.upload_index:
        for filename, path in data_service.upload_index.items():
            try:
                mod_time = os.path.getmtime(path)
                history_data.append({
                    "filename": filename,
                    "timestamp": mod_time,
                    "path": path
                })
            except:
                pass
    return history_data
