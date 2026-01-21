"""
Model selection and pricing configuration.
Centralized definition of cheap/medium/expensive models.
"""
from enum import Enum
from dataclasses import dataclass
from app.config import settings


class ModelTier(str, Enum):
    """Model tier enumeration for selection."""
    CHEAP = "cheap"
    MEDIUM = "medium"
    EXPENSIVE = "expensive"


@dataclass
class ModelConfig:
    """Model configuration with pricing."""
    name: str
    input_price_per_1k: float
    output_price_per_1k: float
    tier: ModelTier


class ModelSelector:
    """
    Centralized model selection and configuration.
    
    Provides a single source of truth for model names and pricing.
    Makes it easy to swap models or adjust pricing.
    """
    
    def __init__(self):
        self.models = {
            ModelTier.CHEAP: ModelConfig(
                name=settings.model_cheap,
                input_price_per_1k=settings.price_cheap_input,
                output_price_per_1k=settings.price_cheap_output,
                tier=ModelTier.CHEAP
            ),
            ModelTier.MEDIUM: ModelConfig(
                name=settings.model_medium,
                input_price_per_1k=settings.price_medium_input,
                output_price_per_1k=settings.price_medium_output,
                tier=ModelTier.MEDIUM
            ),
            ModelTier.EXPENSIVE: ModelConfig(
                name=settings.model_expensive,
                input_price_per_1k=settings.price_expensive_input,
                output_price_per_1k=settings.price_expensive_output,
                tier=ModelTier.EXPENSIVE
            ),
        }
    
    def get_model(self, tier: ModelTier) -> ModelConfig:
        """Get model configuration for a given tier."""
        return self.models[tier]
    
    def get_model_name(self, tier: ModelTier) -> str:
        """Get model name for a given tier."""
        return self.models[tier].name
    
    def get_pricing(self, model_name: str) -> tuple[float, float]:
        """
        Get pricing for a model by name.
        
        Returns:
            Tuple of (input_price_per_1k, output_price_per_1k)
        """
        for model in self.models.values():
            if model.name == model_name:
                return model.input_price_per_1k, model.output_price_per_1k
        # Default fallback pricing
        return 0.001, 0.002
