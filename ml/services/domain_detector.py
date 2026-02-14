# ml/services/domain_detector.py
"""
Domain Detection Service.
Phase 1: Heuristic-based domain detection.

This service analyzes an uploaded image and determines the primary domain
using lightweight heuristics.
"""

import logging
from typing import Optional, Dict, Any
from io import BytesIO
import numpy as np

from ml.contracts.domain import PrimaryDomain, DomainDetectionResult
from ml.config import DOMAIN_CONFIDENCE_THRESHOLD

logger = logging.getLogger(__name__)


class DomainDetectorService:
    """
    Domain detection service using heuristics.
    Phase 1: Lightweight heuristics for domain classification.
    """

    def __init__(self):
        """Initialize the domain detector service."""
        logger.info("DomainDetectorService initialized (Phase 1)")

    def detect(self, image) -> DomainDetectionResult:
        """
        Detect the primary domain of an image using heuristics.

        Args:
            image: PIL Image or similar object

        Returns:
            DomainDetectionResult with detection information
        """
        # Lazy import PIL
        from PIL import Image

        # Convert to PIL if needed
        if not isinstance(image, Image.Image):
            image = Image.open(BytesIO(image))

        # Get image properties
        width, height = image.size
        aspect_ratio = width / height if height > 0 else 1.0

        # Convert to numpy array for analysis
        img_array = np.array(image)

        # Heuristics
        is_grayscale = self._is_grayscale(img_array)
        dominant_color = self._get_dominant_color(img_array)
        has_mri_features = self._has_mri_features(img_array)
        has_fur_texture = self._has_fur_texture(img_array)

        logger.info(
            f"Image analysis: size={width}x{height}, aspect={aspect_ratio:.2f}, "
            f"grayscale={is_grayscale}, dominant_color={dominant_color}, mri={has_mri_features}, fur={has_fur_texture}"
        )

        # Domain detection logic with confidence scoring
        domain_scores = self._calculate_domain_scores(
            is_grayscale,
            dominant_color,
            has_mri_features,
            has_fur_texture,
            aspect_ratio,
        )

        # Select domain with highest confidence
        best_domain = max(domain_scores, key=domain_scores.get)
        confidence = domain_scores[best_domain]

        # Fallback logic for low confidence
        if confidence < DOMAIN_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"Low confidence detection: {best_domain.value} ({confidence:.2f}) < {DOMAIN_CONFIDENCE_THRESHOLD}, falling back to human"
            )
            best_domain = PrimaryDomain.HUMAN
            confidence = 0.5  # Low confidence fallback
            meta = {
                "method": "fallback",
                "reason": f"Low confidence detection, original: {max(domain_scores, key=domain_scores.get).value}",
                "original_confidence": domain_scores[
                    max(domain_scores, key=domain_scores.get)
                ],
            }
        else:
            meta = {
                "method": "heuristic",
                "scores": domain_scores,
            }

        logger.info(
            f"Detected domain: {best_domain.value}, confidence: {confidence:.2f}"
        )

        return DomainDetectionResult(
            domain=best_domain, confidence=confidence, meta=meta
        )

    def _calculate_domain_scores(
        self,
        is_grayscale: bool,
        dominant_color: str,
        has_mri_features: bool,
        has_fur_texture: bool,
        aspect_ratio: float,
    ) -> Dict[PrimaryDomain, float]:
        """Calculate confidence scores for each domain."""
        scores = {
            PrimaryDomain.HUMAN: 0.0,
            PrimaryDomain.ANIMAL: 0.0,
            PrimaryDomain.PLANT: 0.0,
            PrimaryDomain.MEDICAL: 0.0,
        }

        # Medical domain: grayscale + MRI features
        if is_grayscale and has_mri_features:
            scores[PrimaryDomain.MEDICAL] += 0.8
        elif is_grayscale:
            scores[PrimaryDomain.MEDICAL] += 0.4

        # Plant domain: green dominant color
        if dominant_color == "green":
            scores[PrimaryDomain.PLANT] += 0.7
        elif dominant_color in ["mixed", "red"]:
            scores[PrimaryDomain.PLANT] += 0.3

        # Animal domain: fur texture + not green
        if has_fur_texture and dominant_color != "green":
            scores[PrimaryDomain.ANIMAL] += 0.6
        elif dominant_color not in ["green", "blue"]:
            scores[PrimaryDomain.ANIMAL] += 0.4

        # Human domain: default fallback
        max_score = max(scores.values())
        if max_score < 0.5:
            scores[PrimaryDomain.HUMAN] = 0.5  # Baseline human confidence

        # Normalize scores to sum to 1 (optional, but helps with confidence interpretation)
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}

        return scores

    def _is_grayscale(self, img_array: np.ndarray) -> bool:
        """Check if image is mostly grayscale."""
        if len(img_array.shape) == 2:
            return True
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            # Check if R, G, B channels are similar
            diff_rg = np.abs(img_array[:, :, 0] - img_array[:, :, 1])
            diff_rb = np.abs(img_array[:, :, 0] - img_array[:, :, 2])
            return np.mean(diff_rg) < 10 and np.mean(diff_rb) < 10
        return False

    def _get_dominant_color(self, img_array: np.ndarray) -> str:
        """Get dominant color (simplified)."""
        if len(img_array.shape) < 3:
            return "gray"
        # Simple histogram
        r_mean = np.mean(img_array[:, :, 0])
        g_mean = np.mean(img_array[:, :, 1])
        b_mean = np.mean(img_array[:, :, 2])
        if g_mean > r_mean and g_mean > b_mean:
            return "green"
        elif r_mean > g_mean and r_mean > b_mean:
            return "red"
        elif b_mean > r_mean and b_mean > g_mean:
            return "blue"
        else:
            return "mixed"

    def _has_mri_features(self, img_array: np.ndarray) -> bool:
        """Check for MRI-like features (simplified)."""
        # Look for high contrast, circular shapes, etc. (placeholder)
        return np.std(img_array) > 50  # High variance

    def _has_fur_texture(self, img_array: np.ndarray) -> bool:
        """Check for fur-like texture (simplified)."""
        # Placeholder: check for high frequency changes
        if len(img_array.shape) < 3:
            return False
        # Simple edge detection - avoid broadcasting issues
        gray = np.mean(img_array, axis=2)
        # Calculate horizontal and vertical gradients separately
        horiz_edges = np.abs(np.diff(gray, axis=1))  # Shape: (224, 223)
        vert_edges = np.abs(np.diff(gray, axis=0))  # Shape: (223, 224)
        # Use the minimum dimension to avoid shape mismatch
        min_h, min_w = min(horiz_edges.shape[0], vert_edges.shape[0]), min(
            horiz_edges.shape[1], vert_edges.shape[1]
        )
        edges = horiz_edges[:min_h, :min_w] + vert_edges[:min_h, :min_w]
        return np.mean(edges) > 20


# Global service instance
domain_detector_service = DomainDetectorService()
