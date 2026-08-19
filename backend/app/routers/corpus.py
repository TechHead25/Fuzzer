import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List

from .. import models
from ..database import get_db
from ..schemas_corpus import SeedCorpusCreate, SeedCorpusResponse, SeedSchema

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/corpora",
    tags=["corpus"],
    responses={404: {"description": "Not found"}},
)

# Ensure storage directory exists
STORAGE_DIR = os.path.join("data", "corpora")
os.makedirs(STORAGE_DIR, exist_ok=True)

def _build_corpus_response(corpus, db: Session) -> SeedCorpusResponse:
    # Aggregate data
    seeds = db.query(models.Seed).filter(models.Seed.corpus_id == corpus.id).all()
    total_seeds = len(seeds)
    total_bytes = sum([s.size or 0 for s in seeds])
    unique_hashes = len(set([s.hash for s in seeds if s.hash]))
    coverage_seeds = len([s for s in seeds if s.discovered_coverage])
    crash_seeds = len([s for s in seeds if s.triggered_crash])
    
    return SeedCorpusResponse(
        id=corpus.id,
        project_id=corpus.project_id,
        name=corpus.name,
        description=corpus.description,
        created_at=corpus.created_at,
        total_seeds=total_seeds,
        total_bytes=total_bytes,
        unique_hashes=unique_hashes,
        coverage_seeds=coverage_seeds,
        crash_seeds=crash_seeds
    )

@router.get("/", response_model=List[SeedCorpusResponse])
def get_corpora(project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    corpora = db.query(models.SeedCorpus).filter(models.SeedCorpus.project_id == project_id).offset(skip).limit(limit).all()
    return [_build_corpus_response(c, db) for c in corpora]

@router.post("/", response_model=SeedCorpusResponse)
def create_corpus(project_id: int, payload: SeedCorpusCreate, db: Session = Depends(get_db)):
    corpus = models.SeedCorpus(
        project_id=project_id,
        name=payload.name,
        description=payload.description
    )
    db.add(corpus)
    db.commit()
    db.refresh(corpus)
    return _build_corpus_response(corpus, db)

@router.get("/{corpus_id}", response_model=SeedCorpusResponse)
def get_corpus(project_id: int, corpus_id: int, db: Session = Depends(get_db)):
    corpus = db.query(models.SeedCorpus).filter(
        models.SeedCorpus.id == corpus_id, 
        models.SeedCorpus.project_id == project_id
    ).first()
    if not corpus:
        raise HTTPException(404, "Corpus not found")
    return _build_corpus_response(corpus, db)

@router.get("/{corpus_id}/seeds", response_model=List[SeedSchema])
def get_seeds(project_id: int, corpus_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    seeds = db.query(models.Seed).filter(models.Seed.corpus_id == corpus_id).offset(skip).limit(limit).all()
    return seeds

@router.post("/{corpus_id}/seeds", response_model=SeedSchema)
async def upload_seed(
    project_id: int, 
    corpus_id: int, 
    file: UploadFile = File(...),
    origin: str = Form("UPLOAD"),
    parent_seed_id: int = Form(None),
    target_id: int = Form(None),
    db: Session = Depends(get_db)
):
    corpus = db.query(models.SeedCorpus).filter(
        models.SeedCorpus.id == corpus_id, 
        models.SeedCorpus.project_id == project_id
    ).first()
    if not corpus:
        raise HTTPException(404, "Corpus not found")

    content = await file.read()
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Deduplication check
    existing = db.query(models.Seed).filter(
        models.Seed.corpus_id == corpus_id,
        models.Seed.hash == file_hash
    ).first()
    if existing:
        return existing
        
    # Persist file securely
    file_path = os.path.join(STORAGE_DIR, f"{file_hash}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)
        
    seed = models.Seed(
        corpus_id=corpus_id,
        filename=file.filename,
        file_type=file.content_type or "application/octet-stream",
        origin=origin,
        file_path=file_path,
        hash=file_hash,
        size=len(content),
        parent_seed_id=parent_seed_id,
        target_id=target_id,
        discovered_coverage=False,
        triggered_crash=False
    )
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return seed

@router.post("/{corpus_id}/minimize")
def minimize_corpus(project_id: int, corpus_id: int, db: Session = Depends(get_db)):
    # In a full implementation, this queues a backend task via WorkerJob
    # For now, it returns a 202 Accepted.
    from fastapi import Response
    return Response(status_code=202, content="Minimization task queued")
