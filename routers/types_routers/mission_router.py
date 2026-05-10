from fastapi import Depends, HTTPException
from starlette import status

from ..base_crud_router import BaseCrudRouter
from deps.auth import get_current_user
from models.domain.types.mission import Mission
from models.requests.mission_request import MissionCreateRequest, MissionUpdateRequest
from repositories.types_repositories.mission_repository import MissionRepository


def get_mission_repo() -> MissionRepository:
    return MissionRepository()


def is_admin(current_user) -> bool:
    role = getattr(current_user, "role", None)
    user_type = getattr(current_user, "type", None)

    return (
        str(role).lower() == "admin"
        or str(user_type).lower().endswith("admin")
    )


def can_modify_mission(current_user, mission: Mission) -> bool:
    if is_admin(current_user):
        return True

    if not mission.owner_id:
        return False

    return str(mission.owner_id) == str(current_user.id)


mission_router = BaseCrudRouter(
    entity_name="missions",
    model_cls=Mission,
    create_dto=MissionCreateRequest,
    update_dto=MissionUpdateRequest,
    get_repository=get_mission_repo,
    include_create=False,
    include_update=False,
    include_delete=False,
).router


@mission_router.post("")
async def create_mission(
    payload: MissionCreateRequest,
    current_user=Depends(get_current_user),
    repo: MissionRepository = Depends(get_mission_repo),
):
    mission = Mission(
        **payload.model_dump(),
        owner_id=str(current_user.id),
    )

    saved = await repo.add_item(mission)

    if not saved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="couldnt create Mission",
        )

    return saved.model_dump()


@mission_router.put("/{item_id}")
async def update_mission(
    item_id: str,
    payload: MissionUpdateRequest,
    current_user=Depends(get_current_user),
    repo: MissionRepository = Depends(get_mission_repo),
):
    existing = await repo.get_by_id(item_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    if not can_modify_mission(current_user, existing):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to update this mission",
        )

    updated_data = existing.model_dump()
    updated_data.update(payload.model_dump(exclude_unset=True))
    updated_data["id"] = item_id
    updated_data["owner_id"] = existing.owner_id

    updated_mission = Mission(**updated_data)
    updated = await repo.update_item(item_id, updated_mission)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="failed to update Mission",
        )

    return updated.model_dump()


@mission_router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(
    item_id: str,
    current_user=Depends(get_current_user),
    repo: MissionRepository = Depends(get_mission_repo),
):
    existing = await repo.get_by_id(item_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    if not can_modify_mission(current_user, existing):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to delete this mission",
        )

    deleted = await repo.delete_item(item_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )


@mission_router.patch("/{item_id}/complete")
async def complete_mission(
    item_id: str,
    current_user=Depends(get_current_user),
    repo: MissionRepository = Depends(get_mission_repo),
):
    existing = await repo.get_by_id(item_id)

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mission not found",
        )

    if not can_modify_mission(current_user, existing):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to complete this mission",
        )

    updated_data = existing.model_dump()
    updated_data["is_active"] = False

    updated_mission = Mission(**updated_data)
    updated = await repo.update_item(item_id, updated_mission)

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="failed to complete Mission",
        )

    return updated.model_dump()