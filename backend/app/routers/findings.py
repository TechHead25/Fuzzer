from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/findings",
    tags=["findings"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=List[schemas.Finding])
def read_findings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Finding).offset(skip).limit(limit).all()
