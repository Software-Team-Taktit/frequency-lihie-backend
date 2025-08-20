from models.domain.types.users.user import User
from repositories.mongo_repository import MongoRepository
from db.mongo import get_db

class UserRepository(MongoRepository[User]):
    
    def __init__(self):
        super().__init__(collection=get_db()["users"], model_cls=User)
        
    async def get_by_personal_id(self, personal_id:str) -> User:
        doc = await self.collection.find_one({"personal_id": personal_id})
        return User(**doc) if doc else None