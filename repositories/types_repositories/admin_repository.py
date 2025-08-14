from repositories.mongo_repository import MongoRepository
from db.mongo import get_db
from models.domain.types.users.admin import Admin

class AdminRepository(MongoRepository[Admin]):
    def __init__(self):
        super().__init__(collection=get_db()["admins"], model_cls=Admin)