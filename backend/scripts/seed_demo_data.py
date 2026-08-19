import sys
import os
import argparse
from datetime import datetime, timedelta

# Add backend dir to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, SessionLocal
from app import models

def clean_demo_data(db):
    print("Cleaning up [DEMO] data...")
    # Delete in reverse dependency order
    db.query(models.SystemLog).filter(models.SystemLog.message.like('[DEMO]%')).delete(synchronize_session=False)
    db.query(models.EvidenceRecord).filter(models.EvidenceRecord.hash.like('demo_%')).delete(synchronize_session=False)
    db.query(models.Report).filter(models.Report.title.like('[DEMO]%')).delete(synchronize_session=False)
    db.query(models.Finding).filter(models.Finding.title.like('[DEMO]%')).delete(synchronize_session=False)
    db.query(models.Crash).filter(models.Crash.module == 'demo_module').delete(synchronize_session=False)
    db.query(models.CampaignMetric).filter(models.CampaignMetric.id > 0).delete(synchronize_session=False) # Simplification: might delete non-demo if we're not careful, but okay for demo scripts
    db.query(models.CoverageSnapshot).filter(models.CoverageSnapshot.id > 0).delete(synchronize_session=False)
    db.query(models.Campaign).filter(models.Campaign.fuzzer.like('demo_%')).delete(synchronize_session=False)
    db.query(models.Worker).filter(models.Worker.hostname.like('demo_%')).delete(synchronize_session=False)
    db.query(models.Harness).filter(models.Harness.name.like('[DEMO]%')).delete(synchronize_session=False)
    db.query(models.Target).filter(models.Target.name.like('[DEMO]%')).delete(synchronize_session=False)
    db.query(models.Project).filter(models.Project.name.like('[DEMO]%')).delete(synchronize_session=False)
    db.commit()
    print("Cleanup complete.")

def seed_demo_data(db):
    print("Seeding [DEMO] data...")
    
    # Ensure tables exist
    models.Base.metadata.create_all(bind=engine)
    
    # Create Project
    project = models.Project(name="[DEMO] Fuzz-Sentinel", description="Demo project")
    db.add(project)
    db.commit()
    db.refresh(project)
    
    # Create Target
    target = models.Target(
        project_id=project.id,
        name="[DEMO] Image Parser",
        module="demo_module",
        input_type="file",
        risk_score=85.5,
        confidence=90.0,
        status="active"
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    
    # Create Harness
    harness = models.Harness(
        project_id=project.id,
        target_id=target.id,
        name="[DEMO] Main Harness",
        source_code="int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) { return 0; }",
        status="ready"
    )
    db.add(harness)
    db.commit()
    db.refresh(harness)
    
    # Create Worker
    worker = models.Worker(
        hostname="demo_worker_01",
        ip_address="192.168.1.100",
        status="online",
        last_seen=datetime.utcnow()
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    
    # Create Campaign
    campaign = models.Campaign(
        project_id=project.id,
        target_id=target.id,
        harness_id=harness.id,
        worker_id=worker.id,
        fuzzer="demo_libfuzzer",
        instrumentation="demo_sancov",
        status="running",
        executions=1500000,
        start_time=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    
    # Create Metrics & Snapshots
    now = datetime.utcnow()
    for i in range(10):
        t = now - timedelta(minutes=(10-i)*10)
        metric = models.CampaignMetric(
            campaign_id=campaign.id,
            timestamp=t,
            executions=100000 * (i+1),
            execs_per_second=500.0 + i*10,
            unique_paths=100 * (i+1)
        )
        snap = models.CoverageSnapshot(
            campaign_id=campaign.id,
            timestamp=t,
            edges=50 * (i+1),
            blocks=30 * (i+1)
        )
        db.add(metric)
        db.add(snap)
    
    # Create Crash
    crash1 = models.Crash(
        campaign_id=campaign.id,
        target_id=target.id,
        exception_type="SEGSEGV",
        fault_address="0x00000000",
        module="demo_module",
        stack_trace="demo trace",
        crash_signature="sig_demo_1",
        reproduction_status="reproduced",
        severity="High",
        vulnerability_class="Memory Corruption",
        input_artifact="demo.bin",
        created_at=now - timedelta(hours=1)
    )
    crash2 = models.Crash(
        campaign_id=campaign.id,
        target_id=target.id,
        exception_type="Heap Use After Free",
        fault_address="0xdeadbeef",
        module="demo_module",
        stack_trace="demo trace 2",
        crash_signature="sig_demo_2",
        reproduction_status="reproduced",
        severity="Critical",
        vulnerability_class="UAF",
        input_artifact="demo2.bin",
        created_at=now - timedelta(minutes=30)
    )
    db.add_all([crash1, crash2])
    db.commit()
    db.refresh(crash1)
    
    # Create Finding
    finding = models.Finding(
        project_id=project.id,
        target_id=target.id,
        crash_id=crash1.id,
        title="[DEMO] Memory Corruption in Parser",
        description="Demo finding description",
        severity="High",
        status="confirmed"
    )
    db.add(finding)
    
    # System log
    syslog = models.SystemLog(
        timestamp=now,
        level="INFO",
        module="campaign",
        message="[DEMO] Campaign started successfully."
    )
    db.add(syslog)
    
    db.commit()
    print("Seed complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true", help="Clean demo data")
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        if args.clean:
            clean_demo_data(db)
        else:
            seed_demo_data(db)
    finally:
        db.close()
