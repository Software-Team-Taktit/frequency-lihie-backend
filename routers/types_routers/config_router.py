from fastapi import APIRouter, Depends, HTTPException, status
from models.helpers.frequency_range_config import FrequencyRangeConfig
from repositories.types_repositories.frequency_range_repository import FrequencyRangeRepository
from deps.auth import require_admin

config_router = APIRouter(prefix="/config", tags=["config"])

def get_repo():
    return FrequencyRangeRepository()

@config_router.get("/frequency-range", response_model=FrequencyRangeConfig)
async def get_frequency_range(repo: FrequencyRangeRepository = Depends(get_repo)):
    return await repo.get()

@config_router.put("/frequency-range", response_model=FrequencyRangeConfig)
async def update_frequency_range(
    cfg: FrequencyRangeConfig,
    repo: FrequencyRangeRepository = Depends(get_repo),
    _admin=Depends(require_admin)
):
    try:
        return await repo.set(cfg)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )