import re
from typing import Dict, Any, Callable

# AFL_NO_UI=1 output often looks like:
# [*] execs: 1234, execs/s: 12.3, paths: 45, crashes: 1, hangs: 0
# However, for robustness, we'll also support standard fuzzer_stats parsing if needed,
# but this regex targets typical non-UI log output.

METRIC_PATTERN = re.compile(
    r"(?:execs:\s*(?P<execs>\d+)).*(?:execs/s:\s*(?P<execs_per_sec>[\d\.]+)).*(?:paths:\s*(?P<paths>\d+)).*(?:crashes:\s*(?P<crashes>\d+)).*(?:hangs:\s*(?P<hangs>\d+))",
    re.IGNORECASE
)

class WinAFLParser:
    def __init__(self, on_metrics_update: Callable[[Dict[str, Any]], None] = None):
        self.on_metrics_update = on_metrics_update
        self.latest_metrics = {
            "executions": 0,
            "execs_per_second": 0.0,
            "unique_paths": 0,
            "crashes": 0,
            "hangs": 0
        }

    def process_line(self, line: str):
        """
        Parses a line of WinAFL stdout.
        If metrics are found, updates internal state and fires callback.
        """
        match = METRIC_PATTERN.search(line)
        if match:
            self.latest_metrics["executions"] = int(match.group("execs"))
            self.latest_metrics["execs_per_second"] = float(match.group("execs_per_sec"))
            self.latest_metrics["unique_paths"] = int(match.group("paths"))
            self.latest_metrics["crashes"] = int(match.group("crashes"))
            self.latest_metrics["hangs"] = int(match.group("hangs"))
            
            if self.on_metrics_update:
                self.on_metrics_update(self.latest_metrics)
                
        # Also catch DynamoRIO instrumentation errors
        if "DynamoRIO usage error" in line or "DR ERROR" in line:
            # We could trigger an error callback here, but for MVP we rely on the line being sent to logs
            pass
