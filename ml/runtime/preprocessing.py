"""
Image Preprocessing — Centralized Image Preparation

Centralized image preprocessing for consistent and optimized inference.
Phase 6: Performance optimization.
"""

import numpy as np
from PIL import Image


def prepare_image(image: Image.Image, size=(224, 224)):
    """
    Prepare image for ML inference.

    Args:
        image: PIL Image object
        size: Target size as (width, height) tuple

    Returns:
        Preprocessed numpy array ready for model input
    """
    # Resize image
    img = image.resize(size)

    # Convert to RGB if necessary
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Convert to numpy array and normalize
    arr = np.array(img) / 255.0

    # Reshape for model input (add batch dimension)
    return arr.reshape(1, size[0], size[1], 3)


def prepare_image_for_domain(image: Image.Image, domain: str):
    """
    Prepare image based on domain-specific requirements.

    Args:
        image: PIL Image object
        domain: Domain string (animal, plant, medical, etc.)

    Returns:
        Preprocessed numpy array
    """
    # Currently all domains use same preprocessing
    # Future: domain-specific preprocessing (e.g., different sizes)
    if domain in ["animal", "plant"]:
        return prepare_image(image, size=(224, 224))
    elif domain == "medical":
        return prepare_image(image, size=(224, 224))  # Could be different
    else:
        return prepare_image(image, size=(224, 224))
