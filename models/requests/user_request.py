from pydantic import BaseModel, Field, field_validator

class UserCreateRequest(BaseModel):
    personal_id: str
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    unit: str
    
    @field_validator("personal_id")
    @classmethod
    def validate_personal_id(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 7:
            raise ValueError("Personal ID must be exactly 7 digits")
        return v

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Unit must not be empty")
        return v
    
class UserUpdateRequest(UserCreateRequest):
    """
    Partial update of an existing user.
    All fields are optional.
    """
    personal_id: str | None
    first_name: str | None = Field(None, min_length=2)
    last_name: str | None = Field(None, min_length=2)
    unit: str | None = None
    
    @field_validator("personal_id")
    @classmethod
    def validate_personal_id(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 7:
            raise ValueError("Personal ID must be exactly 7 digits")
        return v

class UserLogInRequest(BaseModel):
    personal_id: str = Field(
        ...,
        min_length=7,
        max_length=7,
        pattern=r'^\d{7}$',
        description="מספר אישי חייב להיות 7 ספרות בדיוק"
    )