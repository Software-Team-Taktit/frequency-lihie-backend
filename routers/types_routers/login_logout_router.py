from ..base_crud_router import BaseCrudRouter
from models.domain.types.users.user import User
from models.requests.user_request import UserCreateRequest, UserUpdateRequest, UserLogInRequest
from repositories.types_repositories.user_repository import UserRepository
from fastapi import Depends, HTTPException, APIRouter, Response, Request
from starlette import status
from deps.auth import get_current_user, get_session_repo
from .user_router import user_crud_router
from repositories.types_repositories.session_repository import SessionRepository

def get_user_repo() -> UserRepository:
    return UserRepository()

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("/login")
async def login(dto: UserLogInRequest, response: Response, repo: UserRepository = Depends(get_user_repo), sesion_repo: SessionRepository = Depends(get_session_repo)):
    user = await repo.get_by_personal_id(dto.personal_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    
    session_id = await sesion_repo.create(user.id)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60*60*24*30,
        path='/'
    )
    return {"user": user.model_dump()}
    
@user_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request, 
    response: Response, 
    session_repo: SessionRepository = Depends(get_session_repo)
):
    session_id = request.cookies.get("session_id")
    if session_id:
        await session_repo.delete(session_id)
    response.delete_cookie(key="session_id", path="/", samesite="lax")
    return

@user_router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return current_user.model_dump()


user_router.include_router(user_crud_router)