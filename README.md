# NeuroLens: CIFAR-10 Image Classifier

![Project Banner](assets/logo.png)

## 📖 Overview

**NeuroLens** is a professional **Graphical User Interface (GUI)** application designed to make deep learning
accessible. Built with **Taipy**, it interfaces with a **Convolutional Neural Network (CNN)** trained on the **CIFAR-10
** dataset. This application empowers users to upload images and receive real-time classification predictions, bridging
the gap between complex machine learning models and end-user interaction.

The **CIFAR-10** dataset comprises 60,000 32x32 color images across 10 distinct classes:

* ✈️ Airplane
* 🚗 Automobile
* 🐦 Bird
* 🐱 Cat
* 🦌 Deer
* 🐶 Dog
* 🐸 Frog
* 🐴 Horse
* 🚢 Ship
* 🚚 Truck

---

## 🚀 Key Features

* **User-Friendly Interface:** A clean, web-based GUI that requires no coding knowledge to operate.
* **Real-Time Inference:** Instant classification of uploaded images using a pre-trained CNN model.
* **Visual Feedback:** Displays the uploaded image alongside the model's prediction and confidence score.
* **Cross-Platform:** Runs seamlessly on Windows, macOS, and Linux.

---

## 🛠 System Requirements

To ensure optimal performance, your system should meet the following specifications:

| Component | Requirement |
| :--- | :--- |
| **OS** | Windows 10/11, macOS (Intel/Apple Silicon), Linux (Ubuntu 20.04+) |
| **Python** | Version 3.9, 3.10, or 3.11 (3.12+ not fully supported by TensorFlow yet) |
| **CPU** | Modern multi-core processor (Intel i5 / Ryzen 5 or better) |
| **RAM** | 8 GB minimum (16 GB recommended) |
| **Storage** | 2 GB free space |

---

## 📦 Installation Guide

Follow these steps to set up NeuroLens on your local machine.

### 1. Clone the Repository

```bash
git clone git@github.com:fahim06/NeuroLens.git
cd NeuroLens
```

### 2. Set Up a Virtual Environment

Isolating dependencies is highly recommended. Choose one of the methods below:

#### Option A: Using `venv` (Standard Python)

* **macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
* **Windows:**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```

#### Option B: Using Conda

```bash
conda create --name neurolens python=3.10
conda activate neurolens
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🖥️ Usage

1. **Launch the Application:**
   Ensure your virtual environment is active, then run:
   ```bash
   python src/classifier.py
   ```

2. **Access the GUI:**
   The application will automatically open in your default web browser. If not, navigate to the URL displayed in your
   terminal (typically `http://127.0.0.1:5000`).

3. **Classify Images:**
    * Click the **"Browse"** button to select an image from your computer.
    * (Optional) Use sample images located in `assets/demo_images/` for quick testing.
    * View the predicted class and probability score instantly.

---

## 📂 Project Structure

```plaintext
NeuroLens/
├── .github/                # CI/CD workflows
├── assets/                 # Static resources and models
│   ├── demo_images/        # Sample images for testing
│   ├── baseline_mariya.keras  # Pre-trained CNN model
│   ├── logo.png            # Application branding
│   └── placeholder_image.png
├── notebooks/              # Research & Development
│   ├── NeuralNetworkBuilder.ipynb       # Detailed model training steps
│   └── NeuralNetworkQuickBuilder.ipynb  # Concise training script
├── src/                    # Application Source Code
│   └── classifier.py       # Main entry point (Taipy GUI logic)
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
└── README.md               # Project Documentation
```

---

## 🧰 Technologies Used

* **[Python](https://www.python.org/):** Core programming language.
* **[Taipy](https://www.taipy.io/):** Framework for building data and AI web applications.
* **[TensorFlow](https://www.tensorflow.org/) / [Keras](https://keras.io/):** Deep learning framework for model training
  and inference.
* **[NumPy](https://numpy.org/):** Efficient numerical computation.
* **[Pillow (PIL)](https://python-pillow.org/):** Image processing library.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
