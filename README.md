# NeuroLens: CIFAR-10 Image Classifier

<p align="center">
  <img src="assets/logo.png" alt="NeuroLens Logo" width="120">
</p>

<p align="center">
  <strong>AI-Powered Image Classification with Deep Learning</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
  <img src="https://img.shields.io/badge/framework-Taipy-purple.svg" alt="Taipy">
</p>

---

## 📖 Overview

**NeuroLens** is a professional **Graphical User Interface (GUI)** application designed to make deep learning
accessible. Built with **Taipy**, it interfaces with a **Convolutional Neural Network (CNN)** trained on the **CIFAR-10
** dataset. This application empowers users to upload images and receive real-time classification predictions, bridging
the gap between complex machine learning models and end-user interaction.

### Supported Classes (CIFAR-10)

The model can classify images into 10 distinct categories:

| Icon | Class      | Icon | Class |
|:----:|:-----------|:----:|:------|
|  ✈️  | Airplane   |  🐶  | Dog   |
|  🚗  | Automobile |  🐸  | Frog  |
|  🐦  | Bird       |  🐴  | Horse |
|  🐱  | Cat        |  🚢  | Ship  |
|  🦌  | Deer       |  🚚  | Truck |

---

## ✨ What's New in v2.0.0

- 🎨 **Modern UI Redesign** - Premium glassmorphism design with gradient accents
- 📱 **Fully Responsive** - Works on mobile, tablet, laptop, and desktop
- 🌙 **Dark Theme** - Beautiful dark mode interface
- ⚡ **Improved Performance** - Optimized CSS and animations
- 🔧 **Brand System** - Centralized branding configuration
- 🎯 **Better UX** - Cleaner layout with micro-interactions

---

## 🚀 Key Features

| Feature                         | Description                                               |
|:--------------------------------|:----------------------------------------------------------|
| 🖥️ **User-Friendly Interface** | Clean, modern web-based GUI requiring no coding knowledge |
| ⚡ **Real-Time Inference**       | Instant classification of uploaded images                 |
| 📊 **Visual Feedback**          | Displays image with prediction and confidence score       |
| 🌐 **Cross-Platform**           | Runs on Windows, macOS, and Linux                         |
| 📱 **Responsive Design**        | Works on all screen sizes                                 |
| 🎨 **Modern UI**                | Premium dark theme with glassmorphism effects             |

---

## 🛠 System Requirements

| Component   | Requirement                                                       |
|:------------|:------------------------------------------------------------------|
| **OS**      | Windows 10/11, macOS (Intel/Apple Silicon), Linux (Ubuntu 20.04+) |
| **Python**  | Version 3.10 or 3.11                                              |
| **CPU**     | Modern multi-core processor (Intel i5 / Ryzen 5 or better)        |
| **RAM**     | 8 GB minimum (16 GB recommended)                                  |
| **Storage** | 2 GB free space                                                   |

---

## 📦 Installation Guide

### 1. Clone the Repository

```bash
git clone git@github.com:fahim06/NeuroLens.git
cd NeuroLens
```

### 2. Set Up a Virtual Environment

#### Option A: Using `venv` (Standard Python)

**macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

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

### 1. Launch the Application

```bash
python src/classifier.py
```

### 2. Access the GUI

The application will automatically open in your default web browser at:

```
http://127.0.0.1:5001
```

### 3. Classify Images

1. Click **"Choose Image"** to select an image (PNG, JPG, JPEG)
2. View the predicted class and confidence score instantly
3. Try sample images from `demo_images/` for testing

---

## 📂 Project Structure

```plaintext
NeuroLens/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline configuration
├── assets/
│   ├── favicon/                # Multi-size favicon assets
│   │   ├── favicon.ico
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── favicon-48x48.png
│   │   ├── favicon-64x64.png
│   │   ├── apple-touch-icon.png
│   │   ├── android-chrome-192x192.png
│   │   └── android-chrome-512x512.png
│   ├── baseline_mariya.keras   # Pre-trained CNN model
│   ├── logo.png                # Application logo
│   ├── placeholder_image.png   # Default placeholder
│   └── site.webmanifest        # PWA manifest
├── demo_images/                # Sample images for testing
├── notebooks/
│   ├── NeuralNetworkBuilder.ipynb       # Detailed model training
│   └── NeuralNetworkQuickBuilder.ipynb  # Quick training script
├── src/
│   ├── classifier.py           # Main application entry point
│   └── main.css                # UI stylesheet with design system
├── tests/
│   └── test_classifier.py      # Unit tests
├── .gitignore
├── brand.json                  # Brand configuration
├── LICENSE                     # MIT License
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
└── SECURITY.md                 # Security policy
```

---

## 🧰 Technologies Used

| Technology                                          | Purpose                   |
|:----------------------------------------------------|:--------------------------|
| [**Python**](https://www.python.org/)               | Core programming language |
| [**Taipy**](https://www.taipy.io/)                  | Web application framework |
| [**TensorFlow/Keras**](https://www.tensorflow.org/) | Deep learning framework   |
| [**NumPy**](https://numpy.org/)                     | Numerical computation     |
| [**Pillow**](https://python-pillow.org/)            | Image processing          |

---

## 🧪 Running Tests

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

---

## 🎨 Design System

NeuroLens v2.0 features a comprehensive design system:

- **Color Palette**: Primary (Indigo) + Accent (Cyan) colors
- **Typography**: Inter font family with fluid scaling
- **Spacing**: Consistent 4px-based spacing scale
- **Components**: Cards, buttons, indicators with glassmorphism
- **Animations**: Smooth transitions and micro-interactions
- **Responsive**: 5 breakpoints (320px to 1536px+)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Fahim Yusuf**

- GitHub: [@fahim06](https://github.com/fahim06)

---

<p align="center">
  Built with ❤️ using Taipy & TensorFlow
</p>

