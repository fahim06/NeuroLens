"""
Domain Contracts — Domain Enums & Rules

Defines the primary domains and sub-categories for ML detection.
Phase 0: Enums and basic structure only.
"""

from enum import Enum
from typing import List, Dict


class PrimaryDomain(Enum):
    """Primary content domains for auto-detection."""

    HUMAN = "human"
    ANIMAL = "animal"
    PLANT = "plant"
    MEDICAL = "medical"
    UNKNOWN = "unknown"


class SubCategory(Enum):
    """Sub-categories within primary domains."""

    # Human domain
    HUMAN_FACE = "human_face"
    HUMAN_BODY = "human_body"

    # Animal domain
    ANIMAL_MAMMAL = "mammal"
    ANIMAL_BIRD = "bird"
    ANIMAL_REPTILE = "reptile"
    ANIMAL_FISH = "fish"
    ANIMAL_INSECT = "insect"

    # Plant domain
    PLANT_CITRUS = "citrus"
    PLANT_LEAF = "leaf"
    PLANT_FLOWER = "flower"
    PLANT_FRUIT = "fruit"

    # Medical domain
    MEDICAL_BRAIN = "brain"
    MEDICAL_XRAY = "xray"
    MEDICAL_MRI = "mri"


# Domain mapping for detection routing
DOMAIN_MAPPING: Dict[str, List[SubCategory]] = {
    PrimaryDomain.HUMAN.value: [
        SubCategory.HUMAN_FACE,
        SubCategory.HUMAN_BODY,
    ],
    PrimaryDomain.ANIMAL.value: [
        SubCategory.ANIMAL_MAMMAL,
        SubCategory.ANIMAL_BIRD,
        SubCategory.ANIMAL_REPTILE,
        SubCategory.ANIMAL_FISH,
        SubCategory.ANIMAL_INSECT,
    ],
    PrimaryDomain.PLANT.value: [
        SubCategory.PLANT_CITRUS,
        SubCategory.PLANT_LEAF,
        SubCategory.PLANT_FLOWER,
        SubCategory.PLANT_FRUIT,
    ],
    PrimaryDomain.MEDICAL.value: [
        SubCategory.MEDICAL_BRAIN,
        SubCategory.MEDICAL_XRAY,
        SubCategory.MEDICAL_MRI,
    ],
}


def get_subcategories_for_domain(domain: PrimaryDomain) -> List[SubCategory]:
    """
    Get all subcategories for a given primary domain.

    Args:
        domain: Primary domain enum

    Returns:
        List of subcategories for the domain
    """
    return DOMAIN_MAPPING.get(domain.value, [])
