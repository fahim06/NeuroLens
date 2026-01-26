import os
from datetime import datetime

import numpy as np
from PIL import Image
from taipy.gui import Gui
from tensorflow.keras import models

# Brand Configuration
BRAND_NAME = "NeuroLens"
BRAND_TAGLINE = "AI-Powered Image Classification with Deep Learning"
BRAND_VERSION = "2.0.0"
COPYRIGHT_YEAR = datetime.now().year
COPYRIGHT_HOLDER = "Fahim Yusuf"
GITHUB_URL = "https://github.com/fahim06"

class_names = {
    0: 'airplane',
    1: 'automobile',
    2: 'bird',
    3: 'cat',
    4: 'deer',
    5: 'dog',
    6: 'frog',
    7: 'horse',
    8: 'ship',
    9: 'truck',
}

basedir = os.path.dirname(__file__)


def get_asset_path(filename):
    """
    Helper to resolve asset paths.
    Checks the 'assets' directory.
    """
    return os.path.join(basedir, "../assets", filename)


model_path = get_asset_path("baseline_mariya.keras")
# Ensure the model exists before loading to avoid crash if files are missing entirely
if os.path.exists(model_path):
    try:
        model = models.load_model(model_path)
    except Exception as e:
        # In CI/CD or if file is corrupted (e.g. LFS pointer), we might fail to load.
        # We catch ValueError specifically for Keras loading issues.
        print(f"Warning: Failed to load model from {model_path}: {e}")
        model = None
else:
    print(f"Warning: Model file not found at {model_path}")
    model = None


def predict_image(model_n, path_to_img):
    if model_n is None:
        return 0, "Model not loaded"

    img = Image.open(path_to_img)
    img = img.convert("RGB")
    img = img.resize((32, 32))
    data = np.asarray(img)
    data = data / 255
    probs = model_n.predict(np.array([data])[:1])

    top_prob = probs.max()
    top_pred = class_names[np.argmax(probs)]

    return top_prob, top_pred


# Use relative paths for UI elements so Taipy can serve them
img_asset_path = get_asset_path("placeholder_image.png")
img_path = os.path.relpath(img_asset_path, os.getcwd())

logo_asset_path = get_asset_path("logo.png")
logo_path = os.path.relpath(logo_asset_path, os.getcwd())

# Favicon path - use favicon from root directory
favicon_path = "favicon.ico"

content = ""
prob = 0
pred = "Waiting for input..."

# Dynamic brand variables for UI
brand_name = BRAND_NAME
copyright_holder = COPYRIGHT_HOLDER
copyright_year = COPYRIGHT_YEAR
github_url = GITHUB_URL

index = """
<|app-wrapper|

<|header-container|
<|header-inner|
<|{logo_path}|image|class_name=app-logo|>
<|NeuroLens|text|class_name=app-title|>
<|AI-Powered Image Classification with Deep Learning|text|class_name=app-subtitle|>

<|layout|columns=1 1 1|gap=0.5rem|class_name=feature-tags|
<|🧠 CNN Model|text|class_name=feature-tag|>
<|⚡ Real-time Analysis|text|class_name=feature-tag|>
<|🎯 10 Classes|text|class_name=feature-tag|>
|>
|>
|>

<|main-layout|
<|layout|columns=1 1|columns[mobile]=1|gap=2.5rem|

<|card|
<|📤 Upload Image|text|class_name=card-title|>
<|{content}|file_selector|extensions=.png,.jpg,.jpeg|label=Choose Image|class_name=custom-file-selector|>
<|{img_path}|image|class_name=preview-image|>
<|Supports PNG, JPG, JPEG formats|text|class_name=label-text|>
|>

<|card|
<|🔍 Analysis Results|text|class_name=card-title|>

<|Predicted Class|text|class_name=label-text|>
<|{pred}|text|class_name=prediction-result|>

<|Confidence Score|text|class_name=label-text|>
<|{prob}|indicator|value={prob}|min=0|max=100|width=100%|class_name=custom-indicator|>

<|confidence-display|
<|{prob}%|text|class_name=confidence-value|>
<|Accuracy|text|class_name=confidence-label|>
|>
|>

|>
|>

<|footer|
<|footer-content|
<|{logo_path}|image|class_name=footer-logo|>
<|Built with Taipy & TensorFlow  •  © {copyright_year}|text|class_name=footer-text|>
<|{copyright_holder}|button|class_name=footer-author-btn|on_action=open_github|>
|>
|>

|>
"""


def open_github(state):
    """Open GitHub profile in new tab."""
    import webbrowser
    webbrowser.open(GITHUB_URL)


def on_change(state, var_name, var_val):
    if var_name == "content":
        top_prob, top_pred = predict_image(model, var_val)
        state.prob = round(top_prob * 100)
        state.pred = top_pred
        state.img_path = var_val
    # print(var_name, var_val)


app = Gui(page=index, css_file="main.css")
if __name__ == '__main__':
    # Use absolute path for favicon
    import pathlib

    project_root = pathlib.Path(__file__).parent.parent
    favicon_file = project_root / "assets" / "logo.png"
    app.run(use_reloader=True, port=5001, title="NeuroLens", favicon=str(favicon_file), watermark="")
