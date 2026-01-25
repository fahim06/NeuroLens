from taipy.gui import Gui
from tensorflow.keras import models
from PIL import Image
import numpy as np
import os

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

content = ""
prob = 0
pred = ""

index = """
<|text-center|
<|{logo_path}|image|width=25vw|>

<|{content}|file_selector|extensions=.png|>
select an image from your file system

<|{pred}|>

<|{img_path}|image|>

<|{prob}|indicator|value={prob}|min=0|max=100|width=25vw|>
>
"""


def on_change(state, var_name, var_val):
    if var_name == "content":
        top_prob, top_pred = predict_image(model, var_val)
        state.prob = round(top_prob * 100)
        state.pred = "This is a " + top_pred
        state.img_path = var_val
    # print(var_name, var_val)


app = Gui(page=index)
if __name__ == '__main__':
    app.run(use_reloader=True, port="auto")
