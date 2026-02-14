"""
Multi-Domain Predictor Service — ML Inference Interface

Phase 10: Upgraded from single DR detection to multi-domain detection.
Routes requests based on detection_type to appropriate models.

This service provides the interface for ML predictions.
It bridges the Django API layer with the ML runtime.
"""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MultiDomainPredictorService:
    """
    Service class for handling multi-domain prediction requests.
    Abstracts ML implementation from API layer.

    Supports:
    - Human vs Animal Detection
    - Animal Category Detection
    - Biological Classification (Kingdom → Species)
    - Brain Tumor Detection
    - Citrus Classification
    """

    # Available detection types
    DETECTION_TYPES = {
        "human_animal": {
            "name": "Human vs Animal Detection",
            "description": "Binary detection: human or animal",
        },
        "animal_category": {
            "name": "Animal Category Detection",
            "description": "Classify animal species/category",
        },
        "biological": {
            "name": "Biological Classification",
            "description": "Full taxonomy: Kingdom → Species",
        },
        "brain_tumor": {
            "name": "Brain Tumor Detection",
            "description": "Medical MRI analysis for tumor detection",
        },
        "citrus": {
            "name": "Citrus Classification",
            "description": "Citrus fruit genus identification",
        },
    }

    def __init__(self):
        """Initialize the predictor service."""
        self._engine = None
        self._ml_available = False
        self._init_error = None
        self._initialize_ml()

    def _initialize_ml(self):
        """
        Attempt to initialize the ML inference engine.
        Falls back to mock mode if ML is not available.
        """
        try:
            from ml.inference_engine import inference_engine

            self._engine = inference_engine
            self._ml_available = True
            logger.info("Multi-domain inference engine initialized")
        except ImportError as e:
            self._init_error = f"ML runtime not available: {e}"
            logger.warning(self._init_error)
            self._ml_available = False
        except Exception as e:
            self._init_error = f"ML initialization failed: {e}"
            logger.error(self._init_error)
            self._ml_available = False

    def get_detection_types(self) -> List[Dict[str, str]]:
        """
        Get list of available detection types for UI dropdown.

        Returns:
            List of detection type options
        """
        if self._ml_available and self._engine:
            try:
                return self._engine.get_available_detection_types()
            except Exception:
                pass

        return [
            {"value": k, "name": v["name"], "description": v["description"]}
            for k, v in self.DETECTION_TYPES.items()
        ]

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a prediction based on the input payload.

        Args:
            payload: Dictionary containing:
                - detection_type: Type of detection to perform
                - image_data: Base64 encoded image or image URL

        Returns:
            Dictionary containing prediction results
        """
        # Validate payload
        if not payload:
            raise ValueError("Empty payload provided")

        detection_type = payload.get("detection_type")
        if not detection_type:
            raise ValueError("detection_type is required")

        if detection_type not in self.DETECTION_TYPES:
            raise ValueError(
                f"Invalid detection_type: {detection_type}. "
                f"Valid types: {list(self.DETECTION_TYPES.keys())}"
            )

        # Get image data
        image_data = payload.get("image_data") or payload.get("image_url")
        if not image_data:
            raise ValueError("image_data or image_url is required")

        # Try ML prediction if available
        if self._ml_available and self._engine:
            try:
                result = self._engine.predict(image_data, detection_type)
                return result
            except Exception as e:
                logger.error(f"ML prediction failed, falling back to mock: {e}")

        # Fallback to mock prediction
        return self._mock_predict(detection_type)

    def _mock_predict(self, detection_type: str) -> Dict[str, Any]:
        """
        Generate mock prediction results.
        Used when ML runtime is not available.
        """
        type_info = self.DETECTION_TYPES[detection_type]

        if detection_type == "human_animal":
            prediction = self._mock_human_animal()
        elif detection_type == "animal_category":
            prediction = self._mock_animal_category()
        elif detection_type == "biological":
            prediction = self._mock_biological()
        elif detection_type == "brain_tumor":
            prediction = self._mock_brain_tumor()
        elif detection_type == "citrus":
            prediction = self._mock_citrus()
        else:
            prediction = {"error": "Unknown detection type"}

        return {
            "success": True,
            "detection_type": detection_type,
            "detection_name": type_info["name"],
            "prediction": prediction,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "is_mock": True,
                "reason": self._init_error or "ML runtime not initialized",
            },
        }

    def _mock_human_animal(self) -> Dict[str, Any]:
        """Mock human vs animal detection."""
        confidence = random.uniform(0.80, 0.98)
        is_human = random.random() > 0.5
        return {
            "predicted_class": "Human" if is_human else "Animal",
            "confidence": round(confidence, 4),
            "all_classes": [
                {
                    "label": "Human",
                    "confidence": round(confidence if is_human else 1 - confidence, 4),
                },
                {
                    "label": "Animal",
                    "confidence": round(1 - confidence if is_human else confidence, 4),
                },
            ],
        }

    def _mock_animal_category(self) -> Dict[str, Any]:
        """Mock animal category detection."""
        categories = [
            "Dog",
            "Cat",
            "Bird",
            "Fish",
            "Reptile",
            "Mammal",
            "Insect",
            "Primate",
        ]
        predicted = random.choice(categories)
        confidence = random.uniform(0.75, 0.95)
        return {
            "predicted_class": predicted,
            "confidence": round(confidence, 4),
            "species": f"{predicted.lower()}_species_example",
        }

    def _mock_biological(self) -> Dict[str, Any]:
        """Mock biological classification with full hierarchy."""
        taxonomies = [
            {
                "Kingdom": "Animalia",
                "Phylum": "Chordata",
                "Class": "Mammalia",
                "Order": "Carnivora",
                "Family": "Felidae",
                "Genus": "Panthera",
                "Species": "Panthera leo",
            },
            {
                "Kingdom": "Animalia",
                "Phylum": "Chordata",
                "Class": "Aves",
                "Order": "Passeriformes",
                "Family": "Corvidae",
                "Genus": "Corvus",
                "Species": "Corvus corax",
            },
            {
                "Kingdom": "Plantae",
                "Phylum": "Magnoliophyta",
                "Class": "Magnoliopsida",
                "Order": "Sapindales",
                "Family": "Rutaceae",
                "Genus": "Citrus",
                "Species": "Citrus sinensis",
            },
        ]
        taxonomy = random.choice(taxonomies)
        confidence = random.uniform(0.85, 0.98)

        return {
            "hierarchy": taxonomy,
            "formatted": " → ".join(taxonomy.values()),
            "confidence": round(confidence, 4),
        }

    def _mock_brain_tumor(self) -> Dict[str, Any]:
        """Mock brain tumor detection with medical-safe labels."""
        confidence = random.uniform(0.85, 0.98)
        is_tumor = random.random() > 0.7  # Bias towards no tumor for safety

        result = {
            "predicted_class": "Tumor" if is_tumor else "No Tumor",
            "confidence": round(confidence, 4),
            "is_tumor": is_tumor,
            "all_classes": [
                {
                    "label": "No Tumor",
                    "confidence": round(1 - confidence if is_tumor else confidence, 4),
                },
                {
                    "label": "Tumor",
                    "confidence": round(confidence if is_tumor else 1 - confidence, 4),
                },
            ],
        }

        # Add medical note
        if is_tumor:
            result["medical_note"] = (
                "Potential tumor detected. Consult physician for confirmation."
            )
        else:
            result["medical_note"] = (
                "No tumor indicators detected. Regular checkups recommended."
            )

        return result

    def _mock_citrus(self) -> Dict[str, Any]:
        """Mock citrus classification."""
        citrus_types = [
            "Limon Criollo",
            "Limon Mandarino",
            "Mandarina Pieldesapo",
            "Mandarina Israeli",
            "Naranja Valencia",
            "Tangelo",
            "Toronja",
            "Lima",
        ]
        predicted = random.choice(citrus_types)
        confidence = random.uniform(0.88, 0.99)

        # Generate top 3 predictions
        other_types = [c for c in citrus_types if c != predicted]
        random.shuffle(other_types)

        return {
            "predicted_class": predicted,
            "confidence": round(confidence, 4),
            "top_predictions": [
                {"label": predicted, "confidence": round(confidence, 4)},
                {
                    "label": other_types[0],
                    "confidence": round(random.uniform(0.01, 0.08), 4),
                },
                {
                    "label": other_types[1],
                    "confidence": round(random.uniform(0.01, 0.05), 4),
                },
            ],
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the predictor service is healthy.
        """
        return {
            "status": "healthy" if self._ml_available else "degraded",
            "engine_loaded": self._ml_available,
            "is_mock": not self._ml_available,
            "detection_types": list(self.DETECTION_TYPES.keys()),
            "error": self._init_error,
        }

    def auto_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Auto-analyze an image without requiring detection type selection.

        Phase 10: The user never selects the model — the system does.

        Args:
            payload: Dictionary containing image_data or image_url

        Returns:
            Dictionary containing:
                - detected_domain: Primary domain detected
                - model_used: Which model was selected
                - prediction: Model-specific results
                - biological_classification: Taxonomy if applicable
        """
        # Get image data
        image_data = payload.get("image_data") or payload.get("image_url")
        if not image_data:
            raise ValueError("image_data or image_url is required")

        # Try to use model router for auto-detection
        try:
            from ml.services.model_router import model_router
            from ml.services.domain_detector import domain_detector_service

            # Decode base64 if needed
            image_bytes = self._get_image_bytes(image_data)
            from PIL import Image
            from io import BytesIO

            image = Image.open(BytesIO(image_bytes))

            # Detect domain
            domain_result = domain_detector_service.detect(image)

            # Route to predictor
            predictor = model_router.get_predictor(domain_result.domain)

            # Get prediction
            prediction_result = predictor.predict(image)

            return {
                "success": True,
                "mode": "auto_analyze",
                "detected_domain": domain_result.domain.value,
                "domain_confidence": domain_result.confidence,
                "model_used": predictor.__class__.__name__,
                "prediction": {
                    "label": prediction_result.label,
                    "confidence": prediction_result.confidence,
                },
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": domain_result.meta,
            }

        except ImportError as e:
            logger.warning(f"Model router not available: {e}")
            return self._mock_auto_analyze()
        except Exception as e:
            logger.error(f"Auto-analyze failed: {e}")
            return self._mock_auto_analyze()

    def _get_image_bytes(self, image_data: str) -> bytes:
        """Convert base64 image data to bytes."""
        import base64

        if image_data.startswith("data:"):
            # Remove data URL prefix
            _, encoded = image_data.split(",", 1)
            return base64.b64decode(encoded)
        elif image_data.startswith("http"):
            # Fetch from URL
            import urllib.request

            with urllib.request.urlopen(image_data) as response:
                return response.read()
        else:
            # Assume raw base64
            return base64.b64decode(image_data)

    def _mock_auto_analyze(self) -> Dict[str, Any]:
        """Generate mock auto-analysis results."""
        # Pick a random domain for demo
        domains = ["animal", "plant", "medical"]
        domain = random.choice(domains)

        if domain == "animal":
            prediction = self._mock_biological()
            model_used = "animal_classifier"
            category = "mammal"
        elif domain == "plant":
            prediction = self._mock_citrus()
            prediction["biological_classification"] = {
                "Kingdom": "Plantae",
                "Phylum": "Tracheophyta",
                "Class": "Magnoliopsida",
                "Order": "Sapindales",
                "Family": "Rutaceae",
                "Genus": "Citrus",
                "Species": f"Citrus {prediction['predicted_class'].lower().replace(' ', '_')}",
            }
            model_used = "citrus_classifier"
            category = "citrus"
        else:
            prediction = self._mock_brain_tumor()
            model_used = "brain_tumor_detector"
            category = "brain_mri"

        return {
            "success": True,
            "mode": "auto_analyze",
            "detected_domain": domain,
            "detected_category": category,
            "domain_confidence": round(random.uniform(0.70, 0.90), 2),
            "model_used": model_used,
            "prediction": prediction,
            "biological_classification": prediction.get("biological_classification")
            or prediction.get("hierarchy"),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "is_mock": True,
                "detection_method": "heuristic",
                "reason": self._init_error or "ML runtime not initialized",
            },
        }


# Singleton instance
predictor_service = MultiDomainPredictorService()
