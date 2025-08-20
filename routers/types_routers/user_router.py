from ..base_crud_router import BaseCrudRouter
from models.domain.types.users.user import User
from models.requests.user_request import UserCreateRequest, UserUpdateRequest, UserLogInRequest
from repositories.types_repositories.user_repository import UserRepository
from fastapi import Depends, HTTPException

def get_user_repo() -> UserRepository:
    return UserRepository()

user_router = BaseCrudRouter(
    entity_name="users",
    model_cls=User,
    create_dto=UserCreateRequest,
    update_dto=UserUpdateRequest,
    get_repository=get_user_repo
).router

@user_router.post("/login")
async def login(dto: UserLogInRequest, repo: UserRepository = Depends(get_user_repo)):
    user = await repo.get_by_personal_id(dto.personal_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user.model_dump()