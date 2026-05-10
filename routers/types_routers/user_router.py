from fastapi import Depends, HTTPException
from starlette import status

from ..base_crud_router import BaseCrudRouter
from deps.auth import get_current_user
from models.domain.types.users.user import User
from models.requests.user_request import UserCreateRequest, UserUpdateRequest
from repositories.types_repositories.user_repository import UserRepository
from repositories.types_repositories.mission_repository import MissionRepository


def get_user_repo() -> UserRepository:
    return UserRepository()


def get_mission_repo() -> MissionRepository:
    return MissionRepository()


def is_admin(current_user) -> bool:
    user_type = getattr(current_user, "type", None)
    return str(user_type).lower().endswith("admin")


user_crud_router = BaseCrudRouter(
    entity_name="users",
    model_cls=User,
    create_dto=UserCreateRequest,
    update_dto=UserUpdateRequest,
    get_repository=get_user_repo,
    include_delete=False,
).router


@user_crud_router.delete("/profile/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_profile(
    current_user=Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    mission_repo: MissionRepository = Depends(get_mission_repo),
):
    if is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admins must use the admin profile delete endpoint.",
        )

    has_missions = await mission_repo.exists_by_owner_id(str(current_user.id))

    if has_missions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete profile because this user has missions.",
        )

    deleted = await user_repo.delete_item(str(current_user.id))

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.",
        )