import requests
import config
from typing import Dict, Any, Optional

class FuzzAPIClient:
    def __init__(self):
        self.base_url = config.API_URL
        self.headers = {
            "Authorization": f"Bearer {config.API_KEY}",
            "Content-Type": "application/json"
        }
        self.worker_id = None

    def register(self, diagnostics: Dict[str, Any]) -> int:
        payload = {
            "hostname": config.WORKER_HOSTNAME,
            "ip_address": config.WORKER_IP,
            "capabilities": diagnostics
        }
        res = requests.post(f"{self.base_url}/api/v1/workers/register", json=payload, headers=self.headers)
        res.raise_for_status()
        data = res.json()
        self.worker_id = data["id"]
        return self.worker_id

    def heartbeat(self, status: str) -> None:
        if not self.worker_id:
            return
        res = requests.post(
            f"{self.base_url}/api/v1/workers/{self.worker_id}/heartbeat",
            json={"status": status},
            headers=self.headers,
            timeout=5
        )
        res.raise_for_status()

    def get_job(self) -> Optional[Dict[str, Any]]:
        res = requests.get(
            f"{self.base_url}/api/v1/workers/{self.worker_id}/jobs/next",
            headers=self.headers,
            timeout=10
        )
        if res.status_code == 204:
            return None
        res.raise_for_status()
        return res.json()

    def stream_logs(self, job_id: int, log_line: str) -> None:
        try:
            requests.post(
                f"{self.base_url}/api/v1/workers/jobs/{job_id}/logs",
                json={"log": log_line},
                headers=self.headers,
                timeout=3
            )
        except Exception:
            pass # Fail open on log streaming

    def update_job_status(self, job_id: int, status: str, result_payload: dict = None) -> None:
        payload = {"status": status, "results": result_payload or {}}
        res = requests.patch(
            f"{self.base_url}/api/v1/workers/jobs/{job_id}",
            json=payload,
            headers=self.headers
        )
        res.raise_for_status()

    def upload_artifact(self, job_id: int, file_path: str, artifact_type: str = "crash") -> None:
        with open(file_path, "rb") as f:
            files = {"file": f}
            data = {"type": artifact_type}
            requests.post(
                f"{self.base_url}/api/v1/workers/jobs/{job_id}/artifacts",
                headers={"Authorization": f"Bearer {config.API_KEY}"},
                files=files,
                data=data
            )

    def push_job_metrics(self, job_id: int, metrics: Dict[str, Any]) -> None:
        try:
            requests.post(
                f"{self.base_url}/api/v1/workers/jobs/{job_id}/metrics",
                json=metrics,
                headers=self.headers,
                timeout=3
            )
        except Exception:
            pass # Fail open on metric streaming
