# auth.py
from fastapi import Depends, HTTPException, Header
from starlette import status
from jose import JWTError
from repositories.types_repositories.user_repository import UserRepository
from repositories.types_repositories.admin_repository import AdminRepository
from deps.jwt_utils import decode_token 

def get_user_repo() -> UserRepository:
    return UserRepository()

def get_admin_repo() -> AdminRepository:
    return AdminRepository()

async def get_current_user(
    authorization: str | None = Header(default=None), 
    user_repo: UserRepository = Depends(get_user_repo),
    admin_repo: AdminRepository = Depends(get_admin_repo),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.split(" ", 1)[1]

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong token type",
        )

    sub = payload.get("sub")
    role = payload.get("role")

    if not sub or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    if role == "admin":
        admin = await admin_repo.get_by_id(sub)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin not found",
            )
        return admin

    user = await user_repo.get_by_id(sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
