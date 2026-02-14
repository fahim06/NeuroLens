"""
Biological Taxonomy Registry

Contains biological classification information for known species/classes.
Phase 8: Biological Classification Expansion.
"""

from typing import Dict, Optional


# Biological taxonomy for known animal classes
# Based on standard biological classification hierarchy
BIO_TAXONOMY: Dict[str, Dict[str, str]] = {
    "dog": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Carnivora",
        "family": "Canidae",
        "genus": "Canis",
        "species": "Canis lupus familiaris",
        "common_name": "Domestic Dog",
    },
    "cat": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Carnivora",
        "family": "Felidae",
        "genus": "Felis",
        "species": "Felis catus",
        "common_name": "Domestic Cat",
    },
    "horse": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Perissodactyla",
        "family": "Equidae",
        "genus": "Equus",
        "species": "Equus caballus",
        "common_name": "Horse",
    },
    "cow": {
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Artiodactyla",
        "family": "Bovidae",
        "genus": "Bos",
        "species": "Bos taurus",
        "common_name": "Domestic Cow",
    },
}


def get_taxonomy_for_label(label: str) -> Optional[Dict[str, str]]:
    """
    Get biological taxonomy information for a given label.

    Args:
        label: The predicted class label (e.g., "dog", "cat")

    Returns:
        Dictionary containing taxonomy information, or None if not found
    """
    return BIO_TAXONOMY.get(label.lower())
