"""
Dataset Registry Adapter — Bridge between ML registry and Dataset app

Adapts the Django Dataset model to work with ML registry interfaces.
"""

import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


def get_dataset_by_domain(domain: str) -> Optional[object]:
    """
    Get active dataset for a given domain.

    Args:
        domain: Domain name (e.g., 'animal', 'plant', 'medical')

    Returns:
        Dataset instance or None if not found
    """
    try:
        # Lazy import to avoid Django setup issues
        from datasets.models import Dataset

        return Dataset.objects.filter(domain=domain, active=True).first()
    except Exception as e:
        logger.error(f"Error getting dataset for domain {domain}: {e}")
        return None


def get_classes_for_domain(domain: str) -> List[str]:
    """
    Get class list for a given domain.

    Args:
        domain: Domain name

    Returns:
        List of class names, or empty list if not found
    """
    dataset = get_dataset_by_domain(domain)
    if dataset and dataset.classes:
        return dataset.classes
    return []


def get_active_datasets() -> List[object]:
    """
    Get all active datasets.

    Returns:
        List of active Dataset instances
    """
    try:
        # Lazy import to avoid Django setup issues
        from datasets.models import Dataset

        return list(Dataset.objects.filter(active=True))
    except Exception as e:
        logger.error(f"Error getting active datasets: {e}")
        return []
