# Product Requirements Document (PRD)

## 1. Project Overview

- **Project Name:** Fuzz-Sentinel
- **Purpose:** An enterprise-grade, intelligent continuous fuzzing and security assurance platform engineered for native Windows targets and complex document/binary parsers.
- **Problem Being Solved:** Fuzzing native Windows software is historically brittle, difficult to orchestrate, and suffers from poor visibility. WinAFL and DynamoRIO setups often fail due to subtle ABI incompatibilities, process-management mismatches, undocumented persistence requirements, and non-deterministic harness loops. Fuzz-Sentinel unifies target discovery, automated harness generation, high-performance binary instrumentation (WinAFL / DynamoRIO / TinyInst), telemetry capture, and cryptographic evidence ledger reporting into an end-to-end security operations suite.
- **Goals:**
  1. Provide unified web UI (Next.js) and API backend (FastAPI) for orchestrating campaigns, visualizing live coverage trends, and triaging findings.
  2. Deliver native fuzzing integration via Python workers leveraging WinAFL, DynamoRIO, and custom in-process persistence harnesses.
  3. Support real-world binary targets including document processors (e.g., SumatraPDF / MuPDF).
  4. Ensure end-to-end auditability and integrity: distinguish verified execution findings from AI triage inferences with cryptographic proof.
- **Non-Goals:**
  1. Replacing low-level binary instrumentors with purely proprietary engines (WinAFL/DynamoRIO are leveraged and extended directly).
  2. Replacing human analyst verification in high-risk environments (AI provides triage assistance, never unilateral finding confirmation).

---

## 2. Current System Architecture

```text
+-----------------------------------------------------------------------------+
|                               Developer / Analyst                           |
|                         (Web UI - Next.js App Router)                       |
+---------------------------------------+-------------------------------------+
                                        | HTTP / REST API
                                        v
+-----------------------------------------------------------------------------+
|                         Fuzz-Sentinel Backend (FastAPI)                     |
|  - Campaign Orchestration     - Evidence Ledger       - Target Discovery    |
|  - Coverage Aggregator        - AI Triage Pipeline    - SQLite / PostgreSQL |
+---------------------------------------+-------------------------------------+
                                        | REST / Heartbeat / Task Queue
                                        v
+-----------------------------------------------------------------------------+
|                          Fuzzing Worker (Python)                            |
|  - Pre-flight Diagnostics     - Telemetry Parser      - Process Monitor     |
+---------------------------------------+-------------------------------------+
                                        | Native Process Spawn & IPC Pipes
                                        v
+-----------------------------------------------------------------------------+
|                            Fuzzing Engine (WinAFL)                          |
|  - afl-fuzz.exe (Mutator, IPC pipe server, shared memory bitmap manager)    |
+---------------------------------------+-------------------------------------+
                                        | Binary Translation / Injection
                                        v
+-----------------------------------------------------------------------------+
|                          DynamoRIO Runtime (drrun.exe)                      |
|  - winafl.dll Client (Clean-call hooks, BB coverage, persist loop sync)     |
+---------------------------------------+-------------------------------------+
                                        | Execution & Persistence
                                        v
+-----------------------------------------------------------------------------+
|                     Target Application & Harness Process                    |
|  - pdf_harness.exe (SumatraPDF / MuPDF Fitz parser)                         |
|  - Exported Hooks: iteration_boundary, fuzz_target                          |
|  - In-app persistence: while(1) loop calling target function                |
+---------------------------------------+-------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
+---------------------------------+           +-------------------------------+
|       Input / Corpus Data       |           |    Crashes / Telemetry Logs   |
| - Seed PDFs (dummy.pdf, etc.)   |           | - AFL queue, bitmap, proc logs|
| - Dynamic mutations (.cur_input)|           | - Triage artifacts & findings |
+---------------------------------+           +-------------------------------+
```

---

## 3. Repository Structure

```text
C:\Projects\Fuzzer\
├── backend/                        # FastAPI backend application
│   ├── alembic/                    # Database migrations
│   ├── app/
│   │   ├── ai/                     # AI triage providers & pipelines
│   │   ├── analysis/               # Scoring engine and static analyzers
│   │   ├── harnesses/              # Automated harness generators
│   │   ├── imports/                # Discovery and header parsers
│   │   ├── routers/                # REST API endpoints (campaigns, corpus, coverage,
│   │   │                           # crashes, dashboard, discovery, evidence, findings,
│   │   │                           # harnesses, health, projects, reports, workers, workspace)
│   │   ├── database.py             # Database session manager
│   │   ├── main.py                 # FastAPI application root
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   └── schemas.py              # Pydantic validation schemas
│   ├── data/                       # Built-in sample harness templates
│   ├── scripts/                    # Demo seed scripts
│   └── tests/                      # PyTest test suites (26 passing tests)
├── frontend/                       # Next.js 15+ App Router Dashboard
│   ├── src/
│   │   ├── app/                    # Web UI pages (Dashboard, Projects, Campaigns,
│   │   │                           # Crashes, Coverage, Evidence, Findings, Harnesses, Workspace)
│   │   ├── components/             # Reusable UI components & Recharts visualizations
│   │   ├── lib/                    # API client layer
│   │   └── types/                  # TypeScript domain models & schemas
│   ├── package.json
│   └── tsconfig.json
├── worker/                         # Fuzzing orchestration worker agent
│   ├── core/                       # Fuzzing engine adapters (WinAFL adapter)
│   ├── client.py                   # API client syncing worker with backend
│   ├── config.py                   # Worker environment & configuration
│   ├── diagnostics.py              # Pre-flight environment validation
│   ├── executor.py                 # Native WinAFL process runner
│   ├── main.py                     # Worker CLI entrypoint
│   ├── mock_coverage.py            # Simulated worker mode for demo/UI testing
│   └── winafl_parser.py            # AFL output directory & telemetry parser
├── target/
│   └── sumatrapdf/                 # SumatraPDF / MuPDF target submodule
│       ├── fuzz/                   # In-app persistence fuzzing harness
│       │   ├── pdf_harness.cpp     # C++ MuPDF harness with iteration_boundary
│       │   └── dummy.pdf           # Sample valid test seed
│       ├── premake5.lua            # Premake build configuration (v145 toolset)
│       └── vs2022/                 # Generated Visual Studio 2026/18 solutions
│           └── pdf_harness.vcxproj # Native harness build project
├── winafl/                         # WinAFL instrumentation submodule
│   ├── afl-fuzz.c                  # Core AFL mutator & process runner
│   ├── winafl.c                    # DynamoRIO client instrumentation plugin
│   ├── modules.c                   # Module tracking utilities
│   ├── CMakeLists.txt              # CMake configuration for winafl.dll & afl-fuzz.exe
│   └── build64/                    # 64-bit build directory (bin\afl-fuzz.exe, bin\winafl.dll)
├── dynamorio/                      # DynamoRIO 8.0.0.1 binary distribution (x64)
├── dynamorio_9/                    # DynamoRIO 9 binary distribution (x64)
├── dynamorio_11/                   # DynamoRIO 11 binary distribution (x64)
├── work/
│   └── sumatra-pdf/                # Active runtime fuzzing workspace
│       ├── input/                  # Seed inputs (dummy.pdf, current.pdf)
│       └── output/                 # AFL queue, state, bitmap, and crash outputs
├── corpus/                         # Seed corpus storage
├── coverage/                       # Coverage logs and mapping outputs
├── crashes/                        # Triage crash archives
├── docs/                           # Architectural, competition, and validation docs
├── scripts/                        # Automation and dev environment management scripts
├── shared/                         # Shared project specifications
├── docker-compose.yml              # PostgreSQL container configuration
├── README.md                       # Project quickstart
└── PRD.md                          # Comprehensive Product Requirements Document (this document)
```

---

## 4. Completed Work

| Component | Status | Relevant Files | Evidence & Notes |
|---|---|---|---|
| **FastAPI Backend Core** | **Complete** | `backend/app/*` | Fully implemented REST API for campaigns, targets, crashes, harnesses, evidence ledger, and real-time dashboard stats. |
| **Backend Test Suite** | **Complete** | `backend/tests/*` | 26/26 tests passing across `test_main.py`, `test_scoring_engine.py`, `test_harnesses.py`, `test_workspace.py`. |
| **Frontend UI Dashboard** | **Complete** | `frontend/src/*` | Built in Next.js with dark-mode theme, Recharts telemetry curves, Active Campaigns tables, and Crash Inspector. Production build compiles cleanly. |
| **Target Discovery & Static Analysis** | **Complete** | `backend/app/analysis/*` | Code risk scoring engine based on memory safety heuristics and function signatures. |
| **SumatraPDF C++ Harness** | **Complete** | `target/sumatrapdf/fuzz/pdf_harness.cpp` | Native harness targeting MuPDF `fitz` parser; exports `fuzz_target` and `iteration_boundary`; loops continuously in `main()` for WinAFL in-app persistence. |
| **SumatraPDF Build System** | **Complete** | `target/sumatrapdf/vs2022/pdf_harness.vcxproj` | Configured and building successfully for Release x64 under Visual Studio 2026/18. |
| **WinAFL Build Environment** | **Complete** | `winafl/CMakeLists.txt`, `winafl/build64/*` | MSVC x64 build producing `bin\afl-fuzz.exe` and `bin\winafl.dll` linked against DynamoRIO 8.0.0. |
| **Harness Loop Resolution** | **Complete** | `target/sumatrapdf/fuzz/pdf_harness.cpp` | Fixed single-execution exit by wrapping `iteration_boundary()` in `while(1)` loop, enabling in-app persistence. |
| **WinAFL Child Handle Diagnostic** | **Complete** | `winafl/afl-fuzz.c` | Diagnosed and addressed `drrun.exe` vs target process handle mismatch in `destroy_target_process()`. |

---

## 5. Current State

- **Confirmed Working:**
  - Backend API with SQLite/PostgreSQL support.
  - Frontend Next.js application and telemetry dashboards.
  - SumatraPDF `pdf_harness.exe` compilation and standalone execution.
  - DynamoRIO 8.0.0 binary translation and `winafl.dll` module loading.
  - Basic block coverage mapping and target function instrumentation.
  - Seed generation and input corpus management.
- **Partially Working / In Progress:**
  - WinAFL `afl-fuzz.exe` dry-run cycle under Windows 11 / VS 2026: dry run reaches target and executes clean calls, but final process termination handshake requires verified `OpenProcess` permissions.
- **Experimental:**
  - Automated AI triage pipeline with local LLM integration (`backend/app/ai/provider.py`).

---

## 6. Prioritized Remaining Tasks

### P0 — Blocking: Finalize WinAFL Windows 11 Process Synchronization
- **Description:** Complete the handle acquisition in `winafl/afl-fuzz.c` using `PROCESS_ALL_ACCESS` (or inherited handle retention) to ensure `afl-fuzz.exe` smoothly terminates and cycles persistent target runs without `GLE=87`.
- **Files Involved:** `winafl/afl-fuzz.c`
- **Acceptance Criteria:** `afl-fuzz.exe` completes multi-iteration dry-run and enters continuous fuzzing state without halting.

### P1 — High Priority: Worker Agent End-to-End Campaign Automation
- **Description:** Wire the native WinAFL executor in `worker/executor.py` to the backend REST API to allow starting, monitoring, and stopping campaigns directly from the frontend dashboard.
- **Files Involved:** `worker/executor.py`, `worker/client.py`, `backend/app/routers/campaigns.py`
- **Acceptance Criteria:** Starting a campaign in UI launches worker process and displays live exec/s telemetry.

### P2 — Medium Priority: Crash Deduplication & Triage Ledger
- **Description:** Automatic minidump hashing and stack trace symbolization for crashes emitted to `work/sumatra-pdf/output/crashes`.
- **Files Involved:** `backend/app/analysis/pipeline.py`, `backend/app/routers/crashes.py`
- **Acceptance Criteria:** Crashes automatically generate entries in the Evidence Ledger with unique hash signatures.

### P3 — Future Improvements: Multi-Target Expansion & TinyInst Backend
- **Description:** Add support for additional target binaries (e.g., media codecs, archive extractors) and enable the optional TinyInst debugger backend.

---

## 7. Build Instructions

### 1. Build SumatraPDF Harness (`pdf_harness.exe`)
```powershell
& 'C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\amd64\MSBuild.exe' `
  'C:\Projects\Fuzzer\target\sumatrapdf\vs2022\pdf_harness.vcxproj' `
  /p:Configuration=Release /p:Platform=x64
```

### 2. Build WinAFL (`afl-fuzz.exe` and `winafl.dll`)
```powershell
call "C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd C:\Projects\Fuzzer\winafl\build64
cmake --build . --target afl-fuzz --target winafl --config Release
```

### 3. Setup Backend & Run Tests
```powershell
cd C:\Projects\Fuzzer\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -v
```

### 4. Setup Frontend
```powershell
cd C:\Projects\Fuzzer\frontend
npm install
npm run build
```

---

## 8. Runtime & Fuzzing Instructions

### Run WinAFL In-App Persistent Campaign
```cmd
set "PATH=C:\Projects\Fuzzer\dynamorio\bin64;C:\Projects\Fuzzer\dynamorio\lib64\release;C:\Projects\Fuzzer\dynamorio\drmemory\bin64;%PATH%"

C:\Projects\Fuzzer\winafl\build64\bin\afl-fuzz.exe ^
  -i C:\Projects\Fuzzer\work\sumatra-pdf\input ^
  -o C:\Projects\Fuzzer\work\sumatra-pdf\output ^
  -D C:\Projects\Fuzzer\dynamorio\bin64 ^
  -w C:\Projects\Fuzzer\winafl\build64\bin\winafl.dll ^
  -t 10000 -- ^
  -coverage_module pdf_harness.exe ^
  -target_module pdf_harness.exe ^
  -target_method iteration_boundary ^
  -fuzz_iterations 5000 ^
  -nargs 1 ^
  -call_convention ms64 ^
  -persistence_mode in_app -- ^
  C:\Projects\Fuzzer\target\sumatrapdf\out\rel64\pdf_harness.exe @@
```

---

## 9. Definition of Done

The Fuzz-Sentinel platform reaches full production completeness when:
1. All core components (Backend, Frontend, Worker, Harness, WinAFL) build cleanly on modern Windows systems.
2. End-to-end continuous fuzzing operates reliably on native targets with in-app persistence.
3. Telemetry and findings stream live from workers to the Web UI.
4. Cryptographically signed reports can be generated for all confirmed vulnerabilities.
5. Entire codebase and documentation are version-controlled and synchronized with GitHub.
