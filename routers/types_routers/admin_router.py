from fastapi import Depends, HTTPException
from starlette import status

from ..base_crud_router import BaseCrudRouter
from deps.auth import require_admin
from models.domain.types.users.admin import Admin
from models.requests.admin_request import AdminCreateRequest, AdminUpdateRequest
from repositories.types_repositories.admin_repository import AdminRepository
from repositories.types_repositories.mission_repository import MissionRepository


def get_admin_repo() -> AdminRepository:
    return AdminRepository()


def get_mission_repo() -> MissionRepository:
    return MissionRepository()


admin_router = BaseCrudRouter(
    entity_name="admins",
    model_cls=Admin,
    create_dto=AdminCreateRequest,
    update_dto=AdminUpdateRequest,
    get_repository=get_admin_repo,
    include_delete=False,
).router


@admin_router.delete("/profile/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_admin_profile(
    current_admin=Depends(require_admin),
    admin_repo: AdminRepository = Depends(get_admin_repo),
    mission_repo: MissionRepository = Depends(get_mission_repo),
):
    has_missions = await mission_repo.exists_by_owner_id(str(current_admin.id))

    if has_missions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete profile because this admin has missions.",
        )

    deleted = await admin_repo.delete_item(str(current_admin.id))

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin profile not found.",
        )