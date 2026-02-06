# ml/services/domain_detector.py
"""
Auto-Domain Detection Service.
Phase 0: Interface only, no actual detection logic.

This service analyzes an uploaded image and determines:
1. Primary domain (human, animal, plant, medical)
2. Sub-category within that domain
3. Which model should be used
"""

import logging
from typing import Optional, Dict, Any

from ml.contracts.domain import PrimaryDomain, SubCategory, get_subcategories_for_domain

logger = logging.getLogger(__name__)


class DomainDetectionResult:
    """Result of domain detection."""

    def __init__(
        self,
        primary_domain: PrimaryDomain,
        sub_category: SubCategory,
        confidence: float,
        recommended_model: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.primary_domain = primary_domain
        self.sub_category = sub_category
        self.confidence = confidence
        self.recommended_model = recommended_model
        self.metadata = metadata or {}


class DomainDetectorService:
    """
    Auto-domain detection service.
    Analyzes image content to determine domain and select appropriate model.

    Phase 0: Interface only, returns placeholder results.
    """

    def __init__(self):
        """Initialize the domain detector service."""
        logger.info("DomainDetectorService initialized (Phase 0)")

    def detect_domain(self, image_data: bytes) -> DomainDetectionResult:
        """
        Detect the primary domain of an image.

        Args:
            image_data: Raw image bytes

        Returns:
            DomainDetectionResult with detection information
        """
        # Phase 0: Return placeholder result
        return DomainDetectionResult(
            primary_domain=PrimaryDomain.UNKNOWN,
            sub_category=SubCategory.UNKNOWN,
            confidence=0.0,
            recommended_model="unknown",
            metadata={
                "message": "Domain detection not implemented in Phase 0",
                "phase": "0",
            },
        )

    def is_available(self) -> bool:
        """
        Check if the domain detector is available.

        Returns:
            False in Phase 0
        """
        return False


# Global service instance
domain_detector_service = DomainDetectorService()
