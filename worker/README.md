# Fuzz-Sentinel Windows Worker

The Windows Fuzz Worker is a standalone agent deployed on target fuzzing machines. It securely receives jobs from the Fuzz-Sentinel backend, executes WinAFL instances, and streams coverage/crash artifacts back in real-time.

## Prerequisites

The worker *must* be run on Windows.
- Python 3.10+
- WinAFL (and DynamoRIO)

## Directory Structure
By default, the worker creates a secure sandbox at `C:\FuzzWorker`.

## Setup Instructions

1. Install Python requirements:
   ```cmd
   pip install -r requirements.txt
   ```

2. Download and extract WinAFL to `C:\FuzzWorker\bin\winafl`
3. Download and extract DynamoRIO to `C:\FuzzWorker\bin\dynamorio`

4. Set your API configuration:
   ```cmd
   set FUZZ_API_URL=http://<backend-ip>:8000
   set FUZZ_API_KEY=your-secure-key
   ```

5. Run the worker:
   ```cmd
   python main.py
   ```

## Security Guarantees
- **No Path Traversal**: Workspace execution directories are explicitly validated to sit inside the `C:\FuzzWorker\workspace` sandbox.
- **Process Injection Protection**: `subprocess.Popen` is strictly enforced with `shell=False`.
- **Environment Sanitation**: Dangerous variables (like `PYTHONPATH`) are stripped before WinAFL is launched.
