"""
Fuzz-Sentinel Analysis Engine: Pipeline Orchestrator
====================================================
Coordinates SourceAnalyzer → TargetScorer → database persistence.
Designed to run synchronously (for small trees) or in a background thread.
"""

import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from sqlalchemy.orm import Session

from .analyzers import SourceAnalyzer
from .scorer import TargetScorer
from .types import DiscoveredTarget, EvidenceKind
from ..models import Target, TargetEvidence, EvidenceRecord, SystemLog

logger = logging.getLogger("fuzz_sentinel.analysis.pipeline")


class AnalysisPipeline:
    """
    Orchestrates the full target-discovery pipeline:
      1. SourceAnalyzer  – find candidate functions
      2. TargetScorer    – compute explainable risk scores
      3. DB persistence  – save results, evidence records, system logs

    progress_callback(message: str, pct: float) is optional; called during
    long scans to report progress to the caller.
    """

    def __init__(
        self,
        db: Session,
        project_id: int,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ):
        self.db = db
        self.project_id = project_id
        self.progress = progress_callback or (lambda msg, pct: None)

    def run_source_analysis(
        self,
        source_root: Path,
        min_score: float = 1.0,
    ) -> dict:
        """
        Full pipeline run on a source tree.
        Returns a summary dict with counts.
        """
        self._log(f"Starting source analysis on {source_root}")
        self.progress("Scanning source files…", 0.05)

        analyzer = SourceAnalyzer()
        scorer   = TargetScorer()

        raw_targets = analyzer.analyze(source_root, self.project_id)
        self.progress(f"Found {len(raw_targets)} candidate functions", 0.40)

        scored = []
        for t in raw_targets:
            scored.append(scorer.score(t))

        # Filter by minimum score
        filtered = [t for t in scored if t.risk_score >= min_score]
        filtered.sort(key=lambda t: t.risk_score, reverse=True)
        self.progress(f"Scored {len(filtered)} targets above threshold {min_score}", 0.70)

        # Persist
        saved = 0
        for discovered in filtered:
            try:
                self._persist_target(discovered)
                saved += 1
            except Exception as exc:
                logger.error(f"Failed to save target {discovered.function_name}: {exc}")

        self.db.commit()
        self.progress("Analysis complete", 1.0)
        self._log(f"Source analysis complete: {saved} targets saved to database")

        return {
            "files_scanned": "see logs",
            "candidates_found": len(raw_targets),
            "above_threshold": len(filtered),
            "saved_to_db": saved,
            "min_score": min_score,
        }

    def _persist_target(self, discovered: DiscoveredTarget) -> None:
        reasons_payload = [
            {
                "indicator": r.indicator,
                "description": r.description,
                "weight": r.weight,
                "evidence_kind": r.evidence_kind.value,
                "source_ref": r.source_ref,
            }
            for r in discovered.reasons
        ]

        # Upsert: if same project+function+module already exists, update
        existing = (
            self.db.query(Target)
            .filter(
                Target.project_id == self.project_id,
                Target.name == discovered.function_name,
                Target.module == discovered.module,
            )
            .first()
        )

        if existing:
            existing.risk_score   = discovered.risk_score
            existing.confidence   = discovered.confidence
            existing.status       = "analyzed"
            existing.source_file  = discovered.source_file
            existing.source_line  = discovered.source_line
            existing.address      = discovered.address
            existing.input_type   = discovered.input_type
            existing.updated_at   = datetime.utcnow()
            db_target = existing
        else:
            db_target = Target(
                project_id=self.project_id,
                name=discovered.function_name,
                module=discovered.module,
                address=discovered.address,
                source_file=discovered.source_file,
                source_line=discovered.source_line,
                input_type=discovered.input_type,
                risk_score=discovered.risk_score,
                confidence=discovered.confidence,
                status="analyzed",
            )
            self.db.add(db_target)
            self.db.flush()  # get the ID

        # Evidence record (TargetEvidence)
        evidence = (
            self.db.query(TargetEvidence)
            .filter(TargetEvidence.target_id == db_target.id)
            .first()
        )
        attacker_params = [
            {"name": p.name, "type": p.param_type}
            for p in discovered.parameters if p.is_attacker_controlled
        ]
        mem_ops = {
            k: v for k, v in discovered.raw_indicators.items()
            if k in ("memcpy_call", "buffer_write", "buffer_read", "heap_allocation")
        }
        if evidence:
            evidence.risk_reasons              = reasons_payload
            evidence.attacker_controlled_inputs = attacker_params
            evidence.memory_operations         = mem_ops
        else:
            self.db.add(TargetEvidence(
                target_id=db_target.id,
                risk_reasons=reasons_payload,
                attacker_controlled_inputs=attacker_params,
                memory_operations=mem_ops,
            ))

        # Immutable evidence record (hash of the finding)
        payload = {
            "function": discovered.function_name,
            "module": discovered.module,
            "source_file": discovered.source_file,
            "source_line": discovered.source_line,
            "risk_score": discovered.risk_score,
            "confidence": discovered.confidence,
            "address_kind": discovered.address_kind.value,
            "reasons": reasons_payload,
            "analyzed_at": discovered.analyzed_at.isoformat(),
        }
        payload_json = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()

        self.db.add(EvidenceRecord(
            project_id=self.project_id,
            entity_type="target",
            entity_id=db_target.id,
            hash=payload_hash,
            payload=payload,
        ))

    def _log(self, message: str) -> None:
        logger.info(message)
        self.db.add(SystemLog(
            level="INFO",
            module="analysis.pipeline",
            message=message,
            metadata_={"project_id": self.project_id},
        ))
        self.db.flush()
