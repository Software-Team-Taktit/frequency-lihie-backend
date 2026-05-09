from ..base_crud_router import BaseCrudRouter
from models.domain.types.users.admin import Admin
from models.requests.admin_request import AdminCreateRequest, AdminUpdateRequest
from repositories.types_repositories.admin_repository import AdminRepository

def get_admin_repo() -> AdminRepository:
    return AdminRepository()

admin_router = BaseCrudRouter(
    entity_name="admins",
    model_cls=Admin,
    create_dto=AdminCreateRequest,
    update_dto=AdminUpdateRequest,
    get_repository=get_admin_repo
).router
