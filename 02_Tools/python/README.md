# Python usage

Use a project-local virtual environment; do not install arbitrary packages globally.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

This bootstrap does not install project dependencies or secrets.
