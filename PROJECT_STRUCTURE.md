# NeuroLens Project Structure

> **Version:** 2.1.0  
> **Last Updated:** January 26, 2026  
> **Author:** Fahim Yusuf

This document provides a comprehensive overview of the NeuroLens project structure for AI assistants and developers.

---

## 📁 Directory Tree

```
NeuroLens/
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions CI/CD pipeline
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
│   ├── logo.png                      # Main application logo
│   ├── placeholder_image.png         # Default placeholder for image upload
│   └── site.webmanifest              # PWA manifest file
├── demo_images/                      # Sample images for testing (24 files)
│   ├── demo_img1.png ... demo_img22.png
│   ├── freepik_image1.png
│   └── freepik_image2.png
├── docs/                             # Documentation
│   └── ACCURACY_REPORT.md            # ML accuracy analysis report
├── notebooks/                        # Jupyter notebooks for model training
│   ├── EnhancedModelTraining.ipynb   # Improved training with augmentation
│   ├── NeuralNetworkBuilder.ipynb    # Detailed model training notebook
│   ├── NeuralNetworkQuickBuilder.ipynb # Quick training script
│   └── TransferLearningMobileNetV2.ipynb # Transfer learning (best accuracy)
├── src/                              # Source code
│   ├── classifier.py                 # Main application entry point
│   └── main.css                      # UI stylesheet (1600+ lines)
├── tests/                            # Unit tests
│   └── test_classifier.py            # Classifier module tests
├── .gitignore                        # Git ignore rules
├── brand.json                        # Brand configuration (colors, assets, metadata)
├── CHANGELOG.md                      # Version history and release notes
├── LICENSE                           # MIT License
├── PROJECT_STRUCTURE.md              # This file
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
└── SECURITY.md                       # Security policy
```

---

## 🔑 Key Files

### Entry Point
| File | Purpose |
|------|---------|
| `src/classifier.py` | Main application - Taipy GUI with CNN inference |

### Configuration
| File | Purpose |
|------|---------|
| `brand.json` | Centralized brand config (name, colors, assets, metadata) |
| `requirements.txt` | Python dependencies (taipy, tensorflow, numpy, pillow) |
| `.gitignore` | Git ignore patterns |

### Styling
| File | Purpose |
|------|---------|
| `src/main.css` | Complete UI stylesheet with CSS variables, responsive breakpoints, animations |

### Documentation
| File | Purpose |
|------|---------|
| `README.md` | Project overview, installation, usage |
| `CHANGELOG.md` | Version history with detailed release notes |
| `SECURITY.md` | Vulnerability reporting guidelines |
| `LICENSE` | MIT License |

### AI/ML
| File | Purpose |
|------|---------|
| `assets/baseline_mariya.keras` | Pre-trained CNN model for CIFAR-10 classification |
| `notebooks/*.ipynb` | Model training notebooks |

### CI/CD
| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | GitHub Actions pipeline (Python 3.10, 3.11) |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│                    (Taipy GUI Framework)                     │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │  Upload Image   │    │      Analysis Results           │ │
│  │  - File Selector│    │  - Predicted Class              │ │
│  │  - Preview      │    │  - Confidence Score             │ │
│  └─────────────────┘    └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CLASSIFIER MODULE                        │
│                    (src/classifier.py)                       │
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
│                      CNN MODEL                               │
│              (assets/baseline_mariya.keras)                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  CIFAR-10 Trained Convolutional Neural Network          ││
│  │  - Input: 32x32 RGB images                              ││
│  │  - Output: 10 classes (airplane, automobile, bird,      ││
│  │            cat, deer, dog, frog, horse, ship, truck)    ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies

```
taipy          # Web GUI framework
tensorflow     # Deep learning (v2.15.0)
numpy          # Numerical computing (<2.0.0)
pillow         # Image processing
```

---

## 🎨 CSS Structure (src/main.css)

The stylesheet is organized into 14 sections:

1. **Design System & CSS Variables** - Color palette, typography, spacing
2. **Base Styles & Reset** - Global resets, body styles
3. **Animations & Keyframes** - fadeIn, scaleIn, slideIn, etc.
4. **Layout Components** - app-wrapper, main-layout
5. **Header & Navigation** - header-container, app-logo, app-title
6. **Hero Section** - hero-section, hero-content
7. **Cards & Containers** - card, card-title, card-icon
8. **Form Elements & Inputs** - file-selector, upload-button
9. **Image Preview** - preview-image, image-container
10. **Results & Data Display** - prediction-result, confidence-display
11. **Footer** - footer, footer-content, footer-logo
12. **Responsive Breakpoints** - 320px, 480px, 768px, 1024px, 1280px, 1536px
13. **Accessibility & States** - focus-visible, reduced-motion, high-contrast
14. **Taipy-Specific Overrides** - taipy-layout, taipy-text, taipy-image

---

## 🔧 Brand Configuration (brand.json)

```json
{
  "brand": {
    "name": "NeuroLens",
    "tagline": "AI-Powered Image Classification with Deep Learning",
    "version": "2.1.0",
    "author": "Fahim Yusuf"
  },
  "assets": {
    "logo": { "primary": "assets/logo.png", "favicon": "assets/favicon/*" }
  },
  "colors": {
    "primary": "#6366f1 (Indigo)",
    "accent": "#06b6d4 (Cyan)"
  }
}
```

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

| Breakpoint | Target Devices |
|------------|----------------|
| < 480px | Mobile phones |
| 480px - 767px | Large phones |
| 768px - 1023px | Tablets |
| 1024px - 1279px | Laptops |
| 1280px - 1535px | Desktops |
| ≥ 1536px | Large displays |

---

## 🔄 Version History

| Version | Date | Highlights |
|---------|------|------------|
| 2.1.0 | 2026-01-26 | Fluid typography, enhanced responsiveness, code cleanup |
| 2.0.0 | 2026-01-26 | Complete UI redesign, dark theme, brand system |
| 1.0.0 | Initial | Basic CIFAR-10 classifier with Taipy GUI |

---

## 📝 Notes for AI Assistants

1. **Main entry point**: `src/classifier.py`
2. **Styling**: All CSS in `src/main.css` (no external CSS imports)
3. **Model**: Keras `.keras` format in `assets/`
4. **Framework**: Taipy GUI (not Flask/Django)
5. **Python version**: 3.10 or 3.11
6. **Port**: 5001 (default)
7. **Favicon**: Use `assets/logo.png` for favicon parameter
8. **Watermark**: Disabled via `watermark=""` in `app.run()`
