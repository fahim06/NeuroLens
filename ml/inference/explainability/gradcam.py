"""
Grad-CAM Explainability

Gradient-weighted Class Activation Mapping for CNN interpretability.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray


logger = logging.getLogger(__name__)

try:
    import tensorflow as tf
    from tensorflow import keras
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None
    keras = None


@dataclass
class GradCAMResult:
    """
    Grad-CAM result.
    
    Attributes:
        heatmap: Class activation heatmap (H, W)
        overlay: Heatmap overlaid on original image (H, W, 3)
        class_idx: Target class index
        class_name: Target class name
        activation_layer: Name of layer used
    """
    
    heatmap: NDArray[np.float32]
    overlay: NDArray[np.float32] | None = None
    class_idx: int = 0
    class_name: str = ""
    activation_layer: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding arrays)."""
        return {
            "class_idx": self.class_idx,
            "class_name": self.class_name,
            "activation_layer": self.activation_layer,
            "heatmap_shape": list(self.heatmap.shape),
        }


class GradCAM:
    """
    Grad-CAM for CNN explainability.
    
    Generates class activation heatmaps showing which regions
    of an image contributed most to the prediction.
    
    Example:
        >>> gradcam = GradCAM(model)
        >>> result = gradcam.compute(image, class_idx=0)
        >>> heatmap = result.heatmap
    """
    
    def __init__(
        self,
        model: keras.Model,
        layer_name: str | None = None,
        class_names: list[str] | None = None,
    ) -> None:
        """
        Initialize Grad-CAM.
        
        Args:
            model: Keras model
            layer_name: Name of convolutional layer to use
            class_names: Optional class names
        """
        if not HAS_TF:
            raise ImportError("TensorFlow is required for Grad-CAM")
        
        self.model = model
        self.class_names = class_names or []
        self.layer_name = layer_name or self._find_target_layer()
        
        # Create gradient model
        self._grad_model = self._build_grad_model()
        logger.info(f"Grad-CAM initialized with layer: {self.layer_name}")
    
    def _find_target_layer(self) -> str:
        """Find the last convolutional layer."""
        for layer in reversed(self.model.layers):
            if isinstance(layer, keras.layers.Conv2D):
                return layer.name
            # Check for layers inside nested models
            if hasattr(layer, "layers"):
                for inner_layer in reversed(layer.layers):
                    if isinstance(inner_layer, keras.layers.Conv2D):
                        return f"{layer.name}/{inner_layer.name}"
        
        raise ValueError("No convolutional layer found in model")
    
    def _build_grad_model(self) -> keras.Model:
        """Build model that outputs activations and predictions."""
        # Try to find the layer
        try:
            target_layer = self.model.get_layer(self.layer_name)
        except ValueError:
            # Try nested layer name
            if "/" in self.layer_name:
                parent_name, child_name = self.layer_name.split("/", 1)
                parent_layer = self.model.get_layer(parent_name)
                target_layer = parent_layer.get_layer(child_name)
            else:
                raise
        
        return keras.Model(
            inputs=self.model.input,
            outputs=[target_layer.output, self.model.output],
        )
    
    def compute(
        self,
        image: NDArray[np.float32],
        class_idx: int | None = None,
    ) -> GradCAMResult:
        """
        Compute Grad-CAM heatmap for an image.
        
        Args:
            image: Input image (H, W, C) or (1, H, W, C)
            class_idx: Target class index (None for predicted class)
        
        Returns:
            GradCAMResult with heatmap
        """
        # Add batch dimension if needed
        if image.ndim == 3:
            image = np.expand_dims(image, axis=0)
        
        image_tensor = tf.constant(image, dtype=tf.float32)
        
        # Compute gradients
        with tf.GradientTape() as tape:
            tape.watch(image_tensor)
            conv_outputs, predictions = self._grad_model(image_tensor)
            
            if class_idx is None:
                class_idx = tf.argmax(predictions[0]).numpy()
            
            class_output = predictions[:, class_idx]
        
        # Get gradients of the class output with respect to conv layer
        grads = tape.gradient(class_output, conv_outputs)
        
        # Global average pooling of gradients
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
        
        # Weight the channels by importance
        conv_outputs = conv_outputs[0]
        heatmap = tf.reduce_sum(conv_outputs * pooled_grads, axis=-1)
        
        # Apply ReLU
        heatmap = tf.maximum(heatmap, 0)
        
        # Normalize
        heatmap = heatmap / (tf.reduce_max(heatmap) + 1e-10)
        heatmap = heatmap.numpy()
        
        # Get class name
        class_name = ""
        if self.class_names and class_idx < len(self.class_names):
            class_name = self.class_names[class_idx]
        
        return GradCAMResult(
            heatmap=heatmap,
            class_idx=int(class_idx),
            class_name=class_name,
            activation_layer=self.layer_name,
        )
    
    def compute_with_overlay(
        self,
        image: NDArray[np.float32],
        class_idx: int | None = None,
        alpha: float = 0.4,
        colormap: str = "jet",
    ) -> GradCAMResult:
        """
        Compute Grad-CAM with overlay on original image.
        
        Args:
            image: Input image (H, W, C)
            class_idx: Target class index
            alpha: Overlay transparency
            colormap: Colormap to use
        
        Returns:
            GradCAMResult with heatmap and overlay
        """
        result = self.compute(image, class_idx)
        
        # Resize heatmap to image size
        if image.ndim == 4:
            image = image[0]
        
        h, w = image.shape[:2]
        heatmap_resized = tf.image.resize(
            result.heatmap[..., np.newaxis],
            [h, w],
            method="bilinear",
        ).numpy()[..., 0]
        
        # Apply colormap
        heatmap_colored = self._apply_colormap(heatmap_resized, colormap)
        
        # Normalize image to [0, 1] if needed
        if image.max() > 1.0:
            image_norm = image / 255.0
        else:
            image_norm = image
        
        # Create overlay
        overlay = (1 - alpha) * image_norm + alpha * heatmap_colored
        overlay = np.clip(overlay, 0, 1)
        
        result.heatmap = heatmap_resized
        result.overlay = overlay.astype(np.float32)
        
        return result
    
    def _apply_colormap(
        self,
        heatmap: NDArray[np.float32],
        colormap: str = "jet",
    ) -> NDArray[np.float32]:
        """Apply colormap to heatmap."""
        # Simple jet colormap implementation
        # In production, use matplotlib or custom colormap
        
        # Normalize to [0, 1]
        heatmap = np.clip(heatmap, 0, 1)
        
        # Create RGB channels for jet-like colormap
        r = np.clip(1.5 - np.abs(4 * heatmap - 3), 0, 1)
        g = np.clip(1.5 - np.abs(4 * heatmap - 2), 0, 1)
        b = np.clip(1.5 - np.abs(4 * heatmap - 1), 0, 1)
        
        return np.stack([r, g, b], axis=-1).astype(np.float32)
    
    def batch_compute(
        self,
        images: NDArray[np.float32],
        class_indices: list[int] | None = None,
    ) -> list[GradCAMResult]:
        """
        Compute Grad-CAM for a batch of images.
        
        Args:
            images: Batch of images (N, H, W, C)
            class_indices: List of target class indices
        
        Returns:
            List of GradCAMResult
        """
        results = []
        
        for i, image in enumerate(images):
            class_idx = class_indices[i] if class_indices else None
            result = self.compute(image, class_idx)
            results.append(result)
        
        return results


class GradCAMPlusPlus(GradCAM):
    """
    Grad-CAM++ for improved localization.
    
    Uses second-order gradients for better visualization.
    """
    
    def compute(
        self,
        image: NDArray[np.float32],
        class_idx: int | None = None,
    ) -> GradCAMResult:
        """Compute Grad-CAM++ heatmap."""
        if image.ndim == 3:
            image = np.expand_dims(image, axis=0)
        
        image_tensor = tf.constant(image, dtype=tf.float32)
        
        with tf.GradientTape() as tape2:
            with tf.GradientTape() as tape1:
                tape1.watch(image_tensor)
                conv_outputs, predictions = self._grad_model(image_tensor)
                
                if class_idx is None:
                    class_idx = tf.argmax(predictions[0]).numpy()
                
                class_output = predictions[:, class_idx]
            
            # First derivative
            grads = tape1.gradient(class_output, conv_outputs)
        
        # Second derivative
        grads2 = tape2.gradient(grads, conv_outputs)
        
        if grads2 is None:
            # Fall back to regular Grad-CAM
            return super().compute(image, class_idx)
        
        # Compute alpha weights
        conv_outputs_val = conv_outputs[0].numpy()
        grads_val = grads[0].numpy()
        grads2_val = grads2[0].numpy()
        
        # Alpha calculation for Grad-CAM++
        numerator = grads2_val
        denominator = 2 * grads2_val + conv_outputs_val * (grads2_val ** 2) + 1e-10
        alpha = numerator / denominator
        
        # Weight by positive gradients
        weights = np.maximum(grads_val, 0) * alpha
        weights = np.sum(weights, axis=(0, 1))
        
        # Generate heatmap
        heatmap = np.sum(conv_outputs_val * weights, axis=-1)
        heatmap = np.maximum(heatmap, 0)
        heatmap = heatmap / (np.max(heatmap) + 1e-10)
        
        class_name = ""
        if self.class_names and class_idx < len(self.class_names):
            class_name = self.class_names[class_idx]
        
        return GradCAMResult(
            heatmap=heatmap.astype(np.float32),
            class_idx=int(class_idx),
            class_name=class_name,
            activation_layer=self.layer_name,
        )
