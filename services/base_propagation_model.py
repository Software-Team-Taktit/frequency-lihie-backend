from abc import abstractmethod, ABC
from services.models.base_propagation_dto import BasePropagationDTO

class BasePropagationModel(ABC):
    @abstractmethod
    def calculate_path_loss(self, dto: BasePropagationDTO) -> float:
        """
            Calculates the Path Loss in dB based on the specific model physics.
        """
        pass