# NeuroLens Project Structure

> **Version:** 2.1.0  
> **Last Updated:** January 27, 2026  
> **Author:** Fahim Yusuf  
> **Status:** Production Ready (Fresh Environment)

This document provides a comprehensive overview of the NeuroLens project structure for AI assistants and developers.

---

## 📁 Directory Tree

```
NeuroLens/
├── .github/
│   └── workflows/                    # CI/CD pipeline configurations
├── .git/                             # Git version control
├── .idea/                            # IDE settings
├── assets/
│   ├── favicon/                      # Favicon assets (multiple sizes)
│   │   ├── android-chrome-192x192.png
│   │   ├── android-chrome-512x512.png
│   │   ├── apple-touch-icon.png
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── favicon-48x48.png
│   │   ├── favicon-64x64.png
│   │   ├── favicon.ico
│   │   └── logo.png
│   ├── baseline_mariya.keras         # Pre-trained CNN model (CIFAR-10)
│   ├── enhanced_model.keras          # Improved CNN model with augmentation
│   ├── logo.png                      # Main application logo (PNG)
│   ├── placeholder_image.png         # Default placeholder for UI
│   └── site.webmanifest              # PWA manifest
├── demo_images/                      # 24 sample images for testing
│   ├── demo_img1.png through demo_img22.png
│   ├── freepik_image1.png
│   └── freepik_image2.png
├── notebooks/                        # Jupyter notebooks for training
│   ├── EnhancedModelTraining.ipynb   # Advanced CNN with augmentation & validation
│   ├── NeuralNetworkBuilder.ipynb    # Main training notebook (improved v2.1.0)
│   ├── NeuralNetworkQuickBuilder.ipynb
│   └── TransferLearningMobileNetV2.ipynb # Transfer learning approach
├── src/                              # Source code
│   ├── classifier.py                 # Main application (Taipy GUI)
│   └── main.css                      # Complete UI stylesheet
├── tests/                            # Unit tests
│   └── test_classifier.py            # Test suite for classifier module
├── .gitignore                        # Git ignore rules
├── activate_neurolens.sh             # Environment activation script
├── brand.json                        # Brand configuration (colors, assets, metadata)
├── CHANGELOG.md                      # Version history and release notes
├── LICENSE                           # MIT License
├── PROJECT_STRUCTURE.md              # This file
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies (multi-platform)
└── SECURITY.md                       # Security policy and guidelines
```


---

## 🔑 Key Files

### Entry Point

| File                | Purpose                                         |
|---------------------|-------------------------------------------------|
| `src/classifier.py` | Main application - Taipy GUI with CNN inference |

### Configuration & Environment

| File                    | Purpose                                                      |
|-------------------------|--------------------------------------------------------------|
| `activate_neurolens.sh` | Conda environment activation script (Python 3.11)            |
| `brand.json`            | Centralized brand config (name, colors, assets, metadata)    |
| `requirements.txt`      | Python dependencies (tensorflow, numpy, taipy, pillow, etc.) |

### Styling & UI

| File           | Purpose                                         |
|----------------|-------------------------------------------------|
| `src/main.css` | Complete responsive UI stylesheet (1600+ lines) |

### Documentation

| File                   | Purpose                                       |
|------------------------|-----------------------------------------------|
| `README.md`            | Project overview, installation, usage guide   |
| `CHANGELOG.md`         | Version history with detailed release notes   |
| `SECURITY.md`          | Vulnerability reporting & security guidelines |
| `LICENSE`              | MIT License                                   |
| `PROJECT_STRUCTURE.md` | This file - project structure reference       |

### Models & Training

| File                                    | Purpose                             |
|-----------------------------------------|-------------------------------------|
| `assets/baseline_mariya.keras`          | Pre-trained CNN model for CIFAR-10  |
| `assets/enhanced_model.keras`           | Improved CNN with data augmentation |
| `notebooks/NeuralNetworkBuilder.ipynb`  | Main training notebook (v2.1.0)     |
| `notebooks/EnhancedModelTraining.ipynb` | Advanced training with improvements |

### Testing

| File                       | Purpose                          |
|----------------------------|----------------------------------|
| `tests/test_classifier.py` | Unit tests for classifier module |

---

## 🛠️ Technology Stack

### Core Framework

- **Taipy** - Web GUI framework (Python)
- **TensorFlow 2.15.0** - Deep learning framework
- **Keras** - Neural network API (bundled with TensorFlow)

### Data & ML

- **NumPy 1.24.3** - Numerical computing
- **SciPy 1.10.1** - Scientific computing
- **Pandas 2.0.3** - Data manipulation
- **Scikit-learn 1.3.0** - Machine learning tools

### Image Processing

- **Pillow 10.0.0** - Image processing library

### UI & Styling

- **Matplotlib 3.7.2** - Data visualization
- **Seaborn 0.12.2** - Statistical visualization
- **CSS3** - Responsive styling (1600+ lines)

### Environment

- **Python 3.11** (recommended, tested with 3.10+)
- **Conda** - Environment management
- **GPU Support** - Metal acceleration on M2+ Macs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                       │
│                    (Taipy GUI Framework)                    │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Upload Image   │    │      Analysis Results           │ │
│  │  - File Selector│    │  - Predicted Class              │ │
│  │  - Preview      │    │  - Confidence Score             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLASSIFIER MODULE                       │
│                    (src/classifier.py)                      │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  predict_image()│    │      Brand Configuration        │ │
│  │  - Load image   │    │  - BRAND_NAME, VERSION          │ │
│  │  - Preprocess   │    │  - COPYRIGHT_HOLDER             │ │
│  │  - Inference    │    │  - GITHUB_URL                   │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      CNN MODEL                              │
│              (assets/baseline_mariya.keras)                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  CIFAR-10 Trained Convolutional Neural Network          ││
│  │  - Input: 32x32 RGB images                              ││
│  │  - Output: 10 classes (airplane, automobile, bird,      ││
│  │            cat, deer, dog, frog, horse, ship, truck)    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Environment Setup

### Create Environment

```bash
conda create -n NeuroLens python=3.11 -y
conda activate NeuroLens
```

### Install Dependencies

```bash
# M2 Mac specific
conda install -c apple tensorflow-deps -y
pip install tensorflow-macos==2.15.0
pip install tensorflow-metal==1.1.0

# All other dependencies
pip install -r requirements.txt
```

### Activate Environment

```bash
source activate_neurolens.sh
```

---

## 🎨 CSS Structure (src/main.css)

The stylesheet contains 1600+ lines organized into sections:

- **Design System** - Color palette, typography, spacing
- **Base Styles** - Global resets, body styles
- **Animations** - fadeIn, scaleIn, slideIn keyframes
- **Layout** - app-wrapper, main-layout components
- **Header** - header-container, app-logo, app-title
- **Hero Section** - hero-section, hero-content
- **Cards & Containers** - card, card-title, card-icon
- **Forms & Inputs** - file-selector, upload-button
- **Image Preview** - preview-image, image-container
- **Results Display** - prediction-result, confidence-display
- **Footer** - footer, footer-content, footer-logo
- **Responsive Design** - Mobile (320px), Tablet (768px), Desktop (1024px+)
- **Accessibility** - Focus states, reduced-motion, high-contrast
- **Taipy Overrides** - Framework-specific styling

---

## 🔧 Brand Configuration (brand.json)

Contains centralized brand configuration:

- **Project name**: NeuroLens
- **Tagline**: AI-Powered Image Classification
- **Version**: 2.1.0
- **Author**: Fahim Yusuf
- **Primary color**: Indigo (#6366f1)
- **Accent color**: Cyan (#06b6d4)
- **Assets**: Logo, favicons, manifest file

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v
```

Test file: `tests/test_classifier.py`
- `test_class_names()` - Verify 10 CIFAR-10 classes
- `test_predict_image_no_model()` - Handle missing model
- `test_predict_image_with_mock_model()` - Mock prediction test

---

## 🚀 Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python src/classifier.py

# Access at http://localhost:5001
```

---

## 📱 Responsive Breakpoints

| Breakpoint      | Target Devices |
|-----------------|----------------|
| < 480px         | Mobile phones  |
| 480px - 767px   | Large phones   |
| 768px - 1023px  | Tablets        |
| 1024px - 1279px | Laptops        |
| 1280px - 1535px | Desktops       |
| ≥ 1536px        | Large displays |

---

## 🔄 Version History

| Version | Date       | Highlights                                                               |
|---------|------------|--------------------------------------------------------------------------|
| 2.1.0   | 2026-01-27 | Fresh Python 3.11 environment, cleaned dependencies, removed docs folder |
| 2.0.0   | 2026-01-26 | Complete UI redesign, dark theme, brand system                           |
| 1.0.0   | Initial    | Basic CIFAR-10 classifier with Taipy GUI                                 |

---

## 📝 Notes for AI Assistants

1. **Main entry point**: `src/classifier.py`
2. **Styling**: All CSS in `src/main.css` (1600+ lines)
3. **Model**: Keras `.keras` format in `assets/`
4. **Framework**: Taipy GUI (not Flask/Django)
5. **Python version**: 3.11 (recommended)
6. **Environment**: Fresh conda environment created Jan 27, 2026
7. **Port**: 5001 (default)
8. **GPU**: Metal acceleration on M2+ Macs
9. **Dependencies**: TensorFlow 2.15.0, NumPy 1.24.3, all specified in requirements.txt
10. **Favicon**: Use `assets/logo.png` for favicon parameter
11. **Watermark**: Disabled via `watermark=""` in `app.run()`
12. **No docs folder**: Documentation guides were removed after environment recreation
