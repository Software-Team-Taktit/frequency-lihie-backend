from services.models.base_propagation_dto import BasePropagationDTO

class HataDTO(BasePropagationDTO):
    tx_height_m: float
    rx_height_m: float