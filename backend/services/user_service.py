"""User management service"""
from typing import List, Optional
from datetime import datetime

class UserService:
    async def create_user(self, email: str, password: str) -> dict:
        return {"id": "user_123", "email": email, "created_at": datetime.utcnow()}
    
    async def get_user(self, user_id: str) -> Optional[dict]:
        return {"id": user_id, "email": "user@example.com"}
