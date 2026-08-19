from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from .. import schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)

@router.get("/", response_model=schemas.DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    # Query real database for stats
    active_campaigns = db.query(models.Campaign).filter(models.Campaign.status == 'running').count()
    
    # Get aggregated metrics from the latest campaign metrics
    total_executions = db.query(func.coalesce(func.sum(models.Campaign.executions), 0)).scalar() or 0
    
    # Get latest exec speed from most recent metric
    latest_metric = db.query(models.CampaignMetric).order_by(models.CampaignMetric.timestamp.desc()).first()
    execs_per_second = latest_metric.execs_per_second if latest_metric else 0.0
    unique_paths = latest_metric.unique_paths if latest_metric else 0
    
    # Coverage from latest snapshot
    latest_coverage = db.query(models.CoverageSnapshot).order_by(models.CoverageSnapshot.timestamp.desc()).first()
    coverage_percent = 0.0  # Real coverage requires baseline; show 0 until we have data
    
    # Crash counts
    raw_crashes = db.query(models.Crash).count()
    unique_signatures = db.query(func.count(func.distinct(models.Crash.crash_signature))).scalar() or 0
    
    # Findings
    confirmed_findings = db.query(models.Finding).filter(models.Finding.status == 'confirmed').count()
    
    # Targets & Workers
    total_targets = db.query(models.Target).count()
    total_workers = db.query(models.Worker).count()
    online_workers = db.query(models.Worker).filter(models.Worker.status == 'online').count()
    
    stats = schemas.DashboardStats(
        active_campaigns=active_campaigns,
        total_executions=int(total_executions),
        execs_per_second=execs_per_second,
        unique_paths=unique_paths,
        coverage_percent=coverage_percent,
        raw_crashes=raw_crashes,
        unique_crashes=unique_signatures,
        confirmed_findings=confirmed_findings,
        total_targets=total_targets,
        total_workers=total_workers,
        online_workers=online_workers,
    )
    
    # Workers list
    workers = db.query(models.Worker).all()
    
    # Recent activity from system logs (last 20)
    recent_logs = db.query(models.SystemLog).order_by(models.SystemLog.timestamp.desc()).limit(20).all()
    recent_activity = [
        schemas.RecentActivity(
            id=log.id,
            entity_type=log.module or 'system',
            entity_id=log.id,
            message=log.message,
            timestamp=log.timestamp,
        )
        for log in recent_logs
    ]
    
    # Coverage trend from snapshots
    coverage_snapshots = db.query(models.CoverageSnapshot).order_by(models.CoverageSnapshot.timestamp.asc()).limit(100).all()
    coverage_trend = [
        schemas.CoverageTrendPoint(
            timestamp=snap.timestamp.isoformat() if snap.timestamp else '',
            edges=snap.edges or 0,
            blocks=snap.blocks or 0,
        )
        for snap in coverage_snapshots
    ]
    
    # Execution trend from metrics
    exec_metrics = db.query(models.CampaignMetric).order_by(models.CampaignMetric.timestamp.asc()).limit(100).all()
    execution_trend = [
        schemas.ExecutionTrendPoint(
            timestamp=m.timestamp.isoformat() if m.timestamp else '',
            executions=m.executions or 0,
            execs_per_second=m.execs_per_second or 0.0,
        )
        for m in exec_metrics
    ]
    
    # Crash trend - group crashes by date
    crashes = db.query(models.Crash).order_by(models.Crash.created_at.asc()).all()
    crash_trend_map = {}
    running_total = 0
    seen_sigs = set()
    for crash in crashes:
        date_key = crash.created_at.strftime('%Y-%m-%d') if crash.created_at else 'unknown'
        running_total += 1
        seen_sigs.add(crash.crash_signature)
        crash_trend_map[date_key] = schemas.CrashTrendPoint(
            timestamp=date_key,
            total_crashes=running_total,
            unique_crashes=len(seen_sigs),
        )
    crash_trend = list(crash_trend_map.values())
    
    # Target risk distribution
    targets = db.query(models.Target).order_by(models.Target.risk_score.desc()).limit(20).all()
    target_risk = [
        schemas.TargetRiskItem(
            name=t.name,
            module=t.module,
            risk_score=t.risk_score,
            status=t.status,
        )
        for t in targets
    ]
    
    # Active campaigns list
    active_campaigns_list = db.query(models.Campaign).filter(
        models.Campaign.status.in_(['running', 'starting', 'paused'])
    ).all()
    
    return schemas.DashboardResponse(
        stats=stats,
        workers=[schemas.WorkerStatus.model_validate(w) for w in workers],
        recent_activity=recent_activity,
        coverage_trend=coverage_trend,
        execution_trend=execution_trend,
        crash_trend=crash_trend,
        target_risk_distribution=target_risk,
        active_campaigns_list=active_campaigns_list,
    )
