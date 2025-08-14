from db.mongo import get_db
from models.domain.types.platform import Platform
from repositories.mongo_repository import MongoRepository

class PlatformRepository(MongoRepository[Platform]):
    def __init__(self):
        super().__init__(collection=get_db()["platforms"], model_cls=Platform)