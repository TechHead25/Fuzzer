import time
from typing import Dict, Any

class AIProvider:
    def analyze_crash(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

class MockLocalProvider(AIProvider):
    """
    Simulates a local LLM returning structured JSON.
    Never sends data externally.
    """
    def __init__(self):
        self.model_name = "mock-local-llama3-8b"
        self.model_version = "v1.0"
        self.prompt_version = "p-2026-08-16"
        
    def analyze_crash(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate local LLM inference time
        time.sleep(2)
        
        module = context.get("module", "unknown")
        exc_type = context.get("exception_type", "unknown")
        
        # Hardcoded mock response following the exact requested structure
        return {
            "vulnerability_class": "Out-of-bounds Read (CWE-125)",
            "severity": "High",
            "root_cause_hypothesis": f"The crash is caused by an {exc_type} in {module}. The parser likely attempts to read beyond the bounds of an allocated buffer when processing a malformed length field in the input artifact.",
            "affected_component": f"{module} - Chunk Parser",
            "relevant_code": "SumatraPDF.exe!ParseChunk (offset 0x1A10)",
            "explanation": "Based on the stack trace, the crash occurs deep within the document loading sequence. A length field provided by the input is not validated against the actual buffer boundaries, leading to an invalid memory access.",
            "recommended_investigation": "1. Run the minimized artifact through an ASAN-instrumented build.\n2. Set a breakpoint at ParseChunk to observe the length parameter.\n3. Validate if the length field can be artificially inflated.",
            "remediation_guidance": "Implement bounds checking before the memcpy/read operation in ParseChunk. Ensure that offset + length <= buffer_size.",
            "confidence": "High",
            "uncertainty": "Exact source lines are unknown as debug symbols were not provided in the context."
        }
