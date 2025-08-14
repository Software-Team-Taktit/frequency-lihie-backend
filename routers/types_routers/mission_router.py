from ..base_crud_router import BaseCrudRouter
from models.domain.types.mission import Mission
from models.requests.mission_request import MissionCreateRequest, MissionUpdateRequest
from repositories.types_repositories.mission_repository import MissionRepository

def get_mission_repo() -> MissionRepository:
    return MissionRepository()

mission_router = BaseCrudRouter(
    entity_name="missions",
    model_cls=Mission,
    create_dto=MissionCreateRequest,
    update_dto=MissionUpdateRequest,
    get_repository=get_mission_repo
).router