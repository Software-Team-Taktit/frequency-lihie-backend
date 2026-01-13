from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.types.hata_dto import HataDTO
from services.utils.helpers import all_fields

def hata_mapper(dto: GenericPropagationDTO) -> HataDTO:
    return HataDTO(**all_fields(dto))