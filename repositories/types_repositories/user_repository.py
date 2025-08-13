from models.domain.types.users.user import User
from repositories.mongo_repository import MongoRepository
from db.mongo import db

class UserRepository(MongoRepository[User]):
    
    def __init__(self):
        super().__init__(collection=db["users"], model_cls=User)
        