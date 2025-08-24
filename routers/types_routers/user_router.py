from ..base_crud_router import BaseCrudRouter
from models.domain.types.users.user import User
from models.requests.user_request import UserCreateRequest, UserUpdateRequest, UserLogInRequest
from repositories.types_repositories.user_repository import UserRepository
from fastapi import Depends, HTTPException, APIRouter,Response, Request
from starlette import status
from deps.auth import get_current_user, get_session_repo
from repositories.types_repositories.session_repository import SessionRepository

def get_user_repo() -> UserRepository:
    return UserRepository()

user_crud_router = BaseCrudRouter(
    entity_name="users",
    model_cls=User,
    create_dto=UserCreateRequest,
    update_dto=UserUpdateRequest,
    get_repository=get_user_repo
).router

