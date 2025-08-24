from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase

SESSION_TTL_DAYS = 30

class SessionRepository:
    def __init__(self, db:AsyncIOMotorDatabase):
        self.col = db["sessions"]
        
    async def create(self, user_id: str) -> str:
        sid = uuid4().hex
        await self.col.insert_one({
            "_id" : sid,
            "user_id" : user_id,
            "created_at" : datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)
        })
        return sid
    
    async def get(self, session_id: str) -> Optional[dict]:
        return await self.col.find_one({"_id" : session_id})
    
    async def delete(self, session_id: str) -> None:
        await self.col.delete_one({"_id" : session_id})