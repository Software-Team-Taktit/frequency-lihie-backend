from pydantic import BaseModel

class UserCreateRequest(BaseModel):
    personal_id: str
    first_name: str
    last_name: str
    unit: str
    
class UserUpdateRequest(BaseModel):
    personal_id: str
    first_name: str
    last_name: str
    unit: str