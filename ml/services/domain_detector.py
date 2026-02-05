# ml/services/domain_detector.py
"""
Auto-Domain Detection Service.
Phase 10: The user never selects the model — the system does.

This service analyzes an uploaded image and determines:
1. Primary domain (human, animal, plant, medical)
2. Sub-category within that domain
3. Which model should be used
"""
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PrimaryDomain(Enum):
    """Primary content domains."""

    HUMAN = "human"
    ANIMAL = "animal"
    PLANT = "plant"
    MEDICAL = "medical"
    UNKNOWN = "unknown"


class SubCategory(Enum):
    """Sub-categories within domains."""

    # Human
    HUMAN_FACE = "human_face"
    HUMAN_BODY = "human_body"

    # Animal
    ANIMAL_MAMMAL = "mammal"
    ANIMAL_BIRD = "bird"
    ANIMAL_REPTILE = "reptile"
    ANIMAL_FISH = "fish"
    ANIMAL_INSECT = "insect"

    # Plant
    PLANT_CITRUS = "citrus"
    PLANT_LEAF = "leaf"
    PLANT_FLOWER = "flower"
    PLANT_FRUIT = "fruit"

    # Medical
    MEDICAL_BRAIN_MRI = "brain_mri"
    MEDICAL_XRAY = "xray"
    MEDICAL_CT = "ct_scan"

    UNKNOWN = "unknown"


@dataclass
class DomainDetectionResult:
    """Result of domain detection."""

    primary_domain: PrimaryDomain
    sub_category: SubCategory
    confidence: float
    recommended_model: str
    metadata: Dict[str, Any]


# Domain to model mapping
DOMAIN_MODEL_MAPPING = {
    PrimaryDomain.HUMAN: {
        SubCategory.HUMAN_FACE: "human_detector",
        SubCategory.HUMAN_BODY: "human_detector",
        SubCategory.UNKNOWN: "human_detector",
    },
    PrimaryDomain.ANIMAL: {
        SubCategory.ANIMAL_MAMMAL: "animal_classifier",
        SubCategory.ANIMAL_BIRD: "animal_classifier",
        SubCategory.ANIMAL_REPTILE: "animal_classifier",
        SubCategory.ANIMAL_FISH: "animal_classifier",
        SubCategory.ANIMAL_INSECT: "animal_classifier",
        SubCategory.UNKNOWN: "animal_classifier",
    },
    PrimaryDomain.PLANT: {
        SubCategory.PLANT_CITRUS: "citrus_classifier",
        SubCategory.PLANT_LEAF: "plant_classifier",
        SubCategory.PLANT_FLOWER: "plant_classifier",
        SubCategory.PLANT_FRUIT: "plant_classifier",
        SubCategory.UNKNOWN: "plant_classifier",
    },
    PrimaryDomain.MEDICAL: {
        SubCategory.MEDICAL_BRAIN_MRI: "brain_tumor_detector",
        SubCategory.MEDICAL_XRAY: "medical_classifier",
        SubCategory.MEDICAL_CT: "medical_classifier",
        SubCategory.UNKNOWN: "medical_classifier",
    },
}


class DomainDetectorService:
    """
    Auto-domain detection service.
    Analyzes image content to determine domain and select appropriate model.

    Phase 10: Implements the "Lightweight Domain Detector" concept.
    """

    def __init__(self):
        self._model = None
        self._model_available = False
        self._load_error: Optional[str] = None
        self._try_load_model()

    def _try_load_model(self):
        """Attempt to load the lightweight domain classifier."""
        try:
            # In production, this would load a small CNN for domain detection
            # For now, we use heuristic-based detection
            self._model_available = False
            self._load_error = "Lightweight domain classifier not yet trained"
            logger.info("Domain detector initialized with heuristic mode")
        except Exception as e:
            self._model_available = False
            self._load_error = str(e)
            logger.warning(f"Domain detector model not available: {e}")

    def detect_domain(self, image_data: bytes) -> DomainDetectionResult:
        """
        Detect the primary domain of an image.

        Args:
            image_data: Raw image bytes

        Returns:
            DomainDetectionResult with domain, category, and recommended model
        """
        if self._model_available and self._model:
            return self._model_detect(image_data)
        else:
            return self._heuristic_detect(image_data)

    def _model_detect(self, image_data: bytes) -> DomainDetectionResult:
        """Use trained model for domain detection."""
        # Future: Implement CNN-based detection
        raise NotImplementedError("Model-based detection not yet implemented")

    def _heuristic_detect(self, image_data: bytes) -> DomainDetectionResult:
        """
        Use heuristics to detect domain.

        In production, this would analyze:
        - Image dimensions (medical images have specific ratios)
        - Color distribution (MRI is grayscale, plants are green-heavy)
        - Edge patterns (X-rays have distinct patterns)

        For Phase 10, we return a smart default with metadata.
        """
        try:
            # Analyze image properties
            properties = self._analyze_image_properties(image_data)

            # Determine domain based on properties
            domain, category, confidence = self._classify_from_properties(properties)

            # Get recommended model
            recommended_model = self._get_model_for_domain(domain, category)

            return DomainDetectionResult(
                primary_domain=domain,
                sub_category=category,
                confidence=confidence,
                recommended_model=recommended_model,
                metadata={
                    "detection_method": "heuristic",
                    "image_properties": properties,
                    "model_available": self._model_available,
                },
            )
        except Exception as e:
            logger.error(f"Domain detection failed: {e}")
            return DomainDetectionResult(
                primary_domain=PrimaryDomain.UNKNOWN,
                sub_category=SubCategory.UNKNOWN,
                confidence=0.0,
                recommended_model="animal_classifier",  # Safe default
                metadata={
                    "detection_method": "fallback",
                    "error": str(e),
                },
            )

    def _analyze_image_properties(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze basic image properties for domain hints."""
        properties = {
            "size_bytes": len(image_data),
            "is_grayscale": False,
            "dominant_colors": [],
            "aspect_ratio": 1.0,
        }

        try:
            from PIL import Image
            import io

            img = Image.open(io.BytesIO(image_data))
            properties["width"] = img.width
            properties["height"] = img.height
            properties["aspect_ratio"] = (
                img.width / img.height if img.height > 0 else 1.0
            )
            properties["mode"] = img.mode
            properties["is_grayscale"] = img.mode in ("L", "LA", "1")

            # Sample colors for heuristics
            if img.mode != "L":
                img_rgb = img.convert("RGB")
                # Get a sample of pixels
                pixels = list(img_rgb.getdata())[:1000]
                if pixels:
                    # Calculate average color
                    avg_r = sum(p[0] for p in pixels) / len(pixels)
                    avg_g = sum(p[1] for p in pixels) / len(pixels)
                    avg_b = sum(p[2] for p in pixels) / len(pixels)
                    properties["avg_color"] = (avg_r, avg_g, avg_b)
                    properties["is_greenish"] = avg_g > avg_r and avg_g > avg_b

        except ImportError:
            logger.debug("PIL not available for image analysis")
        except Exception as e:
            logger.debug(f"Image analysis failed: {e}")

        return properties

    def _classify_from_properties(
        self, properties: Dict[str, Any]
    ) -> tuple[PrimaryDomain, SubCategory, float]:
        """
        Classify domain based on image properties.

        Heuristics:
        - Grayscale + square-ish = likely medical (MRI, X-ray)
        - Green dominant = likely plant
        - Standard aspect ratio + colors = likely animal/human
        """
        is_grayscale = properties.get("is_grayscale", False)
        is_greenish = properties.get("is_greenish", False)
        aspect_ratio = properties.get("aspect_ratio", 1.0)

        # Medical images are often grayscale with specific aspect ratios
        if is_grayscale:
            # Square-ish grayscale = likely brain MRI
            if 0.8 <= aspect_ratio <= 1.2:
                return PrimaryDomain.MEDICAL, SubCategory.MEDICAL_BRAIN_MRI, 0.75
            else:
                return PrimaryDomain.MEDICAL, SubCategory.MEDICAL_XRAY, 0.65

        # Green-dominant images = likely plant
        if is_greenish:
            # Could be citrus or other plant
            return PrimaryDomain.PLANT, SubCategory.PLANT_CITRUS, 0.70

        # Default to animal detection (most versatile)
        return PrimaryDomain.ANIMAL, SubCategory.UNKNOWN, 0.60

    def _get_model_for_domain(
        self, domain: PrimaryDomain, category: SubCategory
    ) -> str:
        """Get the recommended model for a domain/category combination."""
        domain_models = DOMAIN_MODEL_MAPPING.get(domain, {})
        model = domain_models.get(category)

        if not model:
            # Try unknown category for the domain
            model = domain_models.get(SubCategory.UNKNOWN)

        if not model:
            # Fallback to animal classifier
            model = "animal_classifier"

        return model


# Singleton instance
domain_detector_service = DomainDetectorService()
