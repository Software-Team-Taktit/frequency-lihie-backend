from enum import Enum

class EnviromentType(str, Enum):
    VERY_DENSE_URBAN = "very_dense_urban"
    DENSE_URBAN = "dense_urban"
    URBAN = "urban"
    SUBURBAN = "suburban"
    RURAL_VILLAGE = "rural_village"