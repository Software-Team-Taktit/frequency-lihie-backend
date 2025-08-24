from fastapi import Depends, HTTPException, Request
from starlette import status
from db.mongo import get_db
from repositories.types_repositories.session_repository import SessionRepository
from repositories.types_repositories.user_repository import UserRepository

def get_session_repo(db = Depends(get_db)):
    return SessionRepository(db)

def get_user_repo(db = Depends(get_db)):
    return UserRepository()

async def get_current_user(
    request: Request,
    session_repo: SessionRepository = Depends(get_session_repo),
    user_repo: UserRepository = Depends(get_user_repo)
):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    sess = await session_repo.get(session_id)
    if not sess: 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expires")
    
    user = await user_repo.get_by_id(sess["user_id"])
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user