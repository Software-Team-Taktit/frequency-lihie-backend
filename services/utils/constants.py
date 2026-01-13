from services.models.enums.pathloss_models_enum import PropagationModelType

MODEL_ALLOWED_FIELDS = {
    PropagationModelType.FSPL: {"freq_mhz", "distance_km"},
    PropagationModelType.HATA: {"freq_mhz", "distance_km", "tx_height_m", "rx_height_m"},
    PropagationModelType.EGLI: {"freq_mhz", "distance_km", "tx_height_m", "rx_height_m"},
}

MODEL_REQUIRED_FIELDS = {
    PropagationModelType.FSPL: {"freq_mhz", "distance_km"},
    PropagationModelType.HATA: {"freq_mhz", "distance_km", "tx_height_m", "rx_height_m"},
    PropagationModelType.EGLI: {"freq_mhz", "distance_km", "tx_height_m", "rx_height_m"},
}