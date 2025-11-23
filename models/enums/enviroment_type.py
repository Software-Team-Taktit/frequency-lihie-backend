from enum import Enum

class EnviromentType(str, Enum):
    MOUNT = "mount"
    URBAN = "urban"
    OPEN_SPACE = "open_space"