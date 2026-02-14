"""
Postprocessor Service — Output Formatting & Enrichment

Handles post-processing of ML model outputs and biological classification enrichment.
Phase 8: Biological Classification Expansion.
"""

import logging
from typing import Any, Dict, List, Optional

from ml.registry.taxonomy import get_taxonomy_for_label

logger = logging.getLogger(__name__)


class PostprocessorService:
    """
    Service for post-processing ML model outputs.

    Responsibilities:
    - Format raw model outputs
    - Apply confidence thresholds
    - Convert predictions to human-readable format
    - Handle edge cases and fallbacks

    Phase 0: Interface only.
    """

    def __init__(self):
        """Initialize the postprocessor service."""
        logger.info("PostprocessorService initialized (Phase 0)")

    def process_binary_output(
        self, raw_output: Any, class_labels: List[str]
    ) -> Dict[str, Any]:
        """
        Process binary classification output.

        Args:
            raw_output: Raw model output
            class_labels: List of class labels

        Returns:
            Processed output dictionary
        """
        # Phase 0: Return placeholder
        return {
            "prediction": "placeholder",
            "confidence": 0.0,
            "class_labels": class_labels,
            "message": "Postprocessing not implemented in Phase 0",
        }

    def process_multiclass_output(
        self, raw_output: Any, class_labels: List[str]
    ) -> Dict[str, Any]:
        """
        Process multi-class classification output.

        Args:
            raw_output: Raw model output
            class_labels: List of class labels

        Returns:
            Processed output dictionary
        """
        # Phase 0: Return placeholder
        return {
            "prediction": "placeholder",
            "confidence": 0.0,
            "top_k": [],
            "class_labels": class_labels,
            "message": "Postprocessing not implemented in Phase 0",
        }

    def process_hierarchical_output(
        self, raw_output: Any, hierarchy_levels: List[str]
    ) -> Dict[str, Any]:
        """
        Process hierarchical classification output.

        Args:
            raw_output: Raw model output
            hierarchy_levels: List of hierarchy levels

        Returns:
            Processed output dictionary
        """
        # Phase 0: Return placeholder
        return {
            "prediction": {},
            "confidence": 0.0,
            "hierarchy": hierarchy_levels,
            "message": "Postprocessing not implemented in Phase 0",
        }

    def enrich_with_taxonomy(self, label: str) -> Optional[Dict[str, str]]:
        """
        Enrich a prediction label with biological taxonomy information.

        Args:
            label: The predicted class label (e.g., "dog", "cat")

        Returns:
            Dictionary containing taxonomy information, or None if not available
        """
        taxonomy = get_taxonomy_for_label(label)
        if taxonomy:
            logger.info(f"[TAXONOMY] Enriched {label} with biological classification")
        return taxonomy


# Global service instance
postprocessor_service = PostprocessorService()
