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
    "rose": {
        "kingdom": "Plantae",
        "phylum": "Tracheophyta",
        "class": "Magnoliopsida",
        "order": "Rosales",
        "family": "Rosaceae",
        "genus": "Rosa",
        "species": "Rosa spp.",
        "common_name": "Rose",
    },
    "sunflower": {
        "kingdom": "Plantae",
        "phylum": "Tracheophyta",
        "class": "Magnoliopsida",
        "order": "Asterales",
        "family": "Asteraceae",
        "genus": "Helianthus",
        "species": "Helianthus annuus",
        "common_name": "Sunflower",
    },
    "tulip": {
        "kingdom": "Plantae",
        "phylum": "Tracheophyta",
        "class": "Magnoliopsida",
        "order": "Liliales",
        "family": "Liliaceae",
        "genus": "Tulipa",
        "species": "Tulipa spp.",
        "common_name": "Tulip",
    },
    "oak": {
        "kingdom": "Plantae",
        "phylum": "Tracheophyta",
        "class": "Magnoliopsida",
        "order": "Fagales",
        "family": "Fagaceae",
        "genus": "Quercus",
        "species": "Quercus spp.",
        "common_name": "Oak Tree",
    },
    "normal": {
        "domain": "medical",
        "category": "diagnostic",
        "condition": "normal",
        "description": "No abnormalities detected",
    },
    "pneumonia": {
        "domain": "medical",
        "category": "diagnostic",
        "condition": "pneumonia",
        "description": "Inflammation of the lungs",
    },
    "covid": {
        "domain": "medical",
        "category": "diagnostic",
        "condition": "covid-19",
        "description": "COVID-19 infection",
    },
    "tuberculosis": {
        "domain": "medical",
        "category": "diagnostic",
        "condition": "tuberculosis",
        "description": "Tuberculosis infection",
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
