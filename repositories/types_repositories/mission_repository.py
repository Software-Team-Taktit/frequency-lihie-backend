from datetime import datetime, timezone
from db.mongo import get_db
from models.domain.types.mission import Mission
from repositories.mongo_repository import MongoRepository

class MissionRepository(MongoRepository[Mission]):
    def __init__(self):
        super().__init__(collection=get_db()["missions"], model_cls=Mission)
        
    async def exists_by_platform_id(self, platform_id: str):
        return await self.collection.count_documents({"platform_id": platform_id}, limit = 1) > 0
    
    async def _refresh_active_status(self, mission: Mission) -> Mission:
        if mission.expires_at is None:
            return mission

        expires_at = mission.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        if mission.is_active and now >= expires_at:
            mission.is_active = False
            await self.collection.update_one(
                {"id": mission.id},
                {"$set": {"is_active": False}}
            )

        return mission
    
    async def get_all(self):
        missions = await super().get_all()
        refreshed = []

        for mission in missions:
            refreshed.append(await self._refresh_active_status(mission))

        return refreshed

    async def get_by_id(self, item_id: str) -> Mission:
        mission = await super().get_by_id(item_id)
        if not mission:
            return None
        return await self._refresh_active_status(mission)
        
    