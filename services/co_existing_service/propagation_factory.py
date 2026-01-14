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
        
    def get_model_type(self, env_type: EnviromentType) -> PropagationModelType:
        mt = self._env_to_model_type.get(env_type)
        if not mt:
            raise ValueError(f"No model type for env_type={env_type}")
        return mt
    
    def get_model(self, model_type: PropagationModelType) -> BasePropagationModel:
        model = self._model_by_type.get(model_type)
        if not model:
            raise ValueError(f"No propagation model for model_type={model_type}")
        return model
    
    def distance_km(self, a: Coordinate, b: Coordinate) -> float:
        return haversine_km(a, b)
    
    def path_loss_db(self, dto: GenericPropagationDTO) -> float:
        model_type = dto.model_type
        mapper = self._mappers.get(model_type)
        if not mapper:
            raise ValueError(f"No mapper for model_type = {model_type}")
        
        specific_dto = mapper(dto)
        
        model = self.get_model(model_type)
        return model.calculate_path_loss(specific_dto)