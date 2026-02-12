from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.fspl_dto import FsplDTO
from services.utils.helpers import all_fields

def fspl_mapper(dto: GenericPropagationDTO) -> FsplDTO:
    if dto.model_type != PropagationModelType.FSPL:
        raise ValueError(f"fspl mapper expected FSPL but got {dto.model_type}")
    
    data = all_fields(dto)
    
    return FsplDTO(**data)