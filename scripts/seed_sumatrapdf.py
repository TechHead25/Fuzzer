import os
import sys

# Ensure backend directory is in path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.database import SessionLocal
from app import models

def seed_sumatra():
    db = SessionLocal()
    
    # 1. Create a Project
    project = models.Project(
        name="SumatraPDF Vulnerability Research",
        description="Fuzzing engagement targeting SumatraPDF v3.4.6 x64 and its underlying MuPDF parsing engine."
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    print(f"Created Project: {project.name} (ID: {project.id})")
    
    # 2. Create an Import Session simulating Ghidra + Source Analysis
    session = models.ImportSession(
        project_id=project.id,
        import_type="ghidra_json",
        filename="SumatraPDF_3.4.6_x64_Analysis.json",
        status="complete",
        targets_imported=4,
        result_summary={"architecture": "x64", "compiler": "MSVC", "version": "3.4.6"}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 3. Create Targets in DISCOVERED state (unverified)
    
    targets_data = [
        {
            "name": "pdf_parse_dict",
            "module": "libmupdf.dll",
            "address": "0x1800F12A0",
            "source_file": "mupdf/source/pdf/pdf-parse.c",
            "source_line": 245,
            "input_type": "binary",
            "risk_score": 92.5,
            "confidence": 85.0,
            "arguments": [
                {"name": "ctx", "type": "fz_context*", "is_attacker_controlled": False},
                {"name": "file", "type": "fz_stream*", "is_attacker_controlled": True},
                {"name": "buf", "type": "pdf_lexbuf*", "is_attacker_controlled": False}
            ],
            "call_path": [
                {"caller": "pdf_open_document", "callee": "pdf_init_document", "evidence_kind": "call_graph"},
                {"caller": "pdf_init_document", "callee": "pdf_parse_dict", "evidence_kind": "source_analysis"}
            ],
            "dependencies": ["zlib", "freetype"],
            "analyst_notes": "Candidate identified via source analysis. Contains heavy pointer arithmetic and recursive object parsing."
        },
        {
            "name": "fz_parse_epub",
            "module": "libmupdf.dll",
            "address": "0x18012B450",
            "source_file": "mupdf/source/fitz/document.c",
            "source_line": 841,
            "input_type": "file",
            "risk_score": 88.0,
            "confidence": 75.0,
            "arguments": [
                {"name": "ctx", "type": "fz_context*", "is_attacker_controlled": False},
                {"name": "filename", "type": "const char*", "is_attacker_controlled": True}
            ],
            "call_path": [
                {"caller": "fz_open_document", "callee": "fz_parse_epub", "evidence_kind": "ghidra_export"}
            ],
            "dependencies": ["libzip"],
            "analyst_notes": "EPUB parser entry point. Reads highly structured XML. XML parser could be vulnerable to deeply nested entities."
        },
        {
            "name": "xps_parse_part",
            "module": "libmupdf.dll",
            "address": "0x1801A9900",
            "source_file": "mupdf/source/xps/xps-doc.c",
            "source_line": 134,
            "input_type": "binary",
            "risk_score": 75.0,
            "confidence": 90.0,
            "arguments": [
                {"name": "ctx", "type": "fz_context*", "is_attacker_controlled": False},
                {"name": "doc", "type": "xps_document*", "is_attacker_controlled": False},
                {"name": "part", "type": "fz_archive*", "is_attacker_controlled": True}
            ],
            "call_path": [
                {"caller": "xps_open_document", "callee": "xps_parse_part", "evidence_kind": "call_graph"}
            ],
            "dependencies": ["libjpeg"],
            "analyst_notes": "Parses XPS parts. Known historical attack surface."
        },
        {
            "name": "ParsePdfString",
            "module": "SumatraPDF.exe",
            "address": "0x0040A560",
            "source_file": "src/PdfParser.cpp",
            "source_line": 512,
            "input_type": "binary",
            "risk_score": 60.5,
            "confidence": 50.0,
            "arguments": [
                {"name": "buf", "type": "const char*", "is_attacker_controlled": True},
                {"name": "len", "type": "size_t", "is_attacker_controlled": True}
            ],
            "call_path": [],
            "dependencies": [],
            "analyst_notes": "Custom string parser wrapper in the SumatraPDF UI code."
        }
    ]
    
    for t_data in targets_data:
        target = models.Target(
            project_id=project.id,
            name=t_data["name"],
            module=t_data["module"],
            address=t_data["address"],
            source_file=t_data["source_file"],
            source_line=t_data["source_line"],
            input_type=t_data["input_type"],
            risk_score=t_data["risk_score"],
            confidence=t_data["confidence"],
            arguments=t_data["arguments"],
            call_path=t_data["call_path"],
            dependencies=t_data["dependencies"],
            status="DISCOVERED",
            import_source="ghidra_json",
            import_session_id=session.id,
            analyst_notes=t_data["analyst_notes"]
        )
        db.add(target)
    
    db.commit()
    print("Injected 4 SumatraPDF candidate targets into DISCOVERED state.")
    db.close()

if __name__ == "__main__":
    seed_sumatra()
