from enum import Enum

class PropagationModelType(str, Enum):
    FSPL = "FSPL"
    HATA = "HATA"
    EGLI = "EGLI"