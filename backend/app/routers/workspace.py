"""
Phase 4: Target Research Workspace API
========================================
Endpoints:

Import
  POST /api/v1/projects/{project_id}/workspace/import
       Upload a reverse-engineering evidence file (Ghidra CSV/JSON, RE notes, etc.)
  GET  /api/v1/projects/{project_id}/workspace/imports
       List import sessions for a project
  GET  /api/v1/projects/{project_id}/workspace/imports/{session_id}
       Get import session detail

Target management (extends Phase 3 discovery router)
  POST /api/v1/projects/{project_id}/workspace/targets
       Manually add a target
  PATCH /api/v1/projects/{project_id}/workspace/targets/{target_id}
       Update target fields
  POST /api/v1/projects/{project_id}/workspace/targets/{target_id}/verify
       Record a verification (status transition with audit trail)
  GET  /api/v1/projects/{project_id}/workspace/targets/{target_id}/verifications
       List all verifications for a target

SumatraPDF overview
  GET  /api/v1/projects/{project_id}/workspace/overview
       Returns target counts, status breakdown, per-target coverage

Import format schema reference
  GET  /api/v1/workspace/import-formats
       Returns schema documentation for all supported import formats
"""

import io
import hashlib
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import (
    APIRouter, Depends, HTTPException, UploadFile, File,
    Form, BackgroundTasks, Query
)
from sqlalchemy.orm import Session
from sqlalchemy import func

from .. import models
from ..database import get_db
from ..imports import get_parser, SUPPORTED_IMPORT_TYPES
from ..schemas_workspace import (
    TargetCreateManual,
    TargetPatch,
    TargetVerifyRequest,
    TargetWithVerification,
    VerificationRecord,
    ImportSessionSummary,
    WorkspaceOverview,
    ImportFormatDoc,
    IMPORT_FORMAT_DOCS,
    TARGET_STATUS_TRANSITIONS,
)

logger = logging.getLogger("fuzz_sentinel.routers.workspace")

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/workspace",
    tags=["workspace"],
)

# ---------------------------------------------------------------------------
# Import format reference
# ---------------------------------------------------------------------------
@router.get("/import-formats", response_model=List[ImportFormatDoc], tags=["workspace"])
def list_import_formats(project_id: int):
    return IMPORT_FORMAT_DOCS


# ---------------------------------------------------------------------------
# Upload and import RE evidence
# ---------------------------------------------------------------------------
@router.post("/import", response_model=ImportSessionSummary)
async def import_evidence(
    project_id: int,
    background_tasks: BackgroundTasks,
    import_type: str = Form(...),
    evidence_file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a reverse-engineering evidence file and import it as target records.
    Returns an ImportSession immediately; processing happens synchronously
    (files are typically small — RE exports).
    """
    _require_project(project_id, db)

    if import_type not in SUPPORTED_IMPORT_TYPES:
        raise HTTPException(400, f"Unsupported import type. Use one of: {', '.join(SUPPORTED_IMPORT_TYPES)}")

    content = await evidence_file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(413, "File exceeds 50 MB limit")

    file_hash = hashlib.sha256(content).hexdigest()

    session = models.ImportSession(
        project_id=project_id,
        import_type=import_type,
        filename=evidence_file.filename or "upload",
        status="pending",
        raw_payload_hash=file_hash,
    )
    db.add(session)
    db.flush()

    try:
        parser = get_parser(import_type)
        records = parser.parse(content, filename=evidence_file.filename or "")
    except Exception as exc:
        session.status = "error"
        session.error_message = str(exc)
        db.commit()
        raise HTTPException(422, f"Parse error: {exc}") from exc

    saved = 0
    skipped = 0
    for rec in records:
        try:
            _upsert_imported_target(db, project_id, session.id, rec)
            saved += 1
        except Exception as exc:
            logger.warning(f"Skipping record {rec.function_name}: {exc}")
            skipped += 1

    session.status = "complete"
    session.targets_imported = saved
    session.result_summary = {
        "parsed": len(records),
        "saved": saved,
        "skipped": skipped,
    }
    db.commit()

    return ImportSessionSummary(
        id=session.id,
        project_id=project_id,
        import_type=import_type,
        filename=session.filename,
        status=session.status,
        targets_imported=saved,
        error_message=session.error_message,
        result_summary=session.result_summary,
        created_at=session.created_at,
    )


@router.get("/imports", response_model=List[ImportSessionSummary])
def list_import_sessions(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    _require_project(project_id, db)
    sessions = (
        db.query(models.ImportSession)
        .filter(models.ImportSession.project_id == project_id)
        .order_by(models.ImportSession.created_at.desc())
        .offset(skip).limit(limit).all()
    )
    return [
        ImportSessionSummary(
            id=s.id,
            project_id=s.project_id,
            import_type=s.import_type,
            filename=s.filename,
            status=s.status,
            targets_imported=s.targets_imported or 0,
            error_message=s.error_message,
            result_summary=s.result_summary,
            created_at=s.created_at,
        )
        for s in sessions
    ]


# ---------------------------------------------------------------------------
# Manual target management
# ---------------------------------------------------------------------------
@router.post("/targets", response_model=TargetWithVerification, status_code=201)
def create_target_manual(
    project_id: int,
    payload: TargetCreateManual,
    db: Session = Depends(get_db),
):
    """Manually add a research target with full field control."""
    _require_project(project_id, db)

    target = models.Target(
        project_id=project_id,
        name=payload.name,
        module=payload.module,
        address=payload.address,
        address_kind=payload.address_kind,
        source_file=payload.source_file,
        source_line=payload.source_line,
        input_type=payload.input_type,
        risk_score=payload.risk_score,
        confidence=payload.confidence,
        status="DISCOVERED",
        arguments=[a.model_dump() for a in payload.arguments] if payload.arguments else [],
        call_path=[c.model_dump() for c in payload.call_path] if payload.call_path else [],
        dependencies=payload.dependencies or [],
        analyst_notes=payload.analyst_notes,
        import_source="manual",
    )
    db.add(target)
    db.flush()

    _record_verification(
        db, target.id,
        verified_by=payload.added_by or "researcher",
        prev_status=None,
        new_status="DISCOVERED",
        evidence=payload.evidence,
        notes=f"Manually added. {payload.analyst_notes or ''}".strip(),
    )
    db.commit()
    return _build_target_response(target, db)


@router.patch("/targets/{target_id}", response_model=TargetWithVerification)
def update_target(
    project_id: int,
    target_id: int,
    payload: TargetPatch,
    db: Session = Depends(get_db),
):
    """Update editable target fields. Status changes must go through /verify."""
    _require_project(project_id, db)
    target = _require_target(project_id, target_id, db)

    for field_name, value in payload.model_dump(exclude_unset=True).items():
        if field_name in ("arguments", "call_path") and isinstance(value, list):
            value = [v.model_dump() if hasattr(v, "model_dump") else v for v in value]
        setattr(target, field_name, value)

    target.updated_at = datetime.utcnow()
    db.commit()
    return _build_target_response(target, db)


# ---------------------------------------------------------------------------
# Verification workflow
# ---------------------------------------------------------------------------
@router.post("/targets/{target_id}/verify", response_model=TargetWithVerification)
def verify_target(
    project_id: int,
    target_id: int,
    payload: TargetVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Transition a target to a new status. Records the full verification trail.
    Only allowed transitions are accepted (see TARGET_STATUS_TRANSITIONS).
    """
    _require_project(project_id, db)
    target = _require_target(project_id, target_id, db)

    allowed = TARGET_STATUS_TRANSITIONS.get(target.status, [])
    if payload.new_status not in allowed:
        raise HTTPException(
            400,
            f"Status '{target.status}' cannot transition to '{payload.new_status}'. "
            f"Allowed transitions: {allowed}"
        )

    prev = target.status
    target.status = payload.new_status
    target.updated_at = datetime.utcnow()

    if payload.new_status == "VERIFIED":
        target.verified_by = payload.verified_by
        target.verified_at = datetime.utcnow()

    _record_verification(
        db, target.id,
        verified_by=payload.verified_by,
        prev_status=prev,
        new_status=payload.new_status,
        evidence=payload.evidence,
        notes=payload.notes,
    )
    db.commit()
    return _build_target_response(target, db)


@router.get("/targets/{target_id}/verifications", response_model=List[VerificationRecord])
def list_verifications(
    project_id: int,
    target_id: int,
    db: Session = Depends(get_db),
):
    _require_project(project_id, db)
    _require_target(project_id, target_id, db)
    records = (
        db.query(models.TargetVerification)
        .filter(models.TargetVerification.target_id == target_id)
        .order_by(models.TargetVerification.timestamp.asc())
        .all()
    )
    return [
        VerificationRecord(
            id=r.id,
            target_id=r.target_id,
            verified_by=r.verified_by,
            previous_status=r.previous_status,
            new_status=r.new_status,
            evidence=r.evidence,
            notes=r.notes,
            timestamp=r.timestamp,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# SumatraPDF / project overview
# ---------------------------------------------------------------------------
@router.get("/overview", response_model=WorkspaceOverview)
def get_workspace_overview(project_id: int, db: Session = Depends(get_db)):
    _require_project(project_id, db)

    all_targets = db.query(models.Target).filter(models.Target.project_id == project_id).all()

    by_status: dict = {}
    for t in all_targets:
        by_status[t.status] = by_status.get(t.status, 0) + 1

    active = by_status.get("ACTIVE", 0)
    verified = by_status.get("VERIFIED", 0) + by_status.get("HARNESS_READY", 0) + \
               by_status.get("FUZZING_READY", 0) + active
    harness_ready = by_status.get("HARNESS_READY", 0)
    fuzzing_ready = by_status.get("FUZZING_READY", 0)
    review_required = by_status.get("REVIEW_REQUIRED", 0)
    disabled = by_status.get("DISABLED", 0)

    # Per-target coverage (from latest coverage snapshot per campaign)
    coverage_by_target: dict = {}
    for t in all_targets:
        # Get campaigns for this target
        campaigns = db.query(models.Campaign).filter(
            models.Campaign.target_id == t.id
        ).all()
        max_edges = 0
        for camp in campaigns:
            snap = (
                db.query(models.CoverageSnapshot)
                .filter(models.CoverageSnapshot.campaign_id == camp.id)
                .order_by(models.CoverageSnapshot.timestamp.desc())
                .first()
            )
            if snap and snap.edges and snap.edges > max_edges:
                max_edges = snap.edges
        if max_edges:
            coverage_by_target[t.name] = max_edges

    # Import sessions count
    import_count = db.query(models.ImportSession).filter(
        models.ImportSession.project_id == project_id
    ).count()

    return WorkspaceOverview(
        project_id=project_id,
        total_targets=len(all_targets),
        by_status=by_status,
        discovered=by_status.get("DISCOVERED", 0),
        review_required=review_required,
        verified=verified,
        harness_ready=harness_ready,
        fuzzing_ready=fuzzing_ready,
        active=active,
        disabled=disabled,
        import_sessions=import_count,
        coverage_by_target=coverage_by_target,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _require_project(project_id: int, db: Session) -> models.Project:
    p = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not p:
        raise HTTPException(404, f"Project {project_id} not found")
    return p


def _require_target(project_id: int, target_id: int, db: Session) -> models.Target:
    t = (
        db.query(models.Target)
        .filter(models.Target.id == target_id, models.Target.project_id == project_id)
        .first()
    )
    if not t:
        raise HTTPException(404, f"Target {target_id} not found in project {project_id}")
    return t


def _record_verification(
    db: Session,
    target_id: int,
    verified_by: str,
    prev_status: Optional[str],
    new_status: str,
    evidence: Optional[List[str]],
    notes: Optional[str],
) -> None:
    db.add(models.TargetVerification(
        target_id=target_id,
        verified_by=verified_by,
        previous_status=prev_status or "",
        new_status=new_status,
        evidence=evidence or [],
        notes=notes or "",
    ))
    db.flush()


def _build_target_response(target: models.Target, db: Session) -> TargetWithVerification:
    verifications = (
        db.query(models.TargetVerification)
        .filter(models.TargetVerification.target_id == target.id)
        .order_by(models.TargetVerification.id.desc())
        .all()
    )
    return TargetWithVerification(
        id=target.id,
        project_id=target.project_id,
        name=target.name,
        module=target.module,
        address=target.address,
        address_kind=target.address_kind,
        source_file=target.source_file,
        source_line=target.source_line,
        input_type=target.input_type,
        risk_score=target.risk_score,
        confidence=target.confidence,
        status=target.status,
        arguments=target.arguments or [],
        call_path=target.call_path or [],
        dependencies=target.dependencies or [],
        import_source=target.import_source,
        analyst_notes=target.analyst_notes,
        verified_by=target.verified_by,
        verified_at=target.verified_at,
        created_at=target.created_at,
        updated_at=target.updated_at,
        verifications=[
            VerificationRecord(
                id=v.id,
                target_id=v.target_id,
                verified_by=v.verified_by,
                previous_status=v.previous_status,
                new_status=v.new_status,
                evidence=v.evidence,
                notes=v.notes,
                timestamp=v.timestamp,
            )
            for v in verifications
        ],
    )


def _upsert_imported_target(
    db: Session,
    project_id: int,
    session_id: int,
    rec,
) -> None:
    """Upsert an ImportedTarget into the database."""
    existing = (
        db.query(models.Target)
        .filter(
            models.Target.project_id == project_id,
            models.Target.name == rec.function_name,
            models.Target.module == rec.module,
        )
        .first()
    )
    if existing:
        # Only update fields that were provided (not None) in the import
        if rec.address:
            existing.address = rec.address
            existing.address_kind = rec.address_kind
        if rec.source_file:
            existing.source_file = rec.source_file
        if rec.source_line:
            existing.source_line = rec.source_line
        if rec.arguments:
            existing.arguments = rec.arguments
        if rec.call_path:
            existing.call_path = rec.call_path
        if rec.dependencies:
            existing.dependencies = rec.dependencies
        if rec.risk_score > 0:
            existing.risk_score = rec.risk_score
        if rec.confidence > 0:
            existing.confidence = rec.confidence
        if rec.analyst_notes:
            existing.analyst_notes = (existing.analyst_notes or "") + f"\n[{rec.import_source}] {rec.analyst_notes}"
        existing.import_session_id = session_id
        existing.updated_at = datetime.utcnow()
        # Escalate status only if still at DISCOVERED
        if existing.status == "DISCOVERED":
            existing.status = "REVIEW_REQUIRED"
    else:
        db.add(models.Target(
            project_id=project_id,
            name=rec.function_name,
            module=rec.module,
            address=rec.address,
            address_kind=rec.address_kind,
            source_file=rec.source_file,
            source_line=rec.source_line,
            input_type=rec.input_type,
            risk_score=rec.risk_score,
            confidence=rec.confidence,
            status="DISCOVERED",
            arguments=rec.arguments or [],
            call_path=rec.call_path or [],
            dependencies=rec.dependencies or [],
            analyst_notes=rec.analyst_notes,
            import_source=rec.import_source,
            import_session_id=session_id,
        ))
    db.flush()
