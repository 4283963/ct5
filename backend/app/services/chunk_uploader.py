import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import aiofiles

from app.config import settings


class ChunkUploadService:
    def __init__(self):
        self._upload_states: Dict[str, dict] = {}
        self._init_directories()

    def _init_directories(self):
        for directory in [settings.CHUNK_DIR, settings.UPLOAD_DIR, settings.PROCESSED_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    def _get_chunk_path(self, file_id: str, chunk_index: int) -> Path:
        return settings.CHUNK_DIR / f"{file_id}_chunk_{chunk_index}"

    def _get_upload_state_path(self, file_id: str) -> Path:
        return settings.CHUNK_DIR / f"{file_id}_state.json"

    async def save_chunk(
        self,
        file_id: str,
        chunk_index: int,
        total_chunks: int,
        filename: str,
        chunk_data: bytes
    ) -> bool:
        chunk_path = self._get_chunk_path(file_id, chunk_index)

        async with aiofiles.open(chunk_path, "wb") as f:
            await f.write(chunk_data)

        if file_id not in self._upload_states:
            self._upload_states[file_id] = {
                "file_id": file_id,
                "filename": filename,
                "total_chunks": total_chunks,
                "received_chunks": set(),
                "upload_time": datetime.now().isoformat()
            }

        self._upload_states[file_id]["received_chunks"].add(chunk_index)
        await self._save_upload_state(file_id)

        return True

    async def _save_upload_state(self, file_id: str):
        state_path = self._get_upload_state_path(file_id)
        state = self._upload_states.get(file_id, {})
        state_copy = dict(state)
        state_copy["received_chunks"] = list(state.get("received_chunks", set()))

        async with aiofiles.open(state_path, "w") as f:
            await f.write(json.dumps(state_copy, indent=2))

    async def _load_upload_state(self, file_id: str) -> Optional[dict]:
        state_path = self._get_upload_state_path(file_id)
        if not state_path.exists():
            return None

        async with aiofiles.open(state_path, "r") as f:
            content = await f.read()
            state = json.loads(content)
            state["received_chunks"] = set(state.get("received_chunks", []))
            return state

    async def is_upload_complete(self, file_id: str) -> bool:
        if file_id not in self._upload_states:
            state = await self._load_upload_state(file_id)
            if state:
                self._upload_states[file_id] = state
            else:
                return False

        state = self._upload_states[file_id]
        return len(state["received_chunks"]) == state["total_chunks"]

    async def merge_chunks(self, file_id: str, filename: str) -> Path:
        state = self._upload_states.get(file_id) or await self._load_upload_state(file_id)
        if not state:
            raise ValueError(f"No upload state found for file_id: {file_id}")

        output_path = settings.UPLOAD_DIR / f"{file_id}_{filename}"

        async with aiofiles.open(output_path, "wb") as outfile:
            for chunk_index in range(state["total_chunks"]):
                chunk_path = self._get_chunk_path(file_id, chunk_index)
                if not chunk_path.exists():
                    raise ValueError(f"Missing chunk {chunk_index} for file {file_id}")

                async with aiofiles.open(chunk_path, "rb") as chunk_file:
                    chunk_data = await chunk_file.read()
                    await outfile.write(chunk_data)

        await self._cleanup_chunks(file_id, state["total_chunks"])

        if file_id in self._upload_states:
            del self._upload_states[file_id]

        state_path = self._get_upload_state_path(file_id)
        if state_path.exists():
            state_path.unlink()

        return output_path

    async def _cleanup_chunks(self, file_id: str, total_chunks: int):
        for chunk_index in range(total_chunks):
            chunk_path = self._get_chunk_path(file_id, chunk_index)
            if chunk_path.exists():
                try:
                    chunk_path.unlink()
                except:
                    pass

    async def get_upload_progress(self, file_id: str) -> Dict:
        state = self._upload_states.get(file_id) or await self._load_upload_state(file_id)
        if not state:
            return {"file_id": file_id, "progress": 0, "status": "not_found"}

        received = len(state["received_chunks"])
        total = state["total_chunks"]
        progress = (received / total) * 100 if total > 0 else 0

        return {
            "file_id": file_id,
            "filename": state.get("filename"),
            "progress": round(progress, 2),
            "received_chunks": received,
            "total_chunks": total,
            "status": "complete" if progress >= 100 else "uploading"
        }


chunk_upload_service = ChunkUploadService()
