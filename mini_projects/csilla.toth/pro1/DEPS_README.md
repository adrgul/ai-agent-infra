This folder includes helper scripts to install Python dependencies required by the `app`.

- `requirements.txt` — pins runtime dependencies. (Contains `openai`, `python-dotenv`, `chromadb`.)
- `install_deps.ps1` — PowerShell script: creates a venv and installs requirements.
- `install_deps.sh` — POSIX shell script: creates a venv and installs requirements.

Quick start (PowerShell):
```powershell
cd path\to\mini_projects\csilla.toth\pro1
.\install_deps.ps1
```

Quick start (bash):
```bash
cd path/to/mini_projects/csilla.toth/pro1
./install_deps.sh
```

Notes:
- Ensure `python` on PATH points to Python 3.8+.
- Set `OPENAI_API_KEY` in environment or create a `.env` file before running the app.

Permission fixes:
- If you encounter permission-denied errors when running or importing files from `app`, run the platform script below from this folder.

PowerShell (Windows):
```powershell
.\fix_app_permissions.ps1
# or pass a different directory:
.\fix_app_permissions.ps1 -AppDir other_folder
```

POSIX (WSL/macOS/Linux):
```bash
./fix_app_permissions.sh
# or pass a different directory:
./fix_app_permissions.sh other_folder
```

Health-check key utility:
- `check_key.py` verifies that `.env` is loaded and that the `openai` package imports correctly. It can also perform an optional API probe.

Run (from `pro1`):
```powershell
python check_key.py           # checks .env and import
python check_key.py --api     # performs a lightweight API models.list() call
python check_key.py --show    # print masked key
```

The `--api` flag will make a real call and may consume quota; omit it to only validate environment and imports.
