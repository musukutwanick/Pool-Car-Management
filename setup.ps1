# Setup script for Windows PowerShell
# Usage: Right-click -> Run with PowerShell, or run from an elevated PowerShell if needed.

# Create virtual environment
python -m venv .venv

# Activate venv in the current session
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    . .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment activation script not found. Be sure Python created .venv folder."
}

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r "requirements.txt"

Write-Host "Requirements installed. Next steps: run 'django-admin startproject poolcar .' and follow README.md for Tailwind setup."