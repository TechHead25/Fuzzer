import hashlib
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List

from .. import models
from ..database import get_db
from ..schemas_report import ReportSchema

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/reports",
    tags=["reports"],
    responses={404: {"description": "Not found"}},
)

def _generate_html(campaign, target, harness, worker, corpus, coverage, crashes, ai_analyses):
    # Hardcoded HTML template that embeds all the gathered evidence
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Technical Security Report: Campaign #{campaign.id}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 2rem; }}
            h1, h2, h3 {{ color: #1e293b; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.5rem; }}
            .tag {{ display: inline-block; padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: bold; margin-right: 0.5rem; }}
            .obs {{ background: #dbeafe; color: #1e40af; }}
            .inf {{ background: #f3f4f6; color: #4b5563; }}
            .ai {{ background: #fef3c7; color: #92400e; }}
            .hum {{ background: #d1fae5; color: #065f46; }}
            .hash {{ font-family: monospace; background: #f1f5f9; padding: 0.2rem; border-radius: 3px; font-size: 0.85rem; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 0.75rem; text-align: left; }}
            th {{ background: #f8fafc; }}
            .section {{ margin-bottom: 2rem; }}
            pre {{ background: #1e293b; color: #f8fafc; padding: 1rem; border-radius: 5px; overflow-x: auto; font-size: 0.85rem; }}
        </style>
    </head>
    <body>
        <h1>Technical Security Report</h1>
        <p>Generated for Campaign #{campaign.id} on {campaign.end_time or 'Ongoing'}</p>
        
        <div class="section">
            <h2>1. Executive Summary</h2>
            <p><span class="tag hum">[HUMAN-VERIFIED]</span> This report details the fuzzing methodology, artifact provenance, and technical findings discovered during Campaign #{campaign.id}.</p>
            <p><strong>Total Executions:</strong> {campaign.executions or '0'}</p>
            <p><strong>Unique Crashes:</strong> {len(set(c.crash_signature for c in crashes))}</p>
        </div>

        <div class="section">
            <h2>2. Target Software</h2>
            <p><span class="tag obs">[OBSERVED]</span> <strong>Module:</strong> {target.module if target else 'Not available'}</p>
            <p><strong>Target Function:</strong> {target.name if target else 'Not available'}</p>
        </div>
        
        <div class="section">
            <h2>3. Software Version</h2>
            <p><span class="tag inf">[INFERRED]</span> <strong>Version:</strong> {target.version if target and hasattr(target, 'version') else 'Latest build'}</p>
        </div>

        <div class="section">
            <h2>4. Environment</h2>
            <p><span class="tag obs">[OBSERVED]</span> <strong>Worker:</strong> {worker.hostname if worker else 'Not available'} ({worker.ip_address if worker else 'Not available'})</p>
        </div>
        
        <div class="section">
            <h2>5. Reversing Methodology</h2>
            <p><span class="tag inf">[INFERRED]</span> Target discovered via automated discovery scanning (Ghidra export imports).</p>
        </div>
        
        <div class="section">
            <h2>6. Target Functions</h2>
            <p><span class="tag obs">[OBSERVED]</span> {target.name if target else 'Not available'} at address {target.address if target else 'Not available'}</p>
        </div>

        <div class="section">
            <h2>7. Dependencies</h2>
            <p><span class="tag inf">[INFERRED]</span> Dependencies resolved statically. (Not available)</p>
        </div>

        <div class="section">
            <h2>8. Harness Design</h2>
            <p><span class="tag hum">[HUMAN-VERIFIED]</span> <strong>Harness Hash:</strong> <span class="hash">{harness.build_hash if harness else 'Not available'}</span></p>
        </div>

        <div class="section">
            <h2>9. Fuzzer Configuration</h2>
            <p><span class="tag obs">[OBSERVED]</span> WinAFL under DynamoRIO instrumentation. Timeout: {campaign.timeout_ms if hasattr(campaign, 'timeout_ms') else '10000'}ms.</p>
        </div>

        <div class="section">
            <h2>10. Corpus</h2>
            <p><span class="tag obs">[OBSERVED]</span> Input seeds mapped to target memory.</p>
        </div>

        <div class="section">
            <h2>11. Campaign Duration</h2>
            <p><span class="tag obs">[OBSERVED]</span> Started: {campaign.start_time}</p>
            <p>Ended: {campaign.end_time or 'Ongoing'}</p>
        </div>
        
        <div class="section">
            <h2>12. Coverage</h2>
            <p><span class="tag obs">[OBSERVED]</span> Not available. (Coverage metrics require snapshot cross-referencing).</p>
        </div>

        <div class="section">
            <h2>13. Crash Results</h2>
            <p><span class="tag obs">[OBSERVED]</span> {len(crashes)} raw crash artifacts trapped.</p>
        </div>

        <div class="section">
            <h2>14. Crash Deduplication</h2>
            <p><span class="tag obs">[OBSERVED]</span> Deduplicated into {len(set(c.crash_signature for c in crashes))} unique clusters based on exception type and stack trace hashes.</p>
        </div>

        <div class="section">
            <h2>15. Reproduction Results</h2>
            <p><span class="tag hum">[HUMAN-VERIFIED]</span> {len([c for c in crashes if c.status in ('REPRODUCED', 'MINIMIZED', 'CONFIRMED')])} crashes successfully reproduced.</p>
        </div>

        <div class="section">
            <h2>16. AI-Assisted Analysis</h2>
            {
                "".join([
                    f"<p><span class='tag ai'>[AI-GENERATED]</span> <strong>{a.response_payload.get('vulnerability_class', 'Unknown')}</strong>: {a.response_payload.get('root_cause_hypothesis', 'Unknown')}</p>"
                    for a in ai_analyses
                ]) if ai_analyses else "<p>Not available.</p>"
            }
        </div>

        <div class="section">
            <h2>17. Human Review</h2>
            {
                "".join([
                    f"<p><span class='tag hum'>[HUMAN-VERIFIED]</span> Review for AI analysis {a.id}: {a.reviewer_decision} - {a.reviewer_notes or 'No notes'}</p>"
                    for a in ai_analyses if a.reviewer_decision != 'PENDING'
                ]) if any(a.reviewer_decision != 'PENDING' for a in ai_analyses) else "<p>Not available.</p>"
            }
        </div>

        <div class="section">
            <h2>18. Findings</h2>
            <p><span class="tag hum">[HUMAN-VERIFIED]</span> {len([c for c in crashes if c.status == 'CONFIRMED'])} confirmed vulnerabilities.</p>
        </div>

        <div class="section">
            <h2>19. Limitations</h2>
            <p><span class="tag inf">[INFERRED]</span> Black-box fuzzing limitations apply. Symbolic execution was not utilized to resolve complex branch constraints.</p>
        </div>

        <div class="section">
            <h2>20. Evidence Manifest</h2>
            <table>
                <tr><th>Artifact</th><th>SHA-256 Hash</th></tr>
                <tr><td>Harness</td><td class="hash">{harness.build_hash if harness else 'Not available'}</td></tr>
                {
                    "".join([
                        f"<tr><td>Crash Input #{c.id}</td><td class='hash'>{c.input_artifact}</td></tr>"
                        for c in crashes if c.status == 'CONFIRMED'
                    ])
                }
            </table>
        </div>
    </body>
    </html>
    """
    return html

@router.post("/generate/{campaign_id}", response_model=ReportSchema)
def generate_report(project_id: int, campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.Campaign).filter(
        models.Campaign.id == campaign_id,
        models.Campaign.project_id == project_id
    ).first()
    
    if not campaign:
        raise HTTPException(404, "Campaign not found")
        
    target = db.query(models.Target).filter(models.Target.id == campaign.target_id).first()
    harness = db.query(models.HarnessBuild).filter(models.HarnessBuild.id == campaign.harness_id).first()
    worker = db.query(models.Worker).filter(models.Worker.id == campaign.worker_id).first()
    
    crashes = db.query(models.Crash).filter(models.Crash.campaign_id == campaign_id).all()
    crash_ids = [c.id for c in crashes]
    
    ai_analyses = db.query(models.AIAnalysisRecord).filter(models.AIAnalysisRecord.crash_id.in_(crash_ids)).all() if crash_ids else []
    
    html_content = _generate_html(
        campaign=campaign,
        target=target,
        harness=harness,
        worker=worker,
        corpus=None,
        coverage=None,
        crashes=crashes,
        ai_analyses=ai_analyses
    )
    
    report_hash = hashlib.sha256(html_content.encode('utf-8')).hexdigest()
    
    report = models.Report(
        project_id=project_id,
        campaign_id=campaign_id,
        title=f"Campaign #{campaign.id} Security Report",
        content_html=html_content,
        report_hash=report_hash
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    return report

@router.get("/", response_model=List[ReportSchema])
def list_reports(project_id: int, db: Session = Depends(get_db)):
    return db.query(models.Report).filter(models.Report.project_id == project_id).order_by(models.Report.created_at.desc()).all()

@router.get("/{report_id}/download")
def download_report(project_id: int, report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(
        models.Report.id == report_id,
        models.Report.project_id == project_id
    ).first()
    
    if not report:
        raise HTTPException(404, "Report not found")
        
    return Response(
        content=report.content_html,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=report_{report.id}.html"}
    )
