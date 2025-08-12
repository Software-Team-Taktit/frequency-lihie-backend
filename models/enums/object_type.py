from enum import Enum as PyEnum

class ObjectType(str, PyEnum):
    USER = "user"
    ADMIN = "admin"
    MISSION = "mission"
    PLATFORM = "platform"