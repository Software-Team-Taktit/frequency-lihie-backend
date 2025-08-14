from ..base_crud_router import BaseCrudRouter
from models.domain.types.users.user import User
from models.requests.user_request import UserCreateRequest, UserUpdateRequest
from repositories.types_repositories.user_repository import UserRepository

def get_user_repo() -> UserRepository:
    return UserRepository()

user_router = BaseCrudRouter(
    entity_name="users",
    model_cls=User,
    create_dto=UserCreateRequest,
    update_dto=UserUpdateRequest,
    get_repository=get_user_repo
).router