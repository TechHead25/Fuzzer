"""
Pydantic schemas for Phase 4: Target Research Workspace.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ---------------------------------------------------------------------------
# Status workflow
# ---------------------------------------------------------------------------
TARGET_STATUSES = [
    "DISCOVERED",
    "REVIEW_REQUIRED",
    "VERIFIED",
    "HARNESS_READY",
    "FUZZING_READY",
    "ACTIVE",
    "DISABLED",
]

TARGET_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    "DISCOVERED":      ["REVIEW_REQUIRED", "DISABLED"],
    "REVIEW_REQUIRED": ["VERIFIED", "DISCOVERED", "DISABLED"],
    "VERIFIED":        ["HARNESS_READY", "REVIEW_REQUIRED", "DISABLED"],
    "HARNESS_READY":   ["FUZZING_READY", "VERIFIED", "DISABLED"],
    "FUZZING_READY":   ["ACTIVE", "HARNESS_READY", "DISABLED"],
    "ACTIVE":          ["FUZZING_READY", "DISABLED"],
    "DISABLED":        ["DISCOVERED"],
}

# ---------------------------------------------------------------------------
# Shared sub-schemas
# ---------------------------------------------------------------------------
class ArgumentSchema(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_attacker_controlled: bool = False

class CallEdgeSchema(BaseModel):
    caller: str
    callee: str
    evidence_kind: str = "user_provided"

class VerificationRecord(BaseModel):
    id: int
    target_id: int
    verified_by: str
    previous_status: Optional[str] = None
    new_status: str
    evidence: Optional[List[str]] = None
    notes: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# ---------------------------------------------------------------------------
# Target schemas
# ---------------------------------------------------------------------------
class TargetCreateManual(BaseModel):
    """Schema for manually adding a research target."""
    name: str = Field(..., description="Exact function name as observed")
    module: str = Field(..., description="Module/binary name")
    address: Optional[str] = Field(None, description="Hex address if known from binary")
    address_kind: str = Field("user_provided", description="'observed' | 'inferred' | 'user_provided'")
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    input_type: str = "binary"
    risk_score: float = Field(0.0, ge=0.0, le=10.0)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    arguments: Optional[List[ArgumentSchema]] = None
    call_path: Optional[List[CallEdgeSchema]] = None
    dependencies: Optional[List[str]] = None
    analyst_notes: Optional[str] = None
    evidence: Optional[List[str]] = None
    added_by: Optional[str] = Field("researcher", description="Analyst who added this target")


class TargetPatch(BaseModel):
    """Partial update schema (all fields optional)."""
    module: Optional[str] = None
    address: Optional[str] = None
    address_kind: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    input_type: Optional[str] = None
    risk_score: Optional[float] = Field(None, ge=0.0, le=10.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    arguments: Optional[List[ArgumentSchema]] = None
    call_path: Optional[List[CallEdgeSchema]] = None
    dependencies: Optional[List[str]] = None
    analyst_notes: Optional[str] = None


class TargetVerifyRequest(BaseModel):
    new_status: str = Field(..., description="Target status to transition to")
    verified_by: str = Field(..., description="Name/ID of the analyst performing verification")
    evidence: Optional[List[str]] = Field(None, description="Evidence strings supporting this transition")
    notes: Optional[str] = Field(None, description="Free-text notes")


class TargetWithVerification(BaseModel):
    """Full target record including verification history."""
    id: int
    project_id: int
    name: str
    module: str
    address: Optional[str] = None
    address_kind: Optional[str] = None
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    input_type: str
    risk_score: float
    confidence: float
    status: str
    arguments: List[Dict[str, Any]] = []
    call_path: List[Dict[str, Any]] = []
    dependencies: List[str] = []
    import_source: Optional[str] = None
    analyst_notes: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    verifications: List[VerificationRecord] = []

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Import schemas
# ---------------------------------------------------------------------------
class ImportSessionSummary(BaseModel):
    id: int
    project_id: int
    import_type: str
    filename: str
    status: str
    targets_imported: int
    error_message: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Overview schema
# ---------------------------------------------------------------------------
class WorkspaceOverview(BaseModel):
    project_id: int
    total_targets: int
    by_status: Dict[str, int]
    discovered: int
    review_required: int
    verified: int
    harness_ready: int
    fuzzing_ready: int
    active: int
    disabled: int
    import_sessions: int
    coverage_by_target: Dict[str, int]


# ---------------------------------------------------------------------------
# Import format documentation
# ---------------------------------------------------------------------------
class ImportFormatDoc(BaseModel):
    import_type: str
    display_name: str
    description: str
    accepted_extensions: List[str]
    example_schema: Optional[str] = None
    notes: Optional[str] = None


IMPORT_FORMAT_DOCS: List[ImportFormatDoc] = [
    ImportFormatDoc(
        import_type="ghidra_csv",
        display_name="Ghidra CSV Export",
        description="Exported from Ghidra via File → Export Program → CSV. Contains function names, addresses, namespaces, and optionally signatures.",
        accepted_extensions=[".csv"],
        example_schema="Name,Location,Type,Namespace,Source\nParseHeader,0x00401234,Function,PdfReader,PdfReader.cpp",
        notes="Addresses from Ghidra are observed (read from binary). Auto-generated FUN_* names are included but marked as low-confidence.",
    ),
    ImportFormatDoc(
        import_type="ghidra_json",
        display_name="Ghidra JSON Export",
        description="JSON export from Ghidra scripts (ExportProgramScript or custom GhidraScript). Top-level keys: functions, datatypes, imports, exports.",
        accepted_extensions=[".json"],
        example_schema='{"functions":[{"name":"ParseHeader","entryPoint":"0x401234","parameters":[{"name":"buf","dataType":"uchar *"}]}]}',
    ),
    ImportFormatDoc(
        import_type="function_list",
        display_name="Function List",
        description="Plain text (one name per line) or JSON list of function names with optional addresses and modules. Useful for importing IDA/WinDbg symbol exports.",
        accepted_extensions=[".txt", ".json"],
        example_schema="ParsePdfHeader\n0x00401234 LoadDocument\n[{\"name\": \"OpenFile\", \"address\": \"0x402000\"}]",
    ),
    ImportFormatDoc(
        import_type="re_notes",
        display_name="RE Notes (JSON)",
        description="Fuzz-Sentinel's canonical structured RE notes format. Supports full field specification including address_kind, arguments, call_path, and analyst confidence.",
        accepted_extensions=[".json"],
        example_schema='{"targets":[{"function":"ParseDocumentHeader","module":"SumatraPDF","address_kind":"user_provided","risk_score":7.5,"notes":"Reads attacker-controlled size field"}]}',
        notes="This is the recommended format for manual research notes. All evidence is preserved verbatim.",
    ),
    ImportFormatDoc(
        import_type="call_graph",
        display_name="Call Graph",
        description="Call graph in DOT format (digraph { A -> B; }) or JSON adjacency list ({\"edges\":[{\"caller\":\"A\",\"callee\":\"B\"}]}). Unique callees become target candidates.",
        accepted_extensions=[".dot", ".json"],
    ),
    ImportFormatDoc(
        import_type="binary_metadata",
        display_name="Binary Metadata (JSON)",
        description="JSON file containing binary exports/symbols from dumpbin /EXPORTS, nm, objdump, or a custom extraction script.",
        accepted_extensions=[".json"],
        example_schema='{"binary":"SumatraPDF.exe","exports":[{"name":"ParsePDF","address":"0x401234","type":"function"}]}',
    ),
]
