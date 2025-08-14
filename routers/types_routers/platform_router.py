from ..base_crud_router import BaseCrudRouter
from models.domain.types.platform import Platform
from models.requests.platform_request import PlatformCreateRequest, PlatformUpdateRequest
from repositories.types_repositories.platform_repository import PlatformRepository

def get_platform_repo() -> PlatformRepository:
    return PlatformRepository()

platform_router = BaseCrudRouter(
    entity_name="platforms",
    model_cls=Platform,
    create_dto=PlatformCreateRequest,
    update_dto=PlatformUpdateRequest,
    get_repository=get_platform_repo
).router
