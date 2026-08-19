"""
Fuzz-Sentinel Analysis Engine: Data Contracts
==============================================
Defines the canonical data structures shared between all analysis pipeline
components. These types distinguish observed, inferred, and user-provided data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class EvidenceKind(str, Enum):
    """Classifies the epistemic status of a piece of information."""
    OBSERVED = "observed"    # Directly read from source/binary (highest trust)
    INFERRED  = "inferred"   # Derived by analysis heuristic (medium trust)
    USER_PROVIDED = "user_provided"  # Supplied by the analyst (must be labelled)


class HarnessType(str, Enum):
    FILE_READER   = "file_reader"
    NETWORK_STUB  = "network_stub"
    API_FUZZER    = "api_fuzzer"
    FORMAT_PARSER = "format_parser"


@dataclass
class ScoringReason:
    """One scored indicator contributing to the overall risk score."""
    indicator: str          # e.g. "buffer_write", "memcpy_call"
    description: str        # Human-readable explanation
    weight: float           # 0.0 – 1.0 added to total score
    evidence_kind: EvidenceKind
    source_ref: Optional[str] = None   # e.g. "line 142 of PdfReader.cpp"


@dataclass
class FunctionParameter:
    """Represents one parameter of the analysed function."""
    name: Optional[str]
    param_type: Optional[str]
    is_attacker_controlled: bool
    evidence_kind: EvidenceKind
    notes: str = ""


@dataclass
class CallEdge:
    """One edge in the call graph leading to this target."""
    caller: str
    callee: str
    evidence_kind: EvidenceKind
    source_ref: Optional[str] = None


@dataclass
class DiscoveredTarget:
    """
    Complete output record for one candidate fuzzing target function.
    All fields carry an evidence_kind so consumers know whether data is
    observed, inferred, or user-supplied. Address is ALWAYS marked inferred
    unless extracted directly from a binary (PDB/DWARF).
    """
    # Identity
    function_name: str
    module: str

    # Location – may be partial; each field carries its own epistemic status
    source_file:   Optional[str]         = None
    source_line:   Optional[int]         = None
    source_file_kind: EvidenceKind       = EvidenceKind.OBSERVED
    address:       Optional[str]         = None   # hex string or None
    address_kind:  EvidenceKind          = EvidenceKind.INFERRED  # NEVER claim as observed unless from binary

    # Scoring
    risk_score:    float                 = 0.0    # 0.0 – 10.0
    confidence:    float                 = 0.0    # 0.0 – 1.0
    reasons:       List[ScoringReason]   = field(default_factory=list)

    # Structural information
    parameters:    List[FunctionParameter] = field(default_factory=list)
    call_path:     List[CallEdge]          = field(default_factory=list)
    dependencies:  List[str]               = field(default_factory=list)

    # Recommendations
    suggested_harness_type: HarnessType  = HarnessType.FILE_READER
    input_type:    str                   = "binary"

    # Raw indicators found during analysis
    raw_indicators: Dict[str, Any]       = field(default_factory=dict)

    # Timestamps
    analyzed_at:   datetime              = field(default_factory=datetime.utcnow)

    def total_score(self) -> float:
        """Sum of all reason weights, capped at 10.0."""
        return min(sum(r.weight for r in self.reasons), 10.0)
