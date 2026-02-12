from services.models.base_propagation_dto import BasePropagationDTO
from pydantic import PositiveFloat

class EgliDTO(BasePropagationDTO):
    tx_height_m: PositiveFloat
    rx_height_m: PositiveFloat