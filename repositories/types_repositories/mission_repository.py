from datetime import datetime, timedelta, timezone

from db.mongo import get_db
from models.domain.types.mission import Mission
from repositories.mongo_repository import MongoRepository


class MissionRepository(MongoRepository[Mission]):
    def __init__(self):
        super().__init__(collection=get_db()["missions"], model_cls=Mission)

    async def exists_by_platform_id(self, platform_id: str):
        return await self.collection.count_documents(
            {"platform_id": platform_id},
            limit=1
        ) > 0

    async def exists_by_owner_id(self, owner_id: str) -> bool:
        return await self.collection.count_documents(
            {"owner_id": str(owner_id)},
            limit=1
        ) > 0

    def _as_utc(self, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)

        return value

    async def _refresh_active_status(self, mission: Mission) -> Mission:
        if mission.expires_at is None:
            return mission

        expires_at = self._as_utc(mission.expires_at)
        now = datetime.now(timezone.utc)

        if mission.is_active and now >= expires_at:
            mission.is_active = False
            mission.deactivated_at = expires_at

            await self.collection.update_one(
                {"id": mission.id},
                {
                    "$set": {
                        "is_active": False,
                        "deactivated_at": expires_at,
                    }
                }
            )

        return mission

    async def delete_inactive_older_than(self, days: int = 7) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.collection.delete_many(
            {
                "is_active": False,
                "deactivated_at": {
                    "$lte": cutoff
                }
            }
        )

        return result.deleted_count

    async def get_all(self):
        missions = await super().get_all()
        refreshed = []

        for mission in missions:
            refreshed.append(await self._refresh_active_status(mission))

        return refreshed

    async def get_active(self):
        missions = await self.get_all()

        return [
            mission for mission in missions
            if mission.is_active is True
        ]

    async def get_by_id(self, item_id: str) -> Mission | None:
        mission = await super().get_by_id(item_id)

        if not mission:
            return None

        return await self._refresh_active_status(mission)