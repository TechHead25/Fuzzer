import time
import logging
import sys
import argparse
import config
import diagnostics
from client import FuzzAPIClient
from executor import ProcessExecutor
from winafl_parser import WinAFLParser
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Track last metric push time to avoid spamming the API
last_metric_push = 0
METRIC_PUSH_INTERVAL = 5.0 # seconds

def main():
    parser = argparse.ArgumentParser(description="Fuzz-Sentinel Windows Worker")
    parser.add_argument("--mock-worker", action="store_true", help="Bypass strict OS and binary dependency checks for testing.")
    args = parser.parse_args()

    config.ensure_directories()
    
    logger.info("Initializing Windows Fuzz Worker...")
    diag = diagnostics.get_diagnostics()
    
    if args.mock_worker:
        logger.info("[MOCK MODE] Bypassing OS and dependency checks.")
        diag["status"] = "OK"
        diag["issues"] = []
        diag["winafl_path"] = str(config.WINAFL_DIR)
        diag["dynamorio_path"] = str(config.DYNAMORIO_DIR)
        
    if diag["status"] == "ERROR":
        logger.error(f"Diagnostics failed. Issues: {diag['issues']}")
        logger.error("Please resolve setup requirements and restart, or use --mock-worker for UI testing.")
        sys.exit(1)
        
    client = FuzzAPIClient()
    try:
        worker_id = client.register(diag)
        logger.info(f"Registered with backend successfully. Worker ID: {worker_id}")
    except Exception as e:
        logger.error(f"Failed to register with API at {config.API_URL}: {e}")
        sys.exit(1)
        
    state = "ONLINE"
    
    while True:
        try:
            client.heartbeat(state)
            
            if state == "ONLINE":
                job = client.get_job()
                if job:
                    logger.info(f"Received job {job['id']}. Preparing execution...")
                    state = "BUSY"
                    execute_job(client, job, is_mock=args.mock_worker)
                    state = "ONLINE"
            
            time.sleep(5) # Poll interval
        except KeyboardInterrupt:
            logger.info("Worker shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            time.sleep(5)

def execute_job(client: FuzzAPIClient, job: dict, is_mock: bool = False):
    global last_metric_push
    job_id = job["id"]
    client.update_job_status(job_id, "RUNNING")
    
    exe_path = job.get("executable", "harness.exe")
    timeout = job.get("timeout", 3600)
    job_args = job.get("args", [])
    
    # In a real environment, WinAFL command construction:
    # afl-fuzz.exe -i corpus -o out -D dynamorio\bin32 -t timeout -- harness.exe @@
    if not is_mock:
        # Resolve real paths
        afl_bin = str(config.WINAFL_DIR / "afl-fuzz.exe")
        winafl_args = job_args
    else:
        # For mock execution, we execute a python script that prints mock WinAFL strings
        afl_bin = sys.executable
        mock_script = f"""
import sys, time
print('WinAFL Mock Engine Started')
print('[*] execs: 0, execs/s: 0.0, paths: 1, crashes: 0, hangs: 0')
for i in range(1, 15):
    time.sleep(1)
    print(f'[*] execs: {{i*100}}, execs/s: 100.5, paths: {{i+1}}, crashes: {{0 if i<10 else 1}}, hangs: 0')
print('Fuzzing complete.')
        """
        script_path = str(config.WORKSPACE_DIR / "mock_winafl.py")
        with open(script_path, "w") as f:
            f.write(mock_script)
        winafl_args = [script_path]
        
    cwd = config.WORKSPACE_DIR
    
    def on_metrics_update(metrics: dict):
        global last_metric_push
        now = time.time()
        if now - last_metric_push > METRIC_PUSH_INTERVAL:
            client.push_job_metrics(job_id, metrics)
            last_metric_push = now
            
    parser = WinAFLParser(on_metrics_update=on_metrics_update)

    def log_stdout(line):
        client.stream_logs(job_id, line)
        parser.process_line(line)
        
    def log_stderr(line):
        client.stream_logs(job_id, line)
        
    try:
        executor = ProcessExecutor(afl_bin, winafl_args, str(cwd), mock_mode=args.mock_worker)
        success = executor.start(on_stdout=log_stdout, on_stderr=log_stderr)
        
        if success:
            exit_code = executor.wait(timeout=timeout)
            logger.info(f"Job {job_id} completed with exit code {exit_code}")
            client.update_job_status(job_id, "COMPLETED", {"exit_code": exit_code})
            # Final metric push to capture ending state
            client.push_job_metrics(job_id, parser.latest_metrics)
        else:
            client.update_job_status(job_id, "FAILED", {"error": "Failed to start executor"})
            
    except Exception as e:
        logger.error(f"Job execution error: {e}")
        client.update_job_status(job_id, "ERROR", {"error": str(e)})

if __name__ == "__main__":
    main()
