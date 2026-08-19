from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class FuzzEngine(ABC):
    """
    Abstract base class for all Fuzz-Sentinel fuzzing engines.
    Ensures that engines like WinAFL, FutureAFL, etc., conform to a common interface.
    """

    @abstractmethod
    def start_campaign(self, campaign_config: Dict[str, Any]) -> str:
        """Start a fuzzing campaign and return a job/process ID."""
        pass

    @abstractmethod
    def stop_campaign(self, job_id: str) -> bool:
        """Stop a running fuzzing campaign."""
        pass

    @abstractmethod
    def get_metrics(self, job_id: str) -> Dict[str, Any]:
        """Retrieve current metrics for the campaign (executions, coverage)."""
        pass

    @abstractmethod
    def get_status(self, job_id: str) -> str:
        """Check if the fuzzer is running, crashed, or stopped."""
        pass
