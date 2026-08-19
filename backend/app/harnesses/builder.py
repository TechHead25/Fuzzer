"""
Harness Builder Engine

Simulates local validation and compilation of the generated harness.
"""

import subprocess
import hashlib
import tempfile
import os
from typing import Dict, Any, Tuple

def build_harness(files: Dict[str, str]) -> Tuple[bool, Dict[str, Any]]:
    """
    Simulates writing the harness to disk, invoking the build script,
    and validating it. Returns (success, result_dict).
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write files
        for filename, content in files.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "w") as f:
                f.write(content)
                
        # To avoid arbitrary un-sandboxed execution on the host machine during MVP,
        # we will do a dry-run/mock build unless instructed otherwise.
        # However, we will capture 'compiler' info from the host if possible.
        
        compiler_version = "Unknown"
        compiler = "MSVC/Clang"
        try:
            # Just test if clang++ is available
            res = subprocess.run(["clang++", "--version"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                compiler = "clang++"
                compiler_version = res.stdout.splitlines()[0]
        except Exception:
            pass

        # Simulate execution of build.bat
        stdout = f"Attempting to build harness in {tmpdir}...\n"
        stdout += "Compiler: " + compiler_version + "\n"
        stdout += "Mock build successful.\n"
        
        stderr = ""
        success = True
        
        # Simulate binary hash
        binary_hash = hashlib.sha256(b"mock_binary_data").hexdigest()
        binary_path = os.path.join(tmpdir, "harness.exe")
        
        return success, {
            "compiler": compiler,
            "compiler_version": compiler_version,
            "architecture": "x86_64",
            "build_command": "build.bat",
            "stdout": stdout,
            "stderr": stderr,
            "binary_path": binary_path,
            "hash": binary_hash
        }
