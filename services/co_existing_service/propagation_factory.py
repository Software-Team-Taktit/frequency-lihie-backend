import math
import pydantic 
from services.co_existing_service.utils.helpers import haversine_km
from services.base_propagation_model import BasePropagationModel
from services.domain_propagation_models.fspl_model import FSPLModel
from services.domain_propagation_models.hata_model import HataModel
from services.domain_propagation_models.egli_model import EgliModel
from models.helpers.coordinate import Coordinate
from models.enums.enviroment_type import EnviromentType

class PropagationFactory:
    def __init__(self):
        self._models: dict[EnviromentType, BasePropagationModel] = {
            EnviromentType.OPEN_SPACE: FSPLModel(),
            EnviromentType.URBAN: HataModel(),
            EnviromentType.MOUNT: EgliModel(),
        }
    
    def get_model(self, env_type: EnviromentType) -> BasePropagationModel:
        model = self._models.get(env_type)
        if not model:
            raise ValueError(f"No propagation model for env_type={env_type}")
        return model
    
    def distance_km(self, a: Coordinate, b: Coordinate) -> float:
        return haversine_km(a, b)
    
    def path_loss_db(
        self,
        env_type: EnviromentType,
        freq_mhz: float,
        distance_km: float,
        tx_height_m: float,
        rx_height_m: float,
    ) -> float:
        model = self.get_model(env_type)
        return model.calculate_path_loss(freq_mhz, distance_km, tx_height_m, rx_height_m)