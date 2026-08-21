"""
Fuzz-Sentinel Worker Configuration
"""

import os
from pathlib import Path

# API Configuration
API_URL = os.environ.get("FUZZ_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("FUZZ_API_KEY", "fuzz-sentinel-dev-key")

# Worker Identity
WORKER_HOSTNAME = os.environ.get("COMPUTERNAME", "Unknown-PC")
WORKER_IP = "127.0.0.1" # In a real deployment, resolve host IP

# Paths & Workspace
WORKER_ROOT = Path(os.environ.get("FUZZ_WORKER_ROOT", "./fuzz_worker_root")).resolve()
WORKSPACE_DIR = WORKER_ROOT / "workspace"
ARTIFACTS_DIR = WORKER_ROOT / "artifacts"
BIN_DIR = WORKER_ROOT / "bin"

# Explicit tools (Check environment, project root, then local bin fallback)
_REPO_ROOT = Path(__file__).resolve().parent.parent

_winafl_env = os.environ.get("WINAFL_DIR")
if _winafl_env:
    WINAFL_DIR = Path(_winafl_env).resolve()
elif (_REPO_ROOT / "winafl" / "build64" / "bin" / "afl-fuzz.exe").exists():
    WINAFL_DIR = (_REPO_ROOT / "winafl" / "build64" / "bin").resolve()
elif (_REPO_ROOT / "winafl" / "bin64" / "afl-fuzz.exe").exists():
    WINAFL_DIR = (_REPO_ROOT / "winafl" / "bin64").resolve()
else:
    WINAFL_DIR = BIN_DIR / "winafl"

_dynamorio_env = os.environ.get("DYNAMORIO_DIR")
if _dynamorio_env:
    DYNAMORIO_DIR = Path(_dynamorio_env).resolve()
elif (_REPO_ROOT / "dynamorio" / "bin64" / "drrun.exe").exists():
    DYNAMORIO_DIR = (_REPO_ROOT / "dynamorio").resolve()
else:
    DYNAMORIO_DIR = BIN_DIR / "dynamorio"

# Security Allowlists
AUTHORIZED_EXEC_DIRS = [
    BIN_DIR,
    WINAFL_DIR,
    DYNAMORIO_DIR,
    _REPO_ROOT,
    Path("C:\\Program Files"),
    Path("C:\\Windows\\System32")
]

def ensure_directories():
    """Create necessary safe directories."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
