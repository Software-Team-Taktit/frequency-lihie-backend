from models.domain.types.users.user import User
from repositories.mongo_repository import MongoRepository
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError
from db.mongo import get_db


class UserRepository(MongoRepository[User]):

    def __init__(self):
        super().__init__(collection=get_db()["users"], model_cls=User)

    async def add_item(self, item: User) -> User:
        item.id = item.personal_id

        existing_user = await get_db()["users"].find_one({"personal_id": item.personal_id})
        existing_admin = await get_db()["admins"].find_one({"personal_id": item.personal_id})

        if existing_user or existing_admin:
            raise HTTPException(
                status_code=409,
                detail="personal id already exists."
            )

        try:
            await self.collection.insert_one(item.model_dump())
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail="personal id already exists."
            )

        return item

    async def get_by_personal_id(self, personal_id: str) -> User:
        doc = await self.collection.find_one({"personal_id": personal_id})
        return User(**doc) if doc else None