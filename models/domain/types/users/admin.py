from models.enums.object_type import ObjectType
from models.domain.types.users.user import User

class Admin(User):
    def __init__(self, **data):
        data["type"] = ObjectType.ADMIN
        super().__init__(**data)