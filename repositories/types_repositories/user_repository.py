from uuid import UUID
from typing import List
from models.domain.types.users.user import User
from repositories.base_repository import BaseRepository
from db.mongo import db

class UserRepository(BaseRepository[User]):
    def __init__(self):
        self.collection = db["users"]

    async def get_all(self) -> List[User]:
        cursor = self.collection.find({})
        users = await cursor.to_list(length=None)
        return [User(**u) for u in users]