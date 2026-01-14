from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.fspl_dto import FsplDTO
from services.utils.helpers import all_fields

def fspl_mapper(dto: GenericPropagationDTO) -> FsplDTO:
    if dto.model_type != PropagationModelType.FSPL:
        raise ValueError(f"fspl mapper expected FSPL but got {dto.model_type}")
    
    data = all_fields(dto)
    
    if data["freq_mhz"] <= 0:
        raise ValueError(f"FSPL requires freq_mhz > 0, got {data['freq_mhz']}")
    if data["distance_km"] <= 0:
        raise ValueError(f"FSPL requires distance_km > 0, got {data['distance_km']}")
    
    return FsplDTO(**data)