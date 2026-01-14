from typing import Callable, Dict

from services.utils.helpers import haversine_km
from services.base_propagation_model import BasePropagationModel
from services.domain_propagation_models.fspl_model import FSPLModel
from services.domain_propagation_models.hata_model import HataModel
from services.domain_propagation_models.egli_model import EgliModel

from models.helpers.coordinate import Coordinate
from models.enums.enviroment_type import EnviromentType

from services.models.enums.pathloss_models_enum import PropagationModelType
from services.models.generic_propagation_dto import GenericPropagationDTO
from services.models.base_propagation_dto import BasePropagationDTO

from services.mappers.fspl_mapper import fspl_mapper
from services.mappers.hata_mapper import hata_mapper
from services.mappers.egli_mapper import egli_mapper

class PropagationFactory:
    def __init__(self):
        #Enviroment -> ModelType
        self._env_to_model_type: Dict[EnviromentType, PropagationModelType] = {
            EnviromentType.OPEN_SPACE: PropagationModelType.FSPL,
            EnviromentType.URBAN: PropagationModelType.HATA,
            EnviromentType.MOUNT: PropagationModelType.EGLI,
        }
        
        #ModelType -> Model instance
        self._model_by_type: Dict[PropagationModelType, BasePropagationModel] = {
            PropagationModelType.FSPL: FSPLModel(),
            PropagationModelType.HATA: HataModel(),
            PropagationModelType.EGLI: EgliModel(),
        }
        
        #ModelType -> Mappers(GenericDTO -> SpecificDTO)
        self._mappers: Dict[
            PropagationModelType, Callable[[GenericPropagationDTO], BasePropagationDTO]
        ] = {
            PropagationModelType.FSPL: fspl_mapper,
            PropagationModelType.HATA: hata_mapper,
            PropagationModelType.EGLI: egli_mapper,
        }
        
    
    