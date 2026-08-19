import subprocess
import threading
import time
import logging
from typing import List, Callable
import security
from mock_coverage import MockWorker

logger = logging.getLogger(__name__)

class ProcessExecutor:
    """
    Safely executes a WinAFL process, capturing stdout/stderr non-blockingly
    and handling strict timeouts and termination.
    """
    def __init__(self, executable: str, args: List[str], cwd: str, env: dict = None, mock_mode: bool = False):
        # Security boundaries applied here
        self.executable = security.validate_executable(executable)
        self.cwd = security.validate_workspace_path(cwd)
        self.env = security.sanitize_environment(env)
        
        # WinAFL relies on string arguments rather than a single list sometimes due to DR,
        # but subprocess list is safer to prevent cmd injection.
        # We explicitly enforce shell=False.
        self.cmd = [str(self.executable)] + [str(a) for a in args]
        
        self.process = None
        self.stdout_lines = []
        self.stderr_lines = []
        self.is_running = False
        self.mock_mode = mock_mode
        self.mock_cov = None
        
        self._stdout_thread = None
        self._stderr_thread = None

    def _reader_thread(self, stream, target_list: list, on_line_cb: Callable = None):
        for line in iter(stream.readline, b''):
            try:
                decoded = line.decode('utf-8', errors='replace').rstrip()
                target_list.append(decoded)
                if on_line_cb:
                    on_line_cb(decoded)
            except Exception:
                pass
        stream.close()

    def start(self, on_stdout: Callable = None, on_stderr: Callable = None):
        logger.info(f"Starting secure process: {self.executable} in {self.cwd}")
        try:
            if self.mock_mode:
                self.mock_cov = MockWorker()
                self.mock_cov.start()

            self.process = subprocess.Popen(
                self.cmd,
                cwd=str(self.cwd),
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False, # CRITICAL: No command injection
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP # Windows: allows CTRL_BREAK_EVENT
            )
            self.is_running = True
            
            self._stdout_thread = threading.Thread(
                target=self._reader_thread, 
                args=(self.process.stdout, self.stdout_lines, on_stdout)
            )
            self._stderr_thread = threading.Thread(
                target=self._reader_thread, 
                args=(self.process.stderr, self.stderr_lines, on_stderr)
            )
            self._stdout_thread.daemon = True
            self._stderr_thread.daemon = True
            self._stdout_thread.start()
            self._stderr_thread.start()
            
            return True
        except Exception as e:
            logger.error(f"Failed to start process: {e}")
            self.stderr_lines.append(f"Execution Error: {e}")
            return False

    def wait(self, timeout: int = None) -> int:
        if not self.process:
            return -1
            
        try:
            exit_code = self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"Process timed out after {timeout}s. Terminating.")
            self.terminate()
            exit_code = self.process.wait()
            
        self.is_running = False
        self._stdout_thread.join(timeout=1.0)
        self._stderr_thread.join(timeout=1.0)
        return exit_code

    def terminate(self):
        if self.process and self.process.poll() is None:
            # On Windows, try to send CTRL_BREAK to gracefully stop WinAFL
            try:
                if self.mock_mode and self.mock_cov:
                    self.mock_cov.stop()
                self.process.send_signal(subprocess.signal.CTRL_BREAK_EVENT)
                time.sleep(2)
                if self.process.poll() is None:
                    self.process.terminate()
            except Exception:
                self.process.kill()
