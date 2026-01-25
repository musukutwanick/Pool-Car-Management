Pool Car Management — Setup Guide

This workspace will host the Pool Car Management System (Django + Tailwind).

Prerequisites
- Python 3.10+ installed and on PATH
- Node.js + npm (required for Tailwind via `django-tailwind`)
- (Optional) Git

Quick Windows (PowerShell) setup

1) Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install Python dependencies
```powershell
pip install --upgrade pip
pip install -r "requirements.txt"
```

3) Start a new Django project (example name `poolcar`) and app
```powershell
# from workspace root
django-admin startproject poolcar .
python manage.py startapp fleet
```

4) Add `tailwind` integration (django-tailwind)
- Add `'tailwind'` and a theme app (e.g., `theme`) to `INSTALLED_APPS` in `poolcar/settings.py`.
- Create a Tailwind theme app:
```powershell
python manage.py tailwind init theme
```
- From the theme directory, install Tailwind dependencies (this uses npm):
```powershell
# from project root
python manage.py tailwind install
```
- During development run:
```powershell
python manage.py tailwind start
```
This runs the Tailwind watcher and builds CSS.

Notes and next steps
- If PowerShell blocks script execution, you may need to set execution policy (run as Administrator):
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
- I'll scaffold the Django project and integrate Tailwind if you want me to run the commands here. Otherwise, run the steps above locally.
- Send the brand manual (colors/fonts) and I'll add a Tailwind theme configuration and sample components matching your brand.

I added initial project scaffolding (Django `poolcar` project, `fleet` app, and `theme` Tailwind app skeleton).

Quick dev helper (PowerShell)

Run the helper script from the workspace root to apply migrations and see Tailwind instructions:
```powershell
.\dev_setup.ps1
```

Tailwind notes:
- Ensure `Node.js` and `npm` are installed.
- From the project root, run:
```powershell
# install theme node deps
python manage.py tailwind install
# build once
python manage.py tailwind build
# or for development watcher
python manage.py tailwind start
```

Next steps I can take for you:
- Implement approval routing logic and add role-based permissions.
- Create API endpoints and frontend pages for submitting and approving requests.
- Add automated tests and CI scripts.
