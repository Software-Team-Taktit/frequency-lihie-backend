from db.mongo import get_db
from models.helpers.frequency_range_config import FrequencyRangeConfig

class FrequencyRangeRepository:
    def __init__(self):
        self.collection = get_db()["config"]
        
    async def get(self) -> FrequencyRangeConfig:
        doc = await self.collection.find_one({"id": "frequency_range"})
        if not doc:
            # default אם אין עדיין מסמך
            return FrequencyRangeConfig(min_mhz=500, max_mhz=1600)
        return FrequencyRangeConfig(**doc)
    
    async def set(self, cfg: FrequencyRangeConfig) -> FrequencyRangeConfig:
        await self.collection.update_one(
            {"id": "frequency_range"},
            {"$set": cfg.model_dump()},
            upsert=True
        )
        return cfg