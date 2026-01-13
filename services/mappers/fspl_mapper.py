from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.types.fspl_dto import FsplDTO
from services.utils.helpers import all_fields

def fspl_mapper(dto: GenericPropagationDTO) -> FsplDTO:
    return FsplDTO(**all_fields(dto))