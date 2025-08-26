from db.mongo import get_db
from models.domain.types.mission import Mission
from repositories.mongo_repository import MongoRepository

class MissionRepository(MongoRepository[Mission]):
    def __init__(self):
        super().__init__(collection=get_db()["missions"], model_cls=Mission)
        
    async def exists_by_platform_id(self, platform_id: str):
        return await self.collection.count_documents({"platform_id": platform_id}, limit = 1) > 0
    