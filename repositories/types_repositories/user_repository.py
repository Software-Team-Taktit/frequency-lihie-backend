from models.domain.types.users.user import User
from repositories.mongo_repository import MongoRepository
from db.mongo import get_db

class UserRepository(MongoRepository[User]):
    
    def __init__(self):
        super().__init__(collection=get_db()["users"], model_cls=User)
        