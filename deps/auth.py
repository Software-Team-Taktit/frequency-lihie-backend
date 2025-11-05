from fastapi import Depends, HTTPException, Header
from starlette import status
from jose import JWTError
from db.mongo import get_db
from repositories.types_repositories.user_repository import UserRepository
from jwt_utils import decode_token



def get_user_repo() -> UserRepository:
    return UserRepository()

async def get_current_user(
    authrization: str | None = Header(defult=None),
    user_repo: UserRepository = Depends(get_user_repo)
):
    if not authrization or not authrization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    
    token = authrization.split(" ", 1)[1].strip()
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