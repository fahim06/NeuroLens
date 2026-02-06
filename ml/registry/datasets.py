"""
Dataset Registry — Dataset Metadata

Registry for dataset configurations and metadata.
Phase 0: Metadata structures only.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DatasetConfig:
    """Configuration for a dataset."""

    name: str
    description: str
    source_url: Optional[str]
    size: Optional[int]  # Number of samples
    classes: List[str]
    image_size: tuple
    format: str  # 'folder', 'zip', 'h5', etc.


# Dataset configurations
DATASET_CONFIGS = {
    "brain_tumor": DatasetConfig(
        name="Brain Tumor Dataset",
        description="Medical MRI images for brain tumor detection",
        source_url="https://github.com/fahim06/Brain_Tumor",
        size=None,
        classes=["No Tumor", "Tumor"],
        image_size=(256, 256),
        format="folder",
    ),
    "citrus": DatasetConfig(
        name="Citrus Classification Dataset",
        description="Citrus fruit images for genus classification",
        source_url="https://github.com/fahim06/Citrus_Classification",
        size=None,
        classes=[
            "Limon Criollo",
            "Limon Mandarino",
            "Mandarina Pieldesapo",
            "Mandarina Israeli",
            "Naranja Valencia",
            "Tangelo",
            "Toronja",
            "Lima",
        ],
        image_size=(224, 224),
        format="folder",
    ),
}


class DatasetRegistry:
    """
    Registry for datasets used in training.

    Phase 0: Metadata only, no actual data loading.
    """

    def __init__(self):
        """Initialize the dataset registry."""
        self._configs = DATASET_CONFIGS
        logger.info(f"DatasetRegistry initialized with {len(self._configs)} datasets")

    def get_config(self, dataset_name: str) -> DatasetConfig:
        """Get configuration for a dataset."""
        if dataset_name not in self._configs:
            raise ValueError(f"Unknown dataset: {dataset_name}")
        return self._configs[dataset_name]

    def get_available_datasets(self) -> List[Dict[str, str]]:
        """Get list of available datasets."""
        return [
            {
                "name": name,
                "description": config.description,
                "classes": len(config.classes),
            }
            for name, config in self._configs.items()
        ]


# Global registry instance
dataset_registry = DatasetRegistry()
