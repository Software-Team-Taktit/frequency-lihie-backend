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
    
    async def get_by_id(self, item_id) -> User:
        user_dict = await self.collection.find_one({"id": str(item_id)})
        if not user_dict:
            return None
        return User(**user_dict)
    
    async def add_item(self, item: User) -> User:
        await self.collection.insert_one(item.model_dump())
        return item
    
    async def delete_item(self, item_id: UUID) -> bool:
        result = await self.collection.delete_one({"id": str(item_id)})
        return result.deleted_count > 0
    
    async def update_item(self, item_id: UUID, item: User) -> User:
        result = await self.collection.replace_one({"id": str(item_id)})
        if result.matched_count > 0:
            return None
        return item