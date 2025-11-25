from uuid import uuid4
from models.domain.base_object import BaseObject
from models.enums.object_type import ObjectType

class Platform(BaseObject):
    name: str
    bw_khz: float
    tx_gain: float
    tx_height_m: float = 20.0
    rx_gain: float
    rx_height_m: float = 1.5
    min_sinr_required_db: float = 12.0
    noise_figure_db: float = 3.0
    
    def __init__(self, **data):
        data["id"] = data.get("id", str(uuid4()))
        data["type"] = ObjectType.PLATFORM
        super().__init__(**data)