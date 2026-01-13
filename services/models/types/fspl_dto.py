from services.models.base_propagation_dto import BasePropagationDTO
from enums.pathloss_models_enum import PropagationModelType


class FsplDTO(BasePropagationDTO):
    model_type: PropagationModelType = PropagationModelType.FSPL