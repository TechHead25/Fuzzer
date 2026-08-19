from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Target(Base):
    __tablename__ = "targets"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String, index=True)
    module = Column(String)
    address = Column(String, nullable=True)
    # address_kind: "observed" (from binary/PDB) | "inferred" | "user_provided"
    address_kind = Column(String, nullable=True, default="inferred")
    source_file = Column(String, nullable=True)
    source_line = Column(Integer, nullable=True)
    input_type = Column(String, default="binary")
    risk_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    # Status workflow: DISCOVERED -> REVIEW_REQUIRED -> VERIFIED ->
    #                 HARNESS_READY -> FUZZING_READY -> ACTIVE -> DISABLED
    status = Column(String, default="DISCOVERED")
    # Structured extended fields
    arguments = Column(JSON, nullable=True)       # list of {name, type, is_attacker_controlled}
    call_path = Column(JSON, nullable=True)        # list of {caller, callee, evidence_kind}
    dependencies = Column(JSON, nullable=True)     # list of dependency strings
    # Provenance
    import_source = Column(String, nullable=True)  # "manual" | "source_analysis" | "ghidra" | "re_notes" | "function_list" | "call_graph"
    import_session_id = Column(Integer, ForeignKey("import_sessions.id"), nullable=True)
    # Analyst notes
    analyst_notes = Column(Text, nullable=True)
    # Verification (denormalised for fast queries; canonical record in TargetVerification)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class TargetVerification(Base):
    """Immutable audit trail of every status transition for a target."""
    __tablename__ = "target_verifications"
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    verified_by = Column(String)             # analyst name / identifier
    previous_status = Column(String)
    new_status = Column(String)
    evidence = Column(JSON, nullable=True)   # list of evidence strings / hashes
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


class ImportSession(Base):
    """Tracks each import job (Ghidra export, RE notes, function list, etc.)."""
    __tablename__ = "import_sessions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    import_type = Column(String)   # "ghidra_csv" | "ghidra_json" | "function_list" | "re_notes" | "call_graph" | "source_analysis"
    filename = Column(String)
    status = Column(String)        # "pending" | "complete" | "error"
    targets_imported = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    raw_payload_hash = Column(String, nullable=True)   # SHA-256 of uploaded file
    result_summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TargetEvidence(Base):
    __tablename__ = "target_evidence"
    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"))
    risk_reasons = Column(JSON)
    attacker_controlled_inputs = Column(JSON)
    memory_operations = Column(JSON)

class Harness(Base):
    __tablename__ = "harnesses"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    name = Column(String)
    engine = Column(String, default="winafl")
    input_type = Column(String, default="file")  # file, memory_buffer, buffer_and_length, structured
    files = Column(JSON, nullable=True)          # Dict of filename -> content
    metadata_json = Column(JSON, nullable=True)  # Init, cleanup, deps info
    status = Column(String, default="CREATED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class HarnessBuild(Base):
    __tablename__ = "harness_builds"
    id = Column(Integer, primary_key=True, index=True)
    harness_id = Column(Integer, ForeignKey("harnesses.id"))
    compiler = Column(String, nullable=True)
    compiler_version = Column(String, nullable=True)
    architecture = Column(String, nullable=True)
    build_command = Column(String, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    binary_path = Column(String, nullable=True)
    hash = Column(String, nullable=True)
    status = Column(String, default="BUILDING")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SeedCorpus(Base):
    __tablename__ = "seed_corpora"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    name = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Seed(Base):
    __tablename__ = "seeds"
    id = Column(Integer, primary_key=True, index=True)
    corpus_id = Column(Integer, ForeignKey("seed_corpora.id"))
    filename = Column(String)
    file_type = Column(String, default="application/octet-stream")
    origin = Column(String, default="UPLOAD") # UPLOAD, MINIMIZED, MUTATED, CRASH
    file_path = Column(String)
    hash = Column(String)
    size = Column(Integer)
    metadata_json = Column(JSON, nullable=True)
    parent_seed_id = Column(Integer, ForeignKey("seeds.id"), nullable=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    discovered_coverage = Column(Boolean, default=False)
    triggered_crash = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    harness_id = Column(Integer, ForeignKey("harnesses.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    fuzzer = Column(String)
    instrumentation = Column(String)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String)
    executions = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CampaignConfiguration(Base):
    __tablename__ = "campaign_configurations"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    corpus_id = Column(Integer, ForeignKey("seed_corpora.id"), nullable=True)
    fuzzer_version = Column(String, nullable=True)
    instrumentation_version = Column(String, nullable=True)
    command_args = Column(JSON, nullable=True)
    env_vars = Column(JSON, nullable=True)
    timeout = Column(Integer)
    duration_limit_secs = Column(Integer, nullable=True)
    memory_limit = Column(Integer)
    dictionary_path = Column(String, nullable=True)

class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    executions = Column(Integer)
    execs_per_second = Column(Float)
    unique_paths = Column(Integer)
    crashes = Column(Integer)
    hangs = Column(Integer, default=0)

class CoverageSnapshot(Base):
    __tablename__ = "coverage_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    coverage_metric = Column(String, default="edge")
    unique_paths = Column(Integer, nullable=True)
    blocks = Column(Integer, nullable=True)
    edges = Column(Integer, nullable=True)
    coverage_data = Column(JSON, nullable=True)
    artifact_reference = Column(String, nullable=True)

class Crash(Base):
    __tablename__ = "crashes"
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    input_artifact = Column(String)
    minimized_artifact = Column(String, nullable=True)
    exception_type = Column(String)
    fault_address = Column(String)
    module = Column(String)
    stack_trace = Column(Text)
    crash_signature = Column(String)
    status = Column(String, default="DETECTED")
    duplicate_of_id = Column(Integer, ForeignKey("crashes.id"), nullable=True)
    ai_analysis_notes = Column(Text, nullable=True)
    human_review_notes = Column(Text, nullable=True)
    severity = Column(String, nullable=True)
    vulnerability_class = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CrashArtifact(Base):
    __tablename__ = "crash_artifacts"
    id = Column(Integer, primary_key=True, index=True)
    crash_id = Column(Integer, ForeignKey("crashes.id"))
    file_path = Column(String)
    hash = Column(String)
    type = Column(String)

class CrashSignature(Base):
    __tablename__ = "crash_signatures"
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, unique=True, index=True)
    normalized_stack = Column(Text)
    classification = Column(String)

class Finding(Base):
    __tablename__ = "findings"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    target_id = Column(Integer, ForeignKey("targets.id"))
    crash_id = Column(Integer, ForeignKey("crashes.id"))
    title = Column(String)
    description = Column(Text)
    severity = Column(String)
    status = Column(String)

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String) # 'Target', 'Crash'
    entity_id = Column(Integer)
    prompt = Column(Text)
    response = Column(Text)
    confidence = Column(Float)
    provider = Column(String)

class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    entity_type = Column(String)
    entity_id = Column(Integer)
    hash = Column(String)
    payload = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    title = Column(String)
    content_html = Column(Text)
    report_hash = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Worker(Base):
    __tablename__ = "workers"
    id = Column(Integer, primary_key=True, index=True)
    hostname = Column(String)
    ip_address = Column(String)
    status = Column(String)
    last_seen = Column(DateTime(timezone=True))
    capabilities = Column(JSON)

class WorkerJob(Base):
    __tablename__ = "worker_jobs"
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
    job_type = Column(String)
    status = Column(String)
    logs = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SystemLog(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String)
    module = Column(String)
    message = Column(Text)
    metadata_ = Column(JSON) # 'metadata' is reserved by SQLAlchemy
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class AIAnalysisRecord(Base):
    __tablename__ = "ai_analysis_records"
    id = Column(Integer, primary_key=True, index=True)
    crash_id = Column(Integer, ForeignKey("crashes.id"))
    model_name = Column(String)
    model_version = Column(String)
    prompt_version = Column(String)
    evidence_ids = Column(JSON, nullable=True)
    response_payload = Column(JSON)
    reviewer_decision = Column(String, default="PENDING")
    reviewer_notes = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
