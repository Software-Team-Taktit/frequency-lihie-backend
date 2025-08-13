from uuid import uuid4, UUID
from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    personal_id: UUID
    first_name: str
    last_name: str
    unit: str