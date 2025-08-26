from db.mongo import get_db
from models.domain.types.platform import Platform
from fastapi import HTTPException
from repositories.mongo_repository import MongoRepository
from repositories.types_repositories.mission_repository import MissionRepository


class PlatformRepository(MongoRepository[Platform]):
    def __init__(self):
        super().__init__(collection=get_db()["platforms"], model_cls=Platform)
        self.mission_repo = MissionRepository()
        
        
    async def delete_item(self, item_id: str):
        if await self.mission_repo.exists_by_platform_id(item_id):
            raise HTTPException(status_code=409, detail="cant delete platform that belongs to mission.")
        return await super().delete_item(item_id)