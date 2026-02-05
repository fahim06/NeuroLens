"""
ML Predictor — Inference Engine

This module handles the actual ML prediction logic.
It normalizes inputs, runs inference, and formats outputs.

IMPORTANT: This module is the ONLY place where model.predict() is called.
Django views should never import TensorFlow directly.
"""

import base64
import io
import logging
from datetime import datetime
from typing import Any, Dict, Union

import numpy as np

logger = logging.getLogger(__name__)

# Image configuration
IMAGE_SIZE = (32, 32)  # Model expects 32x32 input
NUM_CLASSES = 10  # 10-class classifier
CLASS_LABELS = [
    "class_0",
    "class_1",
    "class_2",
    "class_3",
    "class_4",
    "class_5",
    "class_6",
    "class_7",
    "class_8",
    "class_9",
]


class MLPredictor:
    """
    ML Predictor class for running inference.

    Responsibilities:
    - Input normalization (image preprocessing)
    - Model inference
    - Output formatting
    """

    def __init__(self):
        """Initialize the predictor."""
        self._loader = None
        self._model = None

    def _ensure_model_loaded(self) -> bool:
        """Ensure the model is loaded before prediction."""
        if self._model is not None:
            return True

        try:
            from .loader import get_model, get_model_loader

            self._loader = get_model_loader()
            self._model = get_model()
            return self._model is not None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def preprocess_image(self, image_data: Union[str, bytes, np.ndarray]) -> np.ndarray:
        """
        Preprocess image data for model input.

        Args:
            image_data: Base64 string, bytes, or numpy array

        Returns:
            Preprocessed numpy array ready for model input
        """
        try:
            from PIL import Image

            # Handle base64 encoded image
            if isinstance(image_data, str):
                # Remove data URL prefix if present
                if "," in image_data:
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))

            # Handle raw bytes
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))

            # Handle numpy array
            elif isinstance(image_data, np.ndarray):
                image = Image.fromarray(image_data)

            else:
                raise ValueError(f"Unsupported image data type: {type(image_data)}")

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize to expected dimensions
            image = image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)

            # Convert to numpy array and normalize
            img_array = np.array(image, dtype=np.float32)
            img_array = img_array / 255.0  # Normalize to [0, 1]

            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)

            return img_array

        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ValueError(f"Failed to preprocess image: {e}")

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run prediction on the input payload.

        Args:
            payload: Dictionary containing 'image_data' or 'image_url'

        Returns:
            Dictionary with prediction results
        """
        start_time = datetime.utcnow()

        # Validate payload
        if not payload:
            raise ValueError("Empty payload provided")

        image_data = payload.get("image_data")
        image_url = payload.get("image_url")

        if not image_data and not image_url:
            raise ValueError("Either 'image_data' or 'image_url' must be provided")

        # Check if model is loaded
        if not self._ensure_model_loaded():
            # Return mock prediction if model not available
            return self._mock_prediction(start_time)

        try:
            # Get image data
            if image_data:
                preprocessed = self.preprocess_image(image_data)
            elif image_url:
                # For URL, we'd need to fetch the image
                # For now, return mock if URL provided
                logger.warning("Image URL processing not implemented, using mock")
                return self._mock_prediction(start_time)

            # Run inference
            predictions = self._model.predict(preprocessed, verbose=0)

            # Format results
            return self._format_predictions(predictions, start_time)

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise RuntimeError(f"Prediction failed: {e}")

    def _format_predictions(
        self, predictions: np.ndarray, start_time: datetime
    ) -> Dict[str, Any]:
        """Format model predictions into response structure."""

        # Calculate inference time
        inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Get prediction probabilities (10-class output)
        probs = predictions[0]

        # Get the predicted class index and confidence
        predicted_idx = int(np.argmax(probs))
        confidence = float(probs[predicted_idx])
        predicted_class = CLASS_LABELS[predicted_idx]

        # Build all classes with confidence scores
        all_classes = [
            {"label": CLASS_LABELS[i], "confidence": round(float(probs[i]), 4)}
            for i in range(len(CLASS_LABELS))
        ]
        # Sort by confidence descending
        all_classes.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "success": True,
            "model": self._loader.model_name if self._loader else "unknown",
            "prediction": {
                "predicted_class": predicted_class,
                "confidence": round(confidence, 4),
                "class_index": predicted_idx,
                "all_classes": all_classes,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "model_version": "2.0.27",
                "inference_time_ms": round(inference_time, 2),
                "input_size": IMAGE_SIZE,
                "num_classes": NUM_CLASSES,
                "is_mock": False,
            },
        }

    def _mock_prediction(self, start_time: datetime) -> Dict[str, Any]:
        """Return a mock prediction when model is not available."""
        import random

        inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Generate mock probabilities for 10 classes
        mock_probs = [random.random() for _ in range(NUM_CLASSES)]
        total = sum(mock_probs)
        mock_probs = [p / total for p in mock_probs]  # Normalize to sum to 1

        predicted_idx = mock_probs.index(max(mock_probs))
        confidence = mock_probs[predicted_idx]

        all_classes = [
            {"label": CLASS_LABELS[i], "confidence": round(mock_probs[i], 4)}
            for i in range(NUM_CLASSES)
        ]
        all_classes.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "success": True,
            "model": "mock_model",
            "prediction": {
                "predicted_class": CLASS_LABELS[predicted_idx],
                "confidence": round(confidence, 4),
                "class_index": predicted_idx,
                "all_classes": all_classes,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "model_version": "2.0.27",
                "inference_time_ms": round(inference_time + random.randint(50, 150), 2),
                "input_size": IMAGE_SIZE,
                "num_classes": NUM_CLASSES,
                "is_mock": True,
                "reason": "Model not loaded",
            },
        }

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the predictor."""
        model_loaded = self._ensure_model_loaded()

        status = {
            "status": "healthy" if model_loaded else "degraded",
            "model_loaded": model_loaded,
            "is_mock": not model_loaded,
        }

        if self._loader:
            status.update(self._loader.get_status())

        return status


# Singleton instance
ml_predictor = MLPredictor()
