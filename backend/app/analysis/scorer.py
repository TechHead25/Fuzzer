"""
Fuzz-Sentinel Analysis Engine: Target Scorer
============================================
Explainable, indicator-based scoring model.
Each indicator has a documented weight and evidence classification.
The scorer never fabricates indicators – it only scores what the
analyzer observed or inferred.
"""

from typing import List
from .types import DiscoveredTarget, ScoringReason, EvidenceKind, HarnessType


# ---------------------------------------------------------------------------
# Indicator catalogue with documented weights
# ---------------------------------------------------------------------------
INDICATOR_WEIGHTS: dict[str, dict] = {
    # Attacker-controlled data flows (highest value)
    "attacker_controlled_param": {
        "weight": 2.5,
        "description": "Function receives a parameter that originates from attacker-controlled input",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Memory operations
    "memcpy_call": {
        "weight": 1.5,
        "description": "Calls memcpy, memmove, or equivalent – potential buffer overflow site",
        "harness_hint": HarnessType.FILE_READER,
    },
    "buffer_write": {
        "weight": 1.2,
        "description": "Direct write into a fixed-size buffer",
        "harness_hint": HarnessType.FILE_READER,
    },
    "buffer_read": {
        "weight": 0.6,
        "description": "Reads from a buffer controlled by caller",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Length/offset arithmetic
    "length_arithmetic": {
        "weight": 1.0,
        "description": "Arithmetic operations on length or size values – integer overflow risk",
        "harness_hint": HarnessType.FILE_READER,
    },
    "offset_arithmetic": {
        "weight": 0.8,
        "description": "Arithmetic operations on offset or index values",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Parsing / format processing
    "parser_routine": {
        "weight": 1.2,
        "description": "Function is a parser: reads structured fields from input",
        "harness_hint": HarnessType.FORMAT_PARSER,
    },
    "format_string_op": {
        "weight": 0.9,
        "description": "Uses sscanf, sprintf, or similar format-string function",
        "harness_hint": HarnessType.FORMAT_PARSER,
    },
    "string_operation": {
        "weight": 0.7,
        "description": "Uses strcpy, strcat, strlen, or similar string function",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Decompression / encoding
    "decompression_call": {
        "weight": 1.3,
        "description": "Calls a decompression routine (zlib, lzma, etc.) – recursive or nested data risk",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Control flow complexity
    "complex_loop": {
        "weight": 0.8,
        "description": "Contains a loop whose bounds depend on input data",
        "harness_hint": HarnessType.FILE_READER,
    },
    "deep_call_path": {
        "weight": 0.5,
        "description": "Reachable from an entry point via a call path of depth ≥ 3",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Heap allocation
    "heap_allocation": {
        "weight": 0.6,
        "description": "Allocates heap memory whose size depends on input data",
        "harness_hint": HarnessType.FILE_READER,
    },
    # File / stream I/O
    "file_io": {
        "weight": 0.4,
        "description": "Reads from a file or stream – potential to drive with corpus",
        "harness_hint": HarnessType.FILE_READER,
    },
    # Network I/O
    "network_recv": {
        "weight": 0.4,
        "description": "Receives data from a network socket",
        "harness_hint": HarnessType.NETWORK_STUB,
    },
}


class TargetScorer:
    """
    Converts raw indicator maps from analyzers into scored DiscoveredTarget
    objects with fully explainable ScoringReason lists.
    """

    def score(self, target: DiscoveredTarget) -> DiscoveredTarget:
        """
        Populate target.reasons and target.risk_score from target.raw_indicators.
        Also chooses the best harness type suggestion.
        """
        reasons: List[ScoringReason] = []
        harness_votes: dict[HarnessType, float] = {}

        for indicator, value in target.raw_indicators.items():
            if not value:
                continue
            spec = INDICATOR_WEIGHTS.get(indicator)
            if spec is None:
                continue

            weight = spec["weight"]
            evidence_kind = (
                EvidenceKind.OBSERVED
                if indicator in _OBSERVABLE_INDICATORS
                else EvidenceKind.INFERRED
            )
            source_ref = None
            if isinstance(value, str):
                source_ref = value  # e.g. "line 87"
            elif isinstance(value, list) and value:
                source_ref = ", ".join(str(v) for v in value[:3])

            reasons.append(ScoringReason(
                indicator=indicator,
                description=spec["description"],
                weight=weight,
                evidence_kind=evidence_kind,
                source_ref=source_ref,
            ))
            hint: HarnessType = spec["harness_hint"]
            harness_votes[hint] = harness_votes.get(hint, 0.0) + weight

        target.reasons = reasons
        target.risk_score = min(sum(r.weight for r in reasons), 10.0)
        target.suggested_harness_type = (
            max(harness_votes, key=harness_votes.get)
            if harness_votes else HarnessType.FILE_READER
        )
        # Confidence is proportional to how many observed (vs inferred) indicators
        n_observed = sum(1 for r in reasons if r.evidence_kind == EvidenceKind.OBSERVED)
        target.confidence = min(n_observed / max(len(reasons), 1), 1.0)
        return target


# Indicators that can be directly observed from source text
_OBSERVABLE_INDICATORS = {
    "memcpy_call",
    "buffer_write",
    "buffer_read",
    "string_operation",
    "format_string_op",
    "decompression_call",
    "file_io",
    "network_recv",
    "heap_allocation",
    "complex_loop",
}
