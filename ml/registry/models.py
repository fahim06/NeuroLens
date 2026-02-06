"""
Model Registry — ML Model Metadata

Registry for model configurations and metadata.
Phase 0: Metadata structures, no actual model loading.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DetectionType(str, Enum):
    """Supported detection types."""

    HUMAN_ANIMAL = "human_animal"
    ANIMAL_CATEGORY = "animal_category"
    BIOLOGICAL = "biological"
    BRAIN_TUMOR = "brain_tumor"
    CITRUS = "citrus"


@dataclass
class DetectionConfig:
    """Configuration for a detection type."""

    name: str
    description: str
    model_path: Optional[str]
    input_size: tuple
    num_classes: int
    class_labels: List[str]
    preprocessing: str  # 'vgg16', 'mobilenet', 'standard'
    output_format: str  # 'binary', 'multiclass', 'hierarchy'


# Detection configurations based on referenced repositories
DETECTION_CONFIGS: Dict[DetectionType, DetectionConfig] = {
    DetectionType.HUMAN_ANIMAL: DetectionConfig(
        name="Human vs Animal Detection",
        description="Binary classification to detect whether subject is human or animal",
        model_path=None,  # To be trained/loaded
        input_size=(256, 256),
        num_classes=2,
        class_labels=["Human", "Animal"],
        preprocessing="standard",
        output_format="binary",
    ),
    DetectionType.ANIMAL_CATEGORY: DetectionConfig(
        name="Animal Category Detection",
        description="Classify animal into category/species",
        model_path=None,
        input_size=(256, 256),
        num_classes=10,  # Placeholder
        class_labels=[
            "Dog",
            "Cat",
            "Bird",
            "Fish",
            "Reptile",
            "Mammal",
            "Insect",
            "Amphibian",
            "Primate",
            "Other",
        ],
        preprocessing="standard",
        output_format="multiclass",
    ),
    DetectionType.BIOLOGICAL: DetectionConfig(
        name="Biological Classification",
        description="Full taxonomic hierarchy: Kingdom → Species",
        model_path=None,
        input_size=(256, 256),
        num_classes=7,  # Hierarchy levels
        class_labels=[
            "Kingdom",
            "Phylum",
            "Class",
            "Order",
            "Family",
            "Genus",
            "Species",
        ],
        preprocessing="standard",
        output_format="hierarchy",
    ),
    # Brain Tumor Detection - Based on fahim06/Brain_Tumor (VGG16 model)
    DetectionType.BRAIN_TUMOR: DetectionConfig(
        name="Brain Tumor Detection",
        description="Medical image classification for brain tumor presence",
        model_path="assets/brain_tumor_vgg16.keras",
        input_size=(256, 256),  # From VGG16.ipynb: target_size=(256,256,3)
        num_classes=2,
        class_labels=["No Tumor", "Tumor"],
        preprocessing="vgg16",  # VGG16 preprocessing
        output_format="binary",
    ),
    # Citrus Classification - Based on fahim06/Citrus_Classification (MobileNet model)
    DetectionType.CITRUS: DetectionConfig(
        name="Citrus Classification",
        description="Plant genus classification for citrus fruits",
        model_path="assets/citrus_mobilenet.keras",
        input_size=(224, 224),  # MobileNet standard size
        num_classes=8,
        class_labels=[
            "Limon Criollo",
            "Limon Mandarino",
            "Mandarina Pieldesapo",
            "Mandarina Israeli",
            "Naranja Valencia",
            "Tangelo",
            "Toronja",
            "Lima",
        ],
        preprocessing="mobilenet",
        output_format="multiclass",
    ),
}


class ModelRegistry:
    """
    Registry for multi-domain detection models.

    Responsibilities:
    - Map detection type → model configuration
    - Lazy load models on demand (Phase 0: metadata only)
    - Enforce model isolation
    """

    def __init__(self):
        """Initialize the model registry."""
        self._loaded_models: Dict[DetectionType, Any] = {}
        self._configs = DETECTION_CONFIGS
        logger.info(
            f"ModelRegistry initialized with {len(self._configs)} detection types"
        )

    def get_config(self, detection_type: DetectionType) -> DetectionConfig:
        """Get configuration for a detection type."""
        if detection_type not in self._configs:
            raise ValueError(f"Unknown detection type: {detection_type}")
        return self._configs[detection_type]

    def get_available_types(self) -> List[Dict[str, str]]:
        """Get list of available detection types for UI dropdown."""
        return [
            {"value": dt.value, "name": config.name, "description": config.description}
            for dt, config in self._configs.items()
        ]

    def load_model(self, detection_type: DetectionType) -> Optional[Any]:
        """
        Lazy load a model for the specified detection type.

        Phase 0: Always returns None (no actual loading).
        """
        logger.info(f"Phase 0: Would load model for {detection_type.value}")
        return None

    def is_model_available(self, detection_type: DetectionType) -> bool:
        """Check if a model is available for the detection type."""
        config = self.get_config(detection_type)
        return config.model_path is not None


# Global registry instance
model_registry = ModelRegistry()
