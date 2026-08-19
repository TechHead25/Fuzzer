import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, projects, targets, harnesses, campaigns, crashes, findings, reports, evidence, dashboard, discovery, workspace, workers, corpus, coverage, ai

# Structured Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("fuzz_sentinel")

app = FastAPI(title="Fuzz-Sentinel API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred.", "details": str(exc)},
    )

# Include Routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(targets.router)
app.include_router(harnesses.router)
app.include_router(campaigns.router)
app.include_router(crashes.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(evidence.router)
app.include_router(dashboard.router)
app.include_router(discovery.router)
app.include_router(workspace.router)
app.include_router(workers.router)
app.include_router(corpus.router)
app.include_router(coverage.router)
app.include_router(ai.router)

logger.info("Fuzz-Sentinel Backend Application Started")
