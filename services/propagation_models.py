from abc import abstractmethod, ABC
import math

class PropagationModels(ABC):
    @abstractmethod
    def calculate_path_loss(self, freq_mhz: float, distance_km: float,
                            tx_height_m: float, rx_height_m: float) -> float:
        """
            Calculates the Path Loss in dB based on the specific model physics.
        """
        pass