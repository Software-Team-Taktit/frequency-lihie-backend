from services.models.base_propagation_dto import BasePropagationDTO
from enums.pathloss_models_enum import PropagationModelType

class HataDTO(BasePropagationDTO):
    model_type: PropagationModelType = PropagationModelType.HATA
    tx_height_m: float
    rx_height_m: float