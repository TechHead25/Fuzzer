import os
from pathlib import Path
import config

class SecurityViolation(Exception):
    pass

def resolve_and_validate_path(path_str: str, allowed_roots: list[Path]) -> Path:
    """
    Resolves a path to absolute and ensures it falls strictly within one of the allowed roots.
    Prevents path traversal attacks (e.g. ../../Windows/System32).
    """
    try:
        target = Path(path_str).resolve(strict=False)
    except Exception as e:
        raise SecurityViolation(f"Invalid path format: {e}")

    for root in allowed_roots:
        try:
            # If target is relative to root, it's inside.
            target.relative_to(root.resolve(strict=False))
            return target
        except ValueError:
            continue
            
    raise SecurityViolation(f"Path traversal blocked. Path {target} is outside authorized directories.")

def validate_executable(exe_path: str) -> Path:
    """Ensure executable is in an authorized bin directory."""
    # Enforce .exe or .bat
    if not exe_path.lower().endswith(('.exe', '.bat')):
        raise SecurityViolation(f"Executable {exe_path} must be .exe or .bat")
        
    return resolve_and_validate_path(exe_path, config.AUTHORIZED_EXEC_DIRS)

def validate_workspace_path(file_path: str) -> Path:
    """Ensure a working directory or input file is in the secure workspace."""
    return resolve_and_validate_path(file_path, [config.WORKSPACE_DIR])

def sanitize_environment(custom_env: dict = None) -> dict:
    """
    Creates a pristine environment for subprocesses.
    Removes potentially dangerous hooks (like DLL injection vars, PYTHONPATH)
    unless explicitly allowed.
    """
    safe_env = {}
    allowed_keys = {
        'PATH', 'SYSTEMROOT', 'USERPROFILE', 'COMSPEC', 'TEMP', 'TMP',
        'WINDIR', 'APPDATA', 'LOCALAPPDATA', 'PROGRAMFILES', 'PROGRAMFILES(X86)'
    }
    
    for k, v in os.environ.items():
        if k.upper() in allowed_keys:
            safe_env[k] = v
            
    if custom_env:
        for k, v in custom_env.items():
            # Block obviously malicious injection envs just in case
            if k.upper() not in ('LD_PRELOAD', 'PYTHONPATH'):
                safe_env[k] = str(v)
                
    return safe_env
