from typing import TypeVar, Generic, List, Type
from uuid import UUID
from motor.motor_asyncio import AsyncIOMotorCollection
from repositories.base_repository import BaseRepository

T = TypeVar("T")

class MongoRepository(BaseRepository[T], Generic[T]):
    def __init__(self, collection: AsyncIOMotorCollection, model_cls: Type[T]):
        self.collection = collection
        self.model_cls = model_cls
        
    async def get_all(self):
        cursor = self.collection.find({})
        docs = await cursor.to_list(length=None)
        return [self.model_cls(**doc) for doc in docs]
    
    async def get_by_id(self, item_id: str) -> T:
        doc = await self.collection.find_one({"id": item_id})
        if not doc:
            return None
        return self.model_cls(**doc)

    async def add_item(self, item: T) -> T:
        await self.collection.insert_one(item.model_dump())
        return item
    
    async def delete_item(self, item_id: str) -> bool:
        result = await self.collection.delete_one({"id": item_id})
        return result.deleted_count > 0

    async def update_item(self, item_id: str, item: T) -> T:
        result = await self.collection.replace_one({"id": item_id}, item.model_dump())
        if result.matched_count == 0:
            return None
        return item