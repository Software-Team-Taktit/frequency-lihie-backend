from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.types.egli_dto import EgliDTO
from services.utils.helpers import all_fields

def egli_mapper(dto: GenericPropagationDTO) -> EgliDTO:
    if dto.model_type != PropagationModelType.EGLI:
        raise ValueError(f"egli_mapper expected EGLI but got {dto.model_type}")

    data = all_fields(dto)

    return EgliDTO(**data)