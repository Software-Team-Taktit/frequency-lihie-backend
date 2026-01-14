from pydantic import BaseModel, Field, model_validator

class FrequencyRangeConfig(BaseModel):
    id: str = "frequency_range"
    min_mhz: float = Field(..., gt=0)
    max_mhz: float = Field(..., gt=0)
    
    @model_validator
    def _validate(self):
        if self.min_mhz >= self.max_mhz:
            raise ValueError("min_mhz must be smaller than max_mhz")
        return self