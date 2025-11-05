from fastapi import Depends, HTTPException, APIRouter, Response, Request
from starlette import status
from models.domain.types.users.user import User
from models.requests.user_request import UserLogInRequest
from repositories.types_repositories.user_repository import UserRepository
from deps.auth import get_current_user  
from deps.jwt_utils import create_access_token, create_refresh_token, decode_token
from jose import JWTError
import os

def get_user_repo() -> UserRepository:
    return UserRepository()

user_router = APIRouter(prefix="/users", tags=["users"])

REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/users")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"  
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")                  
REFRESH_MAX_AGE = 60 * 60 * 24 * int(os.getenv("REFRESH_TTL_DAYS", "7"))


@user_router.post("/login")
async def login(dto: UserLogInRequest, response: Response, repo: UserRepository = Depends(get_user_repo)):
    user = await repo.get_by_personal_id(dto.personal_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    
    access = create_access_token(sub=user.id, extra={"unit": getattr(user, "unit", "user")})
    refresh = create_refresh_token(sub=user.id)
    
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh,
        httponly=True,
        secure=COOKIE_SECURE,       
        samesite=COOKIE_SAMESITE,   
        max_age=REFRESH_MAX_AGE,
        path=REFRESH_COOKIE_PATH,
    )
    
    return {
        "access_token": access,
        "token_type": "bearer",
        "user": user.model_dump(),
    }
    
@user_router.post("/refresh")
async def refresh_token(req: Request, res: Response):
    rt = req.cookies.get(REFRESH_COOKIE_NAME)
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = decode_token(rt)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")
    new_access = create_access_token(sub=user_id)

    return {"access_token": new_access, "token_type": "bearer"}
    
@user_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        samesite=COOKIE_SAMESITE
    )
    return

@user_router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return current_user.model_dump()

