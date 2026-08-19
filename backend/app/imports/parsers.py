"""
Fuzz-Sentinel Import Engine: Reverse-Engineering Evidence Parsers
=================================================================
Handles importing external RE data into the Fuzz-Sentinel target database.

Supported import formats
------------------------
1. ghidra_csv      — Ghidra "Export Program → CSV" (functions table)
2. ghidra_json     — Ghidra "Export Program → JSON" (full program data)
3. function_list   — Plain text or JSON list of function names/addresses
4. re_notes        — JSON-structured RE notes from manual analysis
5. call_graph      — DOT or JSON adjacency list of caller→callee edges
6. binary_metadata — JSON containing module/section/symbol info

IMPORTANT: No function name or address is fabricated. Every record
           imported retains its origin source and evidence_kind.

Usage
-----
    parser = get_parser("ghidra_csv")
    records = parser.parse(file_bytes, filename="SumatraPDF.exe.csv")
"""

import csv
import io
import json
import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

logger = logging.getLogger("fuzz_sentinel.importer")


# ---------------------------------------------------------------------------
# Canonical import record (one per function found in source)
# ---------------------------------------------------------------------------
@dataclass
class ImportedTarget:
    """
    Raw record from a single import source.
    All fields are Optional — the importer fills what the format provides;
    the rest stays None (never fabricated).
    """
    function_name: str
    module: str = ""
    address: Optional[str] = None
    address_kind: str = "user_provided"   # "observed" if from PDB/binary, "user_provided" if from notes
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    input_type: str = "binary"
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    call_path: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 0.0
    analyst_notes: Optional[str] = None
    import_source: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)   # original row for audit


# ---------------------------------------------------------------------------
# Base parser
# ---------------------------------------------------------------------------
class BaseImportParser(ABC):
    import_type: str = "unknown"

    @abstractmethod
    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        """Parse raw file bytes and return a list of ImportedTarget records."""

    def _normalize_address(self, addr: str) -> Optional[str]:
        """Return a normalised hex address string or None if unparseable."""
        addr = addr.strip()
        if not addr or addr in ("-", "N/A", "None", "null"):
            return None
        # Accept plain hex digits or 0x-prefixed
        addr = addr.replace("`", "").replace(" ", "")
        if re.fullmatch(r"(0x)?[0-9a-fA-F]+", addr):
            return addr if addr.startswith("0x") else f"0x{addr}"
        return None

    def _extract_module(self, filename: str) -> str:
        """Best-effort module name from filename."""
        stem = filename.rsplit(".", 1)[0] if "." in filename else filename
        return stem.split("/")[-1].split("\\")[-1]


# ---------------------------------------------------------------------------
# 1. Ghidra CSV export parser
# ---------------------------------------------------------------------------
class GhidraCSVParser(BaseImportParser):
    """
    Parses Ghidra 'Export → CSV' output.

    Expected columns (Ghidra default):
      Name, Location, Type, Namespace, Source, Reference Count
    Or extended format from Ghidra's function table:
      Name, Entry Point, Signature, Return Type, ...
    """
    import_type = "ghidra_csv"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        module = self._extract_module(filename)
        text = data.decode("utf-8-sig", errors="replace")  # handle BOM
        reader = csv.DictReader(io.StringIO(text))
        targets: List[ImportedTarget] = []

        for row in reader:
            fname = (
                row.get("Name") or row.get("Function Name") or
                row.get("name") or ""
            ).strip()
            if not fname or fname.startswith("FUN_"):
                # Skip unnamed/auto-generated stubs unless user explicitly wants them
                pass  # still include — researcher can dismiss
            if not fname:
                continue

            addr_raw = (
                row.get("Location") or row.get("Entry Point") or
                row.get("Address") or row.get("address") or ""
            )
            addr = self._normalize_address(addr_raw)

            sig = row.get("Signature") or row.get("signature") or ""
            args = self._parse_signature_args(sig)

            ns = row.get("Namespace") or row.get("namespace") or module
            src = row.get("Source") or row.get("source_file") or None
            src_line_raw = row.get("Line") or row.get("source_line") or None
            src_line: Optional[int] = None
            try:
                src_line = int(src_line_raw) if src_line_raw else None
            except (ValueError, TypeError):
                pass

            targets.append(ImportedTarget(
                function_name=fname,
                module=ns or module,
                address=addr,
                address_kind="observed",    # Ghidra reads from binary → observed
                source_file=src,
                source_line=src_line,
                arguments=args,
                import_source="ghidra_csv",
                raw=dict(row),
            ))

        logger.info(f"GhidraCSVParser: parsed {len(targets)} records from {filename}")
        return targets

    def _parse_signature_args(self, sig: str) -> List[Dict[str, Any]]:
        """Best-effort extraction of argument list from a C signature string."""
        m = re.search(r'\((.+)\)', sig)
        if not m:
            return []
        args_str = m.group(1).strip()
        if args_str.lower() in ("void", ""):
            return []
        result = []
        for part in re.split(r',\s*(?![^<>]*>)', args_str):
            part = part.strip()
            if not part:
                continue
            tokens = part.split()
            pname = tokens[-1].lstrip("*&") if tokens else None
            ptype = " ".join(tokens[:-1]) if len(tokens) > 1 else "unknown"
            result.append({
                "name": pname,
                "type": ptype,
                "is_attacker_controlled": False,  # researcher must verify
            })
        return result


# ---------------------------------------------------------------------------
# 2. Ghidra JSON export parser
# ---------------------------------------------------------------------------
class GhidraJSONParser(BaseImportParser):
    """
    Parses Ghidra's JSON export (via ExportProgramScript or GhidraScript).
    Expected top-level keys: functions, datatypes, imports, exports
    """
    import_type = "ghidra_json"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        module = self._extract_module(filename)
        try:
            doc = json.loads(data.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc

        functions = doc.get("functions") or doc.get("Functions") or []
        if isinstance(doc, list):
            functions = doc

        targets: List[ImportedTarget] = []
        for fn in functions:
            if not isinstance(fn, dict):
                continue
            fname = fn.get("name") or fn.get("Name") or fn.get("entryPoint") or ""
            fname = fname.strip()
            if not fname:
                continue

            addr = self._normalize_address(
                fn.get("entryPoint") or fn.get("address") or fn.get("Entry Point") or ""
            )
            src = fn.get("sourceFile") or fn.get("source_file") or None
            src_line: Optional[int] = None
            try:
                src_line = int(fn.get("sourceLine") or fn.get("source_line") or 0) or None
            except (ValueError, TypeError):
                pass

            args = fn.get("parameters") or fn.get("arguments") or []
            parsed_args = []
            for p in args:
                if isinstance(p, dict):
                    parsed_args.append({
                        "name": p.get("name"),
                        "type": p.get("dataType") or p.get("type"),
                        "is_attacker_controlled": False,
                    })

            ns = fn.get("namespace") or fn.get("class") or module

            targets.append(ImportedTarget(
                function_name=fname,
                module=ns,
                address=addr,
                address_kind="observed",   # Ghidra reads from binary
                source_file=src,
                source_line=src_line,
                arguments=parsed_args,
                analyst_notes=fn.get("comment") or fn.get("notes"),
                import_source="ghidra_json",
                raw=fn,
            ))

        logger.info(f"GhidraJSONParser: parsed {len(targets)} functions from {filename}")
        return targets


# ---------------------------------------------------------------------------
# 3. Function list parser (plain text or JSON)
# ---------------------------------------------------------------------------
class FunctionListParser(BaseImportParser):
    """
    Simple function list: one function name per line, optionally with address.

    Accepted formats:
      func_name
      0x1234abcd func_name
      func_name 0x1234abcd
      func_name, 0x1234abcd, module_name

    JSON variant: [{"name": "...", "address": "...", "module": "..."}, ...]
    """
    import_type = "function_list"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        module = self._extract_module(filename)
        text = data.decode("utf-8", errors="replace").strip()

        # Try JSON first
        if text.startswith("[") or text.startswith("{"):
            try:
                return self._parse_json(json.loads(text), module, filename)
            except json.JSONDecodeError:
                pass

        targets: List[ImportedTarget] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue
            parts = re.split(r"[\s,;]+", line)
            addr = None
            name = None
            mod = module
            for part in parts:
                if re.fullmatch(r"(0x)?[0-9a-fA-F]{4,}", part):
                    addr = self._normalize_address(part)
                elif not name:
                    name = part
                else:
                    mod = part

            if not name:
                continue
            targets.append(ImportedTarget(
                function_name=name,
                module=mod,
                address=addr,
                address_kind="user_provided",
                import_source="function_list",
                raw={"line": line},
            ))

        logger.info(f"FunctionListParser: parsed {len(targets)} entries from {filename}")
        return targets

    def _parse_json(self, doc, module: str, filename: str) -> List[ImportedTarget]:
        if isinstance(doc, dict) and "functions" in doc:
            items = doc["functions"]
        elif isinstance(doc, list):
            items = doc
        else:
            raise ValueError("Unrecognised JSON structure for function list")

        targets = []
        for item in items:
            if isinstance(item, str):
                targets.append(ImportedTarget(
                    function_name=item,
                    module=module,
                    import_source="function_list",
                    raw={"entry": item},
                ))
            elif isinstance(item, dict):
                fname = item.get("name") or item.get("function") or ""
                if not fname:
                    continue
                addr = self._normalize_address(item.get("address") or item.get("addr") or "")
                targets.append(ImportedTarget(
                    function_name=fname,
                    module=item.get("module") or module,
                    address=addr,
                    address_kind="user_provided",
                    source_file=item.get("source_file"),
                    source_line=item.get("source_line"),
                    analyst_notes=item.get("notes"),
                    import_source="function_list",
                    raw=item,
                ))
        return targets


# ---------------------------------------------------------------------------
# 4. Reverse-Engineering Notes parser (structured JSON)
# ---------------------------------------------------------------------------
class RENotesParser(BaseImportParser):
    """
    Parses analyst RE notes in Fuzz-Sentinel's canonical JSON format.

    Schema (each entry):
    {
      "function": "ParseDocumentHeader",
      "module": "SumatraPDF",
      "address": "0x...",            -- optional, must be from binary
      "address_kind": "observed",    -- "observed" | "user_provided"
      "source_file": "...",          -- optional
      "source_line": 123,            -- optional
      "arguments": [...],
      "input_type": "pdf",
      "call_path": [...],
      "dependencies": [...],
      "risk_score": 7.5,             -- analyst estimate, 0-10
      "confidence": 0.8,             -- analyst confidence, 0-1
      "notes": "...",
      "evidence": [...]              -- list of evidence strings
    }
    """
    import_type = "re_notes"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        try:
            doc = json.loads(data.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in RE notes file {filename}: {exc}") from exc

        if isinstance(doc, dict) and "targets" in doc:
            entries = doc["targets"]
        elif isinstance(doc, list):
            entries = doc
        else:
            raise ValueError("RE notes JSON must be a list or {\"targets\": [...]}")

        targets = []
        for entry in entries:
            fname = entry.get("function") or entry.get("name") or ""
            fname = fname.strip()
            if not fname:
                continue

            addr_raw = entry.get("address") or entry.get("addr") or ""
            addr = self._normalize_address(addr_raw)
            addr_kind = entry.get("address_kind", "user_provided")
            if addr and addr_kind not in ("observed", "inferred", "user_provided"):
                addr_kind = "user_provided"

            try:
                risk = float(entry.get("risk_score", 0.0))
                risk = max(0.0, min(10.0, risk))
            except (ValueError, TypeError):
                risk = 0.0

            try:
                conf = float(entry.get("confidence", 0.0))
                conf = max(0.0, min(1.0, conf))
            except (ValueError, TypeError):
                conf = 0.0

            call_path = entry.get("call_path") or []
            if isinstance(call_path, list):
                normalised_cp = []
                for edge in call_path:
                    if isinstance(edge, dict):
                        normalised_cp.append({
                            "caller": edge.get("caller", ""),
                            "callee": edge.get("callee", ""),
                            "evidence_kind": edge.get("evidence_kind", "user_provided"),
                        })
                    elif isinstance(edge, str):
                        # "caller -> callee" shorthand
                        parts = edge.split("->")
                        normalised_cp.append({
                            "caller": parts[0].strip() if parts else "",
                            "callee": parts[1].strip() if len(parts) > 1 else "",
                            "evidence_kind": "user_provided",
                        })
                call_path = normalised_cp

            targets.append(ImportedTarget(
                function_name=fname,
                module=entry.get("module") or "",
                address=addr,
                address_kind=addr_kind,
                source_file=entry.get("source_file"),
                source_line=entry.get("source_line"),
                input_type=entry.get("input_type", "binary"),
                arguments=entry.get("arguments") or [],
                call_path=call_path,
                dependencies=entry.get("dependencies") or [],
                risk_score=risk,
                confidence=conf,
                analyst_notes=entry.get("notes"),
                import_source="re_notes",
                raw=entry,
            ))

        logger.info(f"RENotesParser: parsed {len(targets)} entries from {filename}")
        return targets


# ---------------------------------------------------------------------------
# 5. Call-graph parser (DOT or JSON adjacency list)
# ---------------------------------------------------------------------------
class CallGraphParser(BaseImportParser):
    """
    Parses a call graph to extract caller/callee edges and infer target candidates.

    Supported formats:
      - JSON: {"edges": [{"caller": "...", "callee": "..."}]}
              or {"nodes": {...}, "edges": [...]}
      - Simple DOT: digraph { A -> B; B -> C; }
    """
    import_type = "call_graph"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        text = data.decode("utf-8", errors="replace").strip()

        if text.startswith("{") or text.startswith("["):
            edges = self._parse_json_graph(text, filename)
        else:
            edges = self._parse_dot(text, filename)

        # Each unique callee becomes a candidate target
        module = self._extract_module(filename)
        callees: Dict[str, List[Dict]] = {}
        for edge in edges:
            callee = edge["callee"]
            callees.setdefault(callee, []).append(edge)

        targets = []
        for callee, incoming_edges in callees.items():
            targets.append(ImportedTarget(
                function_name=callee,
                module=module,
                call_path=incoming_edges,
                import_source="call_graph",
                raw={"edges": incoming_edges},
            ))

        logger.info(f"CallGraphParser: found {len(targets)} unique callees from {filename}")
        return targets

    def _parse_json_graph(self, text: str, filename: str) -> List[Dict]:
        doc = json.loads(text)
        edges_raw = doc.get("edges") or doc.get("calls") or []
        if isinstance(doc, list):
            edges_raw = doc
        edges = []
        for e in edges_raw:
            if isinstance(e, dict):
                caller = e.get("caller") or e.get("from") or e.get("src") or ""
                callee = e.get("callee") or e.get("to") or e.get("dst") or ""
                if caller and callee:
                    edges.append({"caller": caller, "callee": callee, "evidence_kind": "user_provided"})
            elif isinstance(e, list) and len(e) >= 2:
                edges.append({"caller": str(e[0]), "callee": str(e[1]), "evidence_kind": "user_provided"})
        return edges

    def _parse_dot(self, text: str, filename: str) -> List[Dict]:
        # Extract A -> B patterns
        edges = []
        for m in re.finditer(r'"?(\w[\w:]*)"?\s*->\s*"?(\w[\w:]*)"?', text):
            edges.append({"caller": m.group(1), "callee": m.group(2), "evidence_kind": "user_provided"})
        return edges


# ---------------------------------------------------------------------------
# 6. Binary metadata parser (JSON symbols/exports)
# ---------------------------------------------------------------------------
class BinaryMetadataParser(BaseImportParser):
    """
    Parses a JSON file containing binary symbol/export information.
    Can be produced by: dumpbin /EXPORTS, nm, objdump, or custom scripts.

    Schema:
    {
      "binary": "SumatraPDF.exe",
      "exports": [{"name": "...", "address": "0x...", "ordinal": 1}],
      "imports": [...],
      "symbols": [{"name": "...", "address": "0x...", "type": "function"}]
    }
    """
    import_type = "binary_metadata"

    def parse(self, data: bytes, filename: str = "") -> List[ImportedTarget]:
        try:
            doc = json.loads(data.decode("utf-8", errors="replace"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {filename}: {exc}") from exc

        binary_name = doc.get("binary") or self._extract_module(filename)
        module = binary_name.rsplit(".", 1)[0] if "." in binary_name else binary_name

        sources = []
        sources.extend(doc.get("exports") or [])
        sources.extend(doc.get("symbols") or [])

        targets = []
        seen = set()
        for sym in sources:
            if not isinstance(sym, dict):
                continue
            sym_type = sym.get("type", "function")
            if sym_type not in ("function", "func", "FUNC", "code", "CODE", ""):
                continue
            fname = sym.get("name") or sym.get("symbol") or ""
            fname = fname.strip()
            if not fname or fname in seen:
                continue
            seen.add(fname)

            addr = self._normalize_address(sym.get("address") or sym.get("rva") or "")
            targets.append(ImportedTarget(
                function_name=fname,
                module=module,
                address=addr,
                address_kind="observed",   # from binary symbol table
                import_source="binary_metadata",
                raw=sym,
            ))

        logger.info(f"BinaryMetadataParser: parsed {len(targets)} symbols from {filename}")
        return targets


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_PARSERS = {
    "ghidra_csv":      GhidraCSVParser,
    "ghidra_json":     GhidraJSONParser,
    "function_list":   FunctionListParser,
    "re_notes":        RENotesParser,
    "call_graph":      CallGraphParser,
    "binary_metadata": BinaryMetadataParser,
}

SUPPORTED_IMPORT_TYPES = list(_PARSERS.keys())


def get_parser(import_type: str) -> BaseImportParser:
    cls = _PARSERS.get(import_type)
    if not cls:
        raise ValueError(
            f"Unknown import type '{import_type}'. "
            f"Supported: {', '.join(SUPPORTED_IMPORT_TYPES)}"
        )
    return cls()
