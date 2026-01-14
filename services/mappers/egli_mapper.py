from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.egli_dto import EgliDTO
from services.utils.helpers import all_fields

def egli_mapper(dto: GenericPropagationDTO) -> EgliDTO:
    if dto.model_type != PropagationModelType.EGLI:
        raise ValueError(f"egli_mapper expected EGLI but got {dto.model_type}")

    data = all_fields(dto)

    if data["freq_mhz"] <= 0:
        raise ValueError(f"EGLI requires freq_mhz > 0, got {data['freq_mhz']}")
    if data["distance_km"] <= 0:
        raise ValueError(f"EGLI requires distance_km > 0, got {data['distance_km']}")
    if data["tx_height_m"] <= 0:
        raise ValueError(f"EGLI requires tx_height_m > 0, got {data['tx_height_m']}")
    if data["rx_height_m"] <= 0:
        raise ValueError(f"EGLI requires rx_height_m > 0, got {data['rx_height_m']}")

    return EgliDTO(**data)