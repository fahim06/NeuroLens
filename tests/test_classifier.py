import os
import sys
import pytest
from PIL import Image
import numpy as np

# Add src to path so we can import classifier
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from classifier import predict_image, class_names


# Mock model for testing
class MockModel:
    def predict(self, data):
        # Return a dummy probability array (1 sample, 10 classes)
        # Let's say index 3 (cat) has the highest probability
        probs = np.zeros((1, 10))
        probs[0, 3] = 0.9
        return probs


def test_class_names():
    assert len(class_names) == 10
    assert class_names[0] == 'airplane'
    assert class_names[9] == 'truck'


def test_predict_image_no_model():
    prob, pred = predict_image(None, "dummy_path")
    assert prob == 0
    assert pred == "Model not loaded"


def test_predict_image_with_mock_model(tmp_path):
    # Create a dummy image file
    img_path = tmp_path / "test_image.png"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)

    mock_model = MockModel()

    prob, pred = predict_image(mock_model, str(img_path))

    assert prob == 0.9
    assert pred == 'cat'
