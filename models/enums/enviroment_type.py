from enum import Enum

class EnviromentType(str, Enum):
    INDOOR = "indoor"
    URBAN = "urban"
    OPEN_SPACE = "open_space"