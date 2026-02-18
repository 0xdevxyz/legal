"""
File Storage Service
Handles file uploads for AI Compliance documentation
Supports local storage (default) and can be extended for S3
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
import aiofiles
import mimetypes

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.txt', '.html', '.htm'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-excel',
    'text/plain',
    'text/html'
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class FileStorageService:
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.environ.get(
            'FILE_STORAGE_PATH', 
            '/app/uploads'
        )
        self._ensure_storage_dir()
    
    def _ensure_storage_dir(self):
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        ai_docs_path = Path(self.storage_path) / 'ai_documentation'
        ai_docs_path.mkdir(parents=True, exist_ok=True)
    
    def _get_user_dir(self, user_id: int) -> Path:
        user_dir = Path(self.storage_path) / 'ai_documentation' / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir
    
    def _generate_filename(self, original_filename: str) -> str:
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = "".join(c for c in Path(original_filename).stem if c.isalnum() or c in '-_')[:50]
        return f"{timestamp}_{safe_name}_{unique_id}{ext}"
    
    def validate_file(self, filename: str, content_type: str, file_size: int) -> Tuple[bool, str]:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return False, f"Dateityp nicht erlaubt. Erlaubt: {', '.join(ALLOWED_EXTENSIONS)}"
        
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            guessed_type = mimetypes.guess_type(filename)[0]
            if guessed_type not in ALLOWED_MIME_TYPES:
                return False, f"MIME-Type nicht erlaubt: {content_type}"
        
        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f"Datei zu groß. Maximum: {max_mb}MB"
        
        return True, "OK"
    
    async def save_file(
        self, 
        user_id: int, 
        file_content: bytes, 
        original_filename: str,
        system_id: str = None
    ) -> Dict[str, Any]:
        user_dir = self._get_user_dir(user_id)
        
        if system_id:
            system_dir = user_dir / system_id
            system_dir.mkdir(parents=True, exist_ok=True)
            target_dir = system_dir
        else:
            target_dir = user_dir
        
        new_filename = self._generate_filename(original_filename)
        file_path = target_dir / new_filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        relative_path = str(file_path.relative_to(self.storage_path))
        
        return {
            "file_path": str(file_path),
            "relative_path": relative_path,
            "filename": new_filename,
            "original_filename": original_filename,
            "file_size": len(file_content),
            "file_hash": file_hash,
            "content_type": mimetypes.guess_type(original_filename)[0] or 'application/octet-stream'
        }
    
    async def get_file(self, relative_path: str) -> Optional[bytes]:
        file_path = Path(self.storage_path) / relative_path
        
        if not file_path.exists():
            return None
        
        if not str(file_path.resolve()).startswith(str(Path(self.storage_path).resolve())):
            return None
        
        async with aiofiles.open(file_path, 'rb') as f:
            return await f.read()
    
    async def delete_file(self, relative_path: str) -> bool:
        file_path = Path(self.storage_path) / relative_path
        
        if not file_path.exists():
            return False
        
        if not str(file_path.resolve()).startswith(str(Path(self.storage_path).resolve())):
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def get_download_url(self, relative_path: str, base_url: str = "") -> str:
        return f"{base_url}/api/ai/documentation/file/{relative_path}"


file_storage = FileStorageService()
