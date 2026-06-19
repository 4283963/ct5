from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Optional

from app.models.schemas import (
    UploadChunkResponse,
    UploadCompleteResponse,
    FileInfo,
)
from app.services.chunk_uploader import chunk_upload_service
from app.services.data_processor import data_processor

router = APIRouter()


@router.post("/chunk", response_model=UploadChunkResponse)
async def upload_chunk(
    file_id: str = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    filename: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        chunk_data = await file.read()

        await chunk_upload_service.save_chunk(
            file_id=file_id,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            filename=filename,
            chunk_data=chunk_data,
        )

        return UploadChunkResponse(
            file_id=file_id,
            chunk_index=chunk_index,
            received=True,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk upload failed: {str(e)}")


@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    file_id: str = Form(...),
    filename: str = Form(...),
    total_chunks: int = Form(...),
):
    try:
        is_complete = await chunk_upload_service.is_upload_complete(file_id)
        if not is_complete:
            raise HTTPException(status_code=400, detail="Upload not complete")

        merged_path = await chunk_upload_service.merge_chunks(file_id, filename)

        df, voyage_ids = data_processor.parse_file(merged_path)
        saved_voyage_ids = data_processor.save_processed_data(df, file_id)

        return UploadCompleteResponse(
            file_id=file_id,
            status="success",
            total_records=len(df),
            voyage_ids=saved_voyage_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload completion failed: {str(e)}")


@router.get("/progress/{file_id}")
async def get_upload_progress(file_id: str):
    try:
        progress = await chunk_upload_service.get_upload_progress(file_id)
        return progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct")
async def direct_upload(file: UploadFile = File(...)):
    try:
        import uuid

        file_id = str(uuid.uuid4())
        data = await file.read()

        df, voyage_ids = data_processor.parse_bytes(data, file.filename or "data.csv")
        saved_voyage_ids = data_processor.save_processed_data(df, file_id)

        return {
            "file_id": file_id,
            "filename": file.filename,
            "status": "success",
            "total_records": len(df),
            "voyage_ids": saved_voyage_ids,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/files", response_model=list[FileInfo])
async def list_uploaded_files():
    try:
        voyages = data_processor.get_all_voyages()
        file_groups: dict = {}

        for voyage in voyages:
            if voyage.voyage_id not in file_groups:
                file_groups[voyage.voyage_id] = {
                    "file_id": voyage.voyage_id,
                    "filename": f"{voyage.vessel_name}_{voyage.departure_port}_to_{voyage.arrival_port}",
                    "upload_time": voyage.start_time,
                    "status": "processed",
                    "total_records": 0,
                    "voyage_count": 0,
                }
            file_groups[voyage.voyage_id]["voyage_count"] += 1

        return list(file_groups.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
