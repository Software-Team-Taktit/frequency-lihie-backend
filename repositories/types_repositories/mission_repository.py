from db.mongo import db
from models.domain.types.mission import Mission
from repositories.mongo_repository import MongoRepository

class MissionRepository(MongoRepository[Mission]):
    def __init__(self):
        super().__init__(collection=db["missions"], model_cls=Mission)
