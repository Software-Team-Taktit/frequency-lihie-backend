from fastapi import Depends, HTTPException, APIRouter, Response, Request
from starlette import status
from models.domain.types.users.user import User
from models.requests.user_request import UserLogInRequest
from repositories.types_repositories.user_repository import UserRepository
from models.domain.types.users.admin import Admin
from models.requests.admin_request import AdminLogInRequest
from repositories.types_repositories.admin_repository import AdminRepository
from deps.auth import get_current_user  
from deps.jwt_utils import create_access_token, create_refresh_token, decode_token
from typing import Union
from jose import JWTError
import os

def get_user_repo() -> UserRepository:
    return UserRepository()

def get_admin_repo() -> AdminRepository:
    return AdminRepository()

auth_router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE_NAME = os.getenv("REFRESH_COOKIE_NAME", "refresh_token")
REFRESH_COOKIE_PATH = os.getenv("REFRESH_COOKIE_PATH", "/")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
REFRESH_MAX_AGE = 60 * 60 * 24 * int(os.getenv("REFRESH_TTL_DAYS", "7"))

#---LOGIN---
@auth_router.post("/login")
async def login(
    dto: Union[UserLogInRequest, AdminLogInRequest], 
    response: Response, 
    user_repo: UserRepository = Depends(get_user_repo),
    admin_repo: AdminRepository = Depends(get_admin_repo),
):
    personal_id = dto.personal_id
    
    user = await user_repo.get_by_personal_id(personal_id)
    if user:
        role = "user"
        principal = user
    else:
        admin = await admin_repo.get_by_personal_id(personal_id)
        if not admin:
            raise HTTPException(status_code=404, detail="user/admin not found")
        role = "admin"
        principal = admin
    
    access_token = create_access_token(
        sub=principal.id,
        extra={"role": role},
    )
    
    refresh_token = create_refresh_token(
        sub=principal.id,
        extra={"role": role},
    )
    
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,       
        samesite=COOKIE_SAMESITE,   
        max_age=REFRESH_MAX_AGE,
        path=REFRESH_COOKIE_PATH,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role,
        "user": principal.model_dump(),
    }
    
#---REFRESH---
@auth_router.post("/refresh")
async def refresh_token(req: Request, res: Response):
    token = req.cookies.get(REFRESH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Wrong token type")

    sub = payload.get("sub")
    role = payload.get("role")

    if not sub or not role:
        raise HTTPException(status_code=401, detail="Invalid refresh token payload")

    new_access = create_access_token(
        sub=sub,
        extra={"role": role},
    )

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "role": role,
    }
    
#---LOGOUT---
@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        samesite=COOKIE_SAMESITE
    )
    return

#---WHOAMI---
@auth_router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return current_user.model_dump()