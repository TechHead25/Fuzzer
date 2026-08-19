"""
Target Discovery & Management API Router
=========================================
Endpoints:
  POST /api/v1/projects/{project_id}/targets/discover/source
       - Upload a .zip of source files and run the analysis pipeline
  GET  /api/v1/projects/{project_id}/targets/
       - List all targets for a project (paginated, sortable)
  GET  /api/v1/projects/{project_id}/targets/{target_id}
       - Get one target with full evidence
  GET  /api/v1/projects/{project_id}/targets/{target_id}/evidence
       - Get evidence records for a target
  DELETE /api/v1/projects/{project_id}/targets/{target_id}
       - Remove a target
"""

import io
import os
import zipfile
import tempfile
import logging
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..analysis import AnalysisPipeline
from ..schemas_discovery import (
    TargetDetail,
    TargetSummary,
    TargetEvidenceSchema,
    DiscoveryJobStatus,
    DiscoveryJobCreate,
)

logger = logging.getLogger("fuzz_sentinel.routers.discovery")

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/targets",
    tags=["targets"],
    responses={404: {"description": "Not found"}},
)

# In-process job store (MVP: replace with Redis/Celery in production)
_JOBS: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# List targets
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[TargetSummary])
def list_targets(
    project_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    min_risk: float = Query(0.0, ge=0.0, le=10.0),
    status: Optional[str] = None,
    sort_by: str = Query("risk_score", pattern="^(risk_score|confidence|name|created_at)$"),
    db: Session = Depends(get_db),
):
    _require_project(project_id, db)
    q = db.query(models.Target).filter(models.Target.project_id == project_id)
    if min_risk > 0:
        q = q.filter(models.Target.risk_score >= min_risk)
    if status:
        q = q.filter(models.Target.status == status)
    if sort_by == "risk_score":
        q = q.order_by(models.Target.risk_score.desc())
    elif sort_by == "confidence":
        q = q.order_by(models.Target.confidence.desc())
    elif sort_by == "name":
        q = q.order_by(models.Target.name.asc())
    else:
        q = q.order_by(models.Target.created_at.desc())
    return q.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# Get single target with full evidence
# ---------------------------------------------------------------------------
@router.get("/{target_id}", response_model=TargetDetail)
def get_target(project_id: int, target_id: int, db: Session = Depends(get_db)):
    _require_project(project_id, db)
    target = _require_target(project_id, target_id, db)
    evidence = (
        db.query(models.TargetEvidence)
        .filter(models.TargetEvidence.target_id == target_id)
        .first()
    )
    return TargetDetail(
        id=target.id,
        project_id=target.project_id,
        name=target.name,
        module=target.module,
        address=target.address,
        address_kind=target.address_kind if hasattr(target, 'address_kind') else ("inferred" if target.address else None),
        source_file=target.source_file,
        source_line=target.source_line,
        input_type=target.input_type,
        risk_score=target.risk_score,
        confidence=target.confidence,
        status=target.status,
        created_at=target.created_at,
        updated_at=target.updated_at,
        risk_reasons=evidence.risk_reasons if evidence else [],
        attacker_controlled_inputs=evidence.attacker_controlled_inputs if evidence else [],
        memory_operations=evidence.memory_operations if evidence else {},
        call_path=[],       # Populated when CallGraphAnalyzer is available
        dependencies=[],
        suggested_harness_type="file_reader",
    )


# ---------------------------------------------------------------------------
# Evidence records for a target
# ---------------------------------------------------------------------------
@router.get("/{target_id}/evidence", response_model=List[TargetEvidenceSchema])
def get_target_evidence(project_id: int, target_id: int, db: Session = Depends(get_db)):
    _require_project(project_id, db)
    _require_target(project_id, target_id, db)
    records = (
        db.query(models.EvidenceRecord)
        .filter(
            models.EvidenceRecord.project_id == project_id,
            models.EvidenceRecord.entity_type == "target",
            models.EvidenceRecord.entity_id == target_id,
        )
        .order_by(models.EvidenceRecord.timestamp.desc())
        .all()
    )
    return [
        TargetEvidenceSchema(
            id=r.id,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            hash=r.hash,
            payload=r.payload,
            timestamp=r.timestamp,
        )
        for r in records
    ]


# ---------------------------------------------------------------------------
# Trigger source analysis (upload zip)
# ---------------------------------------------------------------------------
@router.post("/discover/source", response_model=DiscoveryJobStatus)
async def discover_from_source(
    project_id: int,
    background_tasks: BackgroundTasks,
    source_zip: UploadFile = File(..., description="ZIP archive of C/C++ source files"),
    min_score: float = Form(1.0, ge=0.0, le=10.0),
    db: Session = Depends(get_db),
):
    """
    Upload a ZIP of source files and start a target discovery analysis.
    Returns a job ID. Poll /discover/status/{job_id} for progress.
    """
    _require_project(project_id, db)

    if not source_zip.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip archives are accepted")

    content = await source_zip.read()
    if len(content) > 100 * 1024 * 1024:  # 100 MB cap
        raise HTTPException(413, "Archive exceeds 100 MB limit")

    import uuid
    job_id = str(uuid.uuid4())
    _JOBS[job_id] = {"status": "pending", "progress": 0.0, "message": "Queued", "result": None, "error": None}

    # Extract zip to temp dir that persists for the background task
    tmp_dir = tempfile.mkdtemp(prefix="fuzz_sentinel_src_")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Security: prevent path traversal in zip entries
            for member in zf.namelist():
                member_path = Path(tmp_dir) / member
                if not str(member_path.resolve()).startswith(str(Path(tmp_dir).resolve())):
                    raise HTTPException(400, f"Unsafe zip entry: {member}")
            zf.extractall(tmp_dir)
    except zipfile.BadZipFile:
        raise HTTPException(400, "Invalid ZIP archive")

    background_tasks.add_task(
        _run_analysis_job, job_id, project_id, Path(tmp_dir), min_score
    )

    return DiscoveryJobStatus(
        job_id=job_id,
        status="pending",
        progress=0.0,
        message="Analysis job queued",
        result=None,
        error=None,
    )


@router.get("/discover/status/{job_id}", response_model=DiscoveryJobStatus)
def get_discovery_status(project_id: int, job_id: str, db: Session = Depends(get_db)):
    if job_id not in _JOBS:
        raise HTTPException(404, f"Job {job_id} not found")
    j = _JOBS[job_id]
    return DiscoveryJobStatus(
        job_id=job_id,
        status=j["status"],
        progress=j["progress"],
        message=j["message"],
        result=j["result"],
        error=j["error"],
    )


# ---------------------------------------------------------------------------
# Delete a target
# ---------------------------------------------------------------------------
@router.delete("/{target_id}", status_code=204)
def delete_target(project_id: int, target_id: int, db: Session = Depends(get_db)):
    _require_project(project_id, db)
    target = _require_target(project_id, target_id, db)
    db.delete(target)
    db.commit()


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


def _run_analysis_job(job_id: str, project_id: int, source_root: Path, min_score: float):
    """Background task: runs pipeline and updates job status dict."""
    from ..database import SessionLocal
    db = SessionLocal()
    try:
        def progress(msg: str, pct: float):
            _JOBS[job_id]["progress"] = pct
            _JOBS[job_id]["message"] = msg

        _JOBS[job_id]["status"] = "running"
        pipeline = AnalysisPipeline(db, project_id, progress_callback=progress)
        result = pipeline.run_source_analysis(source_root, min_score=min_score)
        _JOBS[job_id]["status"] = "complete"
        _JOBS[job_id]["result"] = result
    except Exception as exc:
        logger.error(f"Analysis job {job_id} failed: {exc}", exc_info=True)
        _JOBS[job_id]["status"] = "error"
        _JOBS[job_id]["error"] = str(exc)
    finally:
        db.close()
        import shutil
        shutil.rmtree(source_root, ignore_errors=True)
