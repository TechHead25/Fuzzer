import threading
import time
import requests
import sys

class MockWorker:
    """Simulates a worker sending coverage snapshots and metrics."""
    def __init__(self, api_url, project_id, campaign_id, target_id):
        self.api_url = api_url
        self.project_id = project_id
        self.campaign_id = campaign_id
        self.target_id = target_id
        self.paths = 100
        self.blocks = 450
        self.running = True
        
    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
    def _run(self):
        while self.running:
            try:
                # Push fake coverage snapshot
                self.paths += 5
                self.blocks += 12
                
                requests.post(f"{self.api_url}/api/v1/projects/{self.project_id}/coverage/", json={
                    "campaign_id": self.campaign_id,
                    "target_id": self.target_id,
                    "coverage_metric": "block",
                    "unique_paths": self.paths,
                    "blocks": self.blocks,
                    "edges": self.blocks * 2,
                    "artifact_reference": f"mock_corpus/seed_{self.paths}.bin"
                })
                
                # Push mock crash every 3 cycles
                if self.paths % 15 == 0:
                    requests.post(f"{self.api_url}/api/v1/projects/{self.project_id}/crashes/", json={
                        "campaign_id": self.campaign_id,
                        "worker_id": 1,
                        "input_artifact": f"crashes/crash_{self.paths}.bin",
                        "exception_type": "EXCEPTION_ACCESS_VIOLATION",
                        "fault_address": "0x00007FF7B0A21A10",
                        "module": "SumatraPDF.exe",
                        "stack_trace": "0x00007FF7B0A21A10 SumatraPDF.exe!ParseChunk\n0x00007FF7B0A21B20 SumatraPDF.exe!LoadDocument\n0x00007FF7B0A21C30 SumatraPDF.exe!Main",
                        "severity": "High",
                        "vulnerability_class": "Out-of-bounds Read"
                    })
            except Exception as e:
                print(f"Mock coverage push failed: {e}", file=sys.stderr)
            time.sleep(10)
            
    def stop(self):
        self.running = False
