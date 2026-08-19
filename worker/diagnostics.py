import platform
import psutil
import shutil
from pathlib import Path
import config

def get_diagnostics():
    """Run worker diagnostics and report system capability."""
    
    # 1. OS Check
    is_windows = platform.system() == "Windows"
    os_version = platform.release()
    
    # 2. Hardware Checks
    mem = psutil.virtual_memory()
    total_mem_gb = mem.total / (1024**3)
    available_mem_gb = mem.available / (1024**3)
    
    disk_usage = shutil.disk_usage(config.WORKER_ROOT.anchor)
    free_disk_gb = disk_usage.free / (1024**3)
    
    # 3. Toolchain Checks
    has_winafl = (config.WINAFL_DIR / "afl-fuzz.exe").exists()
    has_dynamorio = (config.DYNAMORIO_DIR / "bin32" / "drrun.exe").exists() or (config.DYNAMORIO_DIR / "bin64" / "drrun.exe").exists()
    
    status = "OK"
    issues = []
    
    if not is_windows:
        status = "ERROR"
        issues.append("NON_WINDOWS_OS")
        
    if not has_winafl:
        status = "ERROR"
        issues.append("WIN_AFL_NOT_INSTALLED")
        
    if not has_dynamorio:
        status = "ERROR"
        issues.append("INSTRUMENTATION_NOT_INSTALLED")
        
    if free_disk_gb < 5:
        issues.append("LOW_DISK_SPACE")
        
    return {
        "status": status,
        "issues": issues,
        "os": f"Windows {os_version}",
        "memory_total_gb": round(total_mem_gb, 2),
        "memory_available_gb": round(available_mem_gb, 2),
        "disk_free_gb": round(free_disk_gb, 2),
        "winafl_path": str(config.WINAFL_DIR) if has_winafl else None,
        "dynamorio_path": str(config.DYNAMORIO_DIR) if has_dynamorio else None,
    }
