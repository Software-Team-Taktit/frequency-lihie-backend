from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.types.egli_dto import EgliDTO
from services.utils.helpers import all_fields

def egli_mapper(dto: GenericPropagationDTO) -> EgliDTO:
    return EgliDTO(**all_fields(dto))