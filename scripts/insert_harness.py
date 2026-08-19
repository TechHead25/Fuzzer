import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.database import SessionLocal
from app import models

def save_harness():
    db = SessionLocal()
    
    harness = models.Harness(
        project_id=1,
        target_id=2,
        name="fz_parse_epub_harness",
        engine="winafl",
        input_type="file",
        status="READY_FOR_FUZZING"
    )
    db.add(harness)
    db.commit()
    db.refresh(harness)
    
    build = models.HarnessBuild(
        harness_id=harness.id,
        compiler="g++ (Rev3, Built by MSYS2 project) 14.1.0",
        compiler_version="14.1.0",
        architecture="x64",
        build_command="g++ mupdf_mock.c harness.cpp -o harness.exe -O2",
        stdout="Building SumatraPDF EPUB Harness...\nCompiling mupdf_mock.c and harness.cpp with g++...\nBuild complete! Output is in harness.exe",
        stderr="[Mock] fz_parse_epub hit! Parsing file: test.epub\nVALIDATION SUCCESS: Harness executed cleanly.",
        status="VALIDATED",
        hash="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    )
    db.add(build)
    
    # Update target state to HARNESS_READY
    target = db.query(models.Target).filter_by(id=2).first()
    target.status = "HARNESS_READY"
    
    db.commit()
    print("Harness successfully registered in database.")

if __name__ == "__main__":
    save_harness()
