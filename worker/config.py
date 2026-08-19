"""
Fuzz-Sentinel Worker Configuration
"""

import os
from pathlib import Path

# API Configuration
API_URL = os.environ.get("FUZZ_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("FUZZ_API_KEY")
if not API_KEY:
    raise ValueError("CRITICAL: FUZZ_API_KEY environment variable is required.")

# Worker Identity
WORKER_HOSTNAME = os.environ.get("COMPUTERNAME", "Unknown-PC")
WORKER_IP = "127.0.0.1" # In a real deployment, resolve host IP

# Paths & Workspace
WORKER_ROOT = Path(os.environ.get("FUZZ_WORKER_ROOT", "./fuzz_worker_root")).resolve()
WORKSPACE_DIR = WORKER_ROOT / "workspace"
ARTIFACTS_DIR = WORKER_ROOT / "artifacts"
BIN_DIR = WORKER_ROOT / "bin"

# Security Allowlists
# Only executables in these paths can be run
AUTHORIZED_EXEC_DIRS = [
    BIN_DIR,
    Path("C:\\Program Files"),
    Path("C:\\Windows\\System32")
]

# Explicit tools
WINAFL_DIR = BIN_DIR / "winafl"
DYNAMORIO_DIR = BIN_DIR / "dynamorio"

def ensure_directories():
    """Create necessary safe directories."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    BIN_DIR.mkdir(parents=True, exist_ok=True)
