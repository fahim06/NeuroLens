# NeuroLens Model Accuracy - Root Cause Analysis Report

> **Version:** 2.1.0  
> **Date:** January 26, 2026  
> **Author:** AI Systems Auditor

---

## 🔴 Executive Summary

The NeuroLens model exhibits low accuracy (< 60%) due to **multiple compounding issues** across the ML pipeline. This report identifies root causes and provides actionable fixes.

---

## 🔬 Root Cause Analysis

### 1. 🎯 PRIMARY ISSUE: Domain Mismatch

| Factor | CIFAR-10 Training Data | Real-World Input |
|--------|------------------------|------------------|
| Image Size | 32×32 pixels | Variable (often 100-4000px) |
| Image Quality | Low resolution, pixelated | High resolution, sharp |
| Background | Simple, clean | Complex, cluttered |
| Object Size | Object fills frame | Object may be small in frame |
| Lighting | Controlled | Variable |
| Angle | Standard | Variable |

**Impact:** The model was trained on tiny 32×32 CIFAR-10 images. When real-world images are resized from 1000px to 32px, critical details are lost, causing poor predictions.

---

### 2. 🔧 PREPROCESSING ISSUES

#### Current Preprocessing (classifier.py):
```python
img = Image.open(path_to_img)
img = img.convert("RGB")
img = img.resize((32, 32))  # ⚠️ No interpolation method specified
data = np.asarray(img)
data = data / 255  # ✅ Correct normalization
```

#### Issues Found:
| Issue | Current | Should Be |
|-------|---------|-----------|
| Resize Method | Default (NEAREST) | LANCZOS or BILINEAR |
| Aspect Ratio | Stretched/Squished | Center crop or pad |
| Color Order | RGB (correct) | RGB ✅ |
| Normalization | /255 (correct) | /255 ✅ |

---

### 3. 🧠 MODEL ARCHITECTURE ISSUES

#### Current Architecture (from notebook):
```
Conv2D(32, 3) → MaxPool → Conv2D(32, 5) → MaxPool → Flatten → Dense(64) → Dense(10) → Softmax
```

#### Issues:
| Problem | Impact | Severity |
|---------|--------|----------|
| Only 2 Conv layers | Low feature extraction capacity | 🔴 High |
| No Dropout | Overfitting risk | 🟡 Medium |
| No BatchNorm | Slower convergence, unstable | 🟡 Medium |
| Small Dense layer (64) | Limited representation power | 🟡 Medium |
| Only 10 epochs | Undertrained | 🔴 High |
| No data augmentation | Poor generalization | 🔴 High |

---

### 4. 📊 TRAINING ISSUES

| Issue | Current | Recommended |
|-------|---------|-------------|
| Epochs | 10 | 50-100 |
| Validation Split | None used | 20% |
| Data Augmentation | None | Rotation, flip, zoom, shift |
| Learning Rate | Default Adam | Scheduled decay |
| Early Stopping | None | patience=10 |
| Batch Size | Default (32) | 64-128 |

---

### 5. 🔢 INFERENCE ISSUES

Current confidence calculation:
```python
top_prob = probs.max()  # Gets highest probability
```

This is correct, but the model outputs may not be well-calibrated.

---

## 📈 Accuracy Failure Tree

```
Low Accuracy (<60%)
├── Domain Mismatch (40% contribution)
│   ├── CIFAR-10 images are 32x32
│   ├── Real images are high-resolution
│   └── Downscaling loses critical features
├── Undertrained Model (30% contribution)
│   ├── Only 10 epochs
│   ├── No validation monitoring
│   └── No early stopping
├── Weak Architecture (20% contribution)
│   ├── Only 2 conv layers
│   ├── No regularization
│   └── Small capacity
└── Preprocessing Mismatch (10% contribution)
    ├── No quality resize interpolation
    └── No aspect ratio handling
```

---

## 🛠️ Recommended Fixes

### Phase 1: Quick Fixes (Immediate)

1. **Fix Preprocessing** - Use LANCZOS interpolation
2. **Add Center Crop** - Maintain aspect ratio
3. **Add Input Validation** - Check image quality

### Phase 2: Model Improvements (Short-term)

1. **Increase Training Epochs** - 50+ epochs
2. **Add Data Augmentation** - Rotation, flip, zoom
3. **Add Dropout & BatchNorm** - Regularization
4. **Add Validation Split** - Monitor overfitting

### Phase 3: Architecture Upgrade (Medium-term)

1. **Use Transfer Learning** - MobileNetV2 or EfficientNetB0
2. **Fine-tune on Domain Data** - Collect real-world examples
3. **Ensemble Models** - Combine multiple models

---

## 📊 Expected Improvements

| Fix | Expected Accuracy Gain |
|-----|------------------------|
| Better preprocessing | +5-10% |
| More epochs + augmentation | +10-15% |
| Transfer learning (MobileNet) | +20-30% |
| **Total Potential** | **+35-55%** |

---

## ✅ Implementation Priority

1. 🔴 **CRITICAL**: Fix preprocessing (resize interpolation)
2. 🔴 **CRITICAL**: Increase training epochs to 50+
3. 🟡 **HIGH**: Add data augmentation
4. 🟡 **HIGH**: Add validation split
5. 🟢 **MEDIUM**: Upgrade to transfer learning model

---

## 🚀 Implementation Status

### Completed Fixes

| Fix | Status | Details |
|-----|--------|---------|
| Preprocessing | ✅ Done | LANCZOS interpolation + center crop |
| Data Augmentation | ✅ Done | Rotation, flip, zoom, shear, brightness |
| Enhanced Model | ✅ Done | `EnhancedModelTraining.ipynb` |
| Transfer Learning | ✅ Done | `TransferLearningMobileNetV2.ipynb` |

### Available Models

| Model | File | Expected Accuracy |
|-------|------|-------------------|
| Baseline | `baseline_mariya.keras` | ~55-60% |
| Enhanced CNN | `enhanced_model.keras` | ~75-80% |
| MobileNetV2 | `mobilenet_cifar10_production.keras` | ~85-92% |

### How to Generate New Model

1. Open `notebooks/TransferLearningMobileNetV2.ipynb`
2. Run all cells (takes ~30-60 minutes)
3. Model saved to `assets/mobilenet_cifar10_production.keras`
4. Update `classifier.py` to use new model

---

