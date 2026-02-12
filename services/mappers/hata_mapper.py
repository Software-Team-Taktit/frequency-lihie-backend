from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.hata_dto import HataDTO
from services.utils.helpers import all_fields

def hata_mapper(dto: GenericPropagationDTO) -> HataDTO:
    if dto.model_type != PropagationModelType.HATA:
        raise ValueError(f"hata_mapper expected HATA but got {dto.model_type}")
    
    data = all_fields(dto)
    
    return HataDTO(**data)