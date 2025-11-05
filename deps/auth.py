# auth.py
from fastapi import Depends, HTTPException, Header
from starlette import status
from jose import JWTError
from repositories.types_repositories.user_repository import UserRepository
from deps.jwt_utils import decode_token 

def get_user_repo() -> UserRepository:
    return UserRepository()

async def get_current_user(
    authorization: str | None = Header(default=None), 
    user_repo: UserRepository = Depends(get_user_repo),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
