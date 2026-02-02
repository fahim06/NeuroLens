# 🧱 NeuroLens — Django Rebuild Phase 0: Reset & Foundation

This canvas defines **Phase 0** of the Django rebuild. It is written as a **direct execution plan for AI agents** and mirrors how a real software company resets a project safely.

---

## 🎯 Phase 0 Purpose

Phase 0 does **NOT** build features.
It establishes a **clean, stable, reviewable foundation** for the Django + DRF rebuild.

Outcomes:
- new rebuild branch
- clean repo baseline
- environments defined
- Django project scaffolded
- governance rules enforced

---

## 🔒 GLOBAL RULES (NON-NEGOTIABLE)

- ❌ Do NOT touch `main`
- ❌ Do NOT merge into `dev`
- ❌ Do NOT add ML code
- ❌ Do NOT add frontend
- ✅ Work ONLY in `django-rebuild`
- ✅ Keep Phase 0 minimal and boring

---

## 🌳 Branch Setup

### Step 0.1 — Create Rebuild Branch

```bash
git checkout dev
git pull origin dev
git checkout -b django-rebuild
```

Purpose:
- preserve beta branch
- isolate rebuild work

---

## 📁 Repository State (Pre-Confirmed)

Only these files/folders exist:
```
.git
.github
.gitignore
.idea
.vscode
assets
demo_images
LICENSE
README.md
SECURITY.md
```

✅ This is correct and intentional.

---

## 🧪 Environment Strategy (Conda)

### Environments to Define (Phase 0 only)

| Env Name | Purpose |
|-------|--------|
| neurolens-django | Django + DRF runtime |
| neurolens-dev | tooling, lint, CI |

⚠️ ML environment will be added in a later phase.

---

## ⚙️ Step 0.2 — Create Conda Environment Files

Create folder:
```bash
mkdir envs
```

### `envs/neurolens-django.yml`
```yaml
name: neurolens-django
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - pip
  - django
  - djangorestframework
  - python-dotenv
  - psycopg2
  - gunicorn
```

### `envs/neurolens-dev.yml`
```yaml
name: neurolens-dev
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - pip
  - black
  - ruff
  - mypy
  - pytest
  - pre-commit
```

---

## ⚙️ Step 0.3 — Create Environments

```bash
conda env create -f envs/neurolens-django.yml
conda env create -f envs/neurolens-dev.yml
```

Verify:
```bash
conda env list
```

---

## 🏗️ Step 0.4 — Django Project Scaffold

Activate Django env:
```bash
conda activate neurolens-django
```

Create project:
```bash
django-admin startproject neurolens .
```

Resulting structure:
```
neurolens/
├── neurolens/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── manage.py
```

⚠️ Do NOT create apps yet.

---

## ⚙️ Step 0.5 — Basic Settings Hardening

Agent must:
- enable `INSTALLED_APPS`:
  - rest_framework
- set `TIME_ZONE`
- set `DEFAULT_AUTO_FIELD`
- ensure project runs with SQLite

❌ No custom settings modules yet.

---

## 🧪 Step 0.6 — Smoke Test

```bash
python manage.py runserver
```

Open browser:
```
http://127.0.0.1:8000/
```

Expected:
- Django welcome page
- No warnings
- No errors

---

## 📦 Step 0.7 — .gitignore Review

Ensure `.gitignore` includes:
- `__pycache__/`
- `.env`
- `*.sqlite3`
- `.idea/`
- `.vscode/`

---

## 📝 Step 0.8 — README Status Update

Append to README:

```
## Project Status

Django REST rebuild in progress.
Current phase: Phase 0 — Foundation
```

---

## 📌 Step 0.9 — Commit Phase 0

```bash
git status
git add .
git commit -m "Phase 0: Django rebuild foundation"
```

---

## ✅ Phase 0 Completion Criteria

- `django-rebuild` branch exists
- Conda envs created
- Django project runs
- No apps yet
- No ML code
- No frontend code
- Clean commit

---

## 🚦 What Happens Next

Phase 1 will:
- define Django settings layout
- create core apps (`users`, `core`)
- configure DRF properly
- add health check API

---

## ▶️ Next Instruction (Awaiting User)

Reply with **ONE**:

1️⃣ "Start Django Rebuild — Phase 1"  
2️⃣ "Review Phase 0 before continuing"  
3️⃣ "Explain DRF request lifecycle again"

---

> **Reminder:**
> Phase 0 is about **discipline**, not speed.

