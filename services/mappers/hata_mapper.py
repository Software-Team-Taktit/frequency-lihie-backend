from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.hata_dto import HataDTO
from services.utils.helpers import all_fields

def hata_mapper(dto: GenericPropagationDTO) -> HataDTO:
    if dto.model_type != PropagationModelType.HATA:
        raise ValueError(f"hata_mapper expected HATA but got {dto.model_type}")
    
    data = all_fields(dto)
    
    if data["freq_mhz"] <= 0:
        raise ValueError(f"HATA requires freq_mhz > 0, got {data['freq_mhz']}")
    if data["distance_km"] <= 0:
        raise ValueError(f"HATA requires distance_km > 0, got {data['distance_km']}")
    if data["tx_height_m"] <= 0:
        raise ValueError(f"HATA requires tx_height_m > 0, got {data['tx_height_m']}")
    if data["rx_height_m"] <= 0:
        raise ValueError(f"HATA requires rx_height_m > 0, got {data['rx_height_m']}")
    
    return HataDTO(**data)