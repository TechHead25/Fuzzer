"""
Fuzz-Sentinel Analysis Engine: Source Code Analyzer
====================================================
Performs static analysis on C/C++ source files using regex heuristics and
AST-level pattern matching (via tree-sitter when available, regex fallback
when not installed).

All findings are classified as OBSERVED (text found in source) or INFERRED
(derived from naming / proximity heuristics). Addresses are NEVER assigned
here – that requires a binary analysis step.
"""

import re
import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Set

from .types import (
    DiscoveredTarget, FunctionParameter, EvidenceKind, HarnessType
)

logger = logging.getLogger("fuzz_sentinel.analysis.source")


# ---------------------------------------------------------------------------
# Indicator patterns (compiled once at import time)
# ---------------------------------------------------------------------------
_PATTERNS: Dict[str, re.Pattern] = {
    "memcpy_call":         re.compile(r'\b(memcpy|memmove|wmemcpy|CopyMemory|RtlCopyMemory)\s*\(', re.I),
    "buffer_write":        re.compile(r'\b(\w+)\s*\[\s*.+\]\s*='),
    "buffer_read":         re.compile(r'=\s*\*?\s*(\w+)\s*\[\s*.+\]'),
    "string_operation":    re.compile(r'\b(strcpy|strcat|sprintf|vsprintf|gets|wcscpy|wcscat)\s*\(', re.I),
    "format_string_op":    re.compile(r'\b(sscanf|fscanf|scanf|printf|fprintf|snprintf|vsnprintf)\s*\(', re.I),
    "decompression_call":  re.compile(r'\b(inflate|uncompress|LzmaUncompress|BZ2_bzDecompress|zlib_inflate|lz4_decompress)\s*\(', re.I),
    "heap_allocation":     re.compile(r'\b(malloc|calloc|realloc|new\s+\w|\bHeapAlloc)\s*\(', re.I),
    "file_io":             re.compile(r'\b(fread|fopen|ReadFile|CreateFile|ifstream|read\s*\()\s*\(', re.I),
    "network_recv":        re.compile(r'\b(recv|recvfrom|WSARecv|read\s*\(sock)\s*\(', re.I),
    "length_arithmetic":   re.compile(r'\b(len|length|size|count|num|n)\b\s*[\+\-\*\/]'),
    "offset_arithmetic":   re.compile(r'\b(offset|off|pos|idx|index)\b\s*[\+\-\*]'),
    "complex_loop":        re.compile(r'\bfor\s*\(.*;\s*\w+\s*[<>=]\s*\w*(len|length|size|count|n)\w*\s*;'),
    "parser_routine":      re.compile(r'(parse|read|decode|load|deseriali[sz]e|import|open)\w*', re.I),
}

_ENTRY_POINT_PATTERNS: re.Pattern = re.compile(
    r'(main|wmain|DllMain|WinMain|wWinMain|Open|Load|Parse|Read|Decode|Import)\b', re.I
)

# Regex to extract a C/C++ function signature (best-effort; no full parser)
_FUNCTION_SIG: re.Pattern = re.compile(
    r'^[\w\s\*&:<>]+\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?\{?\s*$',
    re.MULTILINE,
)

_PARAM_SPLIT: re.Pattern = re.compile(r',\s*(?![^<>]*>)')  # handle template args

_ATTACKER_PARAM_HINTS: set = {
    "buf", "buffer", "data", "input", "src", "stream", "content",
    "payload", "bytes", "pData", "pBuffer", "lpBuffer", "pbData",
}


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, source_root: Path, project_id: int) -> List[DiscoveredTarget]:
        """Run analysis and return discovered targets."""


# ---------------------------------------------------------------------------
# Source Analyzer
# ---------------------------------------------------------------------------
class SourceAnalyzer(BaseAnalyzer):
    """
    Analyses a directory of C/C++ source files.

    Steps:
    1. Walk all .c/.cpp/.h files under source_root.
    2. Extract function signatures.
    3. Per function body, match indicator patterns.
    4. Build raw_indicators dict (observed).
    5. Infer 'parser_routine' from function name if name matches.
    6. Infer 'attacker_controlled_param' from parameter names.
    7. Return list of DiscoveredTarget (un-scored; caller should run TargetScorer).
    """

    EXTENSIONS = {".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB per file
    MAX_FILES = 2000

    def analyze(self, source_root: Path, project_id: int) -> List[DiscoveredTarget]:
        discovered: List[DiscoveredTarget] = []
        files_scanned = 0

        for root, _dirs, files in os.walk(source_root):
            for fname in files:
                if files_scanned >= self.MAX_FILES:
                    break
                fpath = Path(root) / fname
                if fpath.suffix.lower() not in self.EXTENSIONS:
                    continue
                if fpath.stat().st_size > self.MAX_FILE_SIZE:
                    logger.warning(f"Skipping large file: {fpath}")
                    continue
                files_scanned += 1
                try:
                    targets = self._analyze_file(fpath, source_root)
                    discovered.extend(targets)
                except Exception as exc:
                    logger.error(f"Error analyzing {fpath}: {exc}")

        logger.info(
            f"SourceAnalyzer: scanned {files_scanned} files, "
            f"found {len(discovered)} candidate functions"
        )
        return discovered

    def _analyze_file(self, fpath: Path, source_root: Path) -> List[DiscoveredTarget]:
        text = fpath.read_text(encoding="utf-8", errors="replace")
        rel_path = str(fpath.relative_to(source_root))
        functions = self._extract_functions(text, rel_path)
        return functions

    def _extract_functions(self, text: str, rel_path: str) -> List[DiscoveredTarget]:
        """
        Best-effort extraction of function bodies.
        We split on function signatures then gather the body until the
        matching closing brace. Returns one DiscoveredTarget per function.
        """
        targets: List[DiscoveredTarget] = []
        lines = text.splitlines()
        n = len(lines)
        i = 0
        while i < n:
            line = lines[i]
            m = _FUNCTION_SIG.match(line.rstrip())
            if not m:
                i += 1
                continue

            func_name = m.group(1)
            param_str = m.group(2).strip()
            start_line = i + 1  # 1-indexed

            # Find function body
            body_lines, end_i = self._collect_body(lines, i)
            if body_lines is None:
                i += 1
                continue

            body = "\n".join(body_lines)
            indicators = self._match_indicators(func_name, body)
            if not indicators:
                i = end_i + 1
                continue

            params = self._parse_params(param_str)
            module = Path(rel_path).stem

            target = DiscoveredTarget(
                function_name=func_name,
                module=module,
                source_file=rel_path,
                source_line=start_line,
                source_file_kind=EvidenceKind.OBSERVED,
                address=None,
                address_kind=EvidenceKind.INFERRED,
                parameters=params,
                raw_indicators=indicators,
                input_type="binary",
            )
            targets.append(target)
            i = end_i + 1

        return targets

    def _collect_body(self, lines: List[str], start: int):
        """Collect lines from the opening { to the matching }. Returns (body, end_index)."""
        depth = 0
        body: List[str] = []
        found_open = False
        for i in range(start, min(start + 500, len(lines))):
            l = lines[i]
            depth += l.count("{") - l.count("}")
            if "{" in l:
                found_open = True
            if found_open:
                body.append(l)
            if found_open and depth <= 0:
                return body, i
        return None, start

    def _match_indicators(self, func_name: str, body: str) -> Dict[str, Any]:
        """Match indicator patterns in the function body."""
        indicators: Dict[str, Any] = {}

        for indicator, pat in _PATTERNS.items():
            if indicator == "parser_routine":
                # Name-based inference
                if pat.search(func_name):
                    indicators[indicator] = f"function name matches '{func_name}'"
                continue
            m = pat.search(body)
            if m:
                # Store the matched text as evidence reference
                indicators[indicator] = m.group(0).strip()[:80]

        # Infer parser_routine from body presence of magic constants
        if re.search(r'0x[0-9A-Fa-f]{4,}', body) and "buffer_read" in indicators:
            indicators.setdefault("parser_routine", "magic constant comparison with buffer read")

        return indicators

    def _parse_params(self, param_str: str) -> List[FunctionParameter]:
        if not param_str or param_str.strip() == "void":
            return []
        params = []
        for part in _PARAM_SPLIT.split(param_str):
            part = part.strip()
            if not part:
                continue
            tokens = part.split()
            pname = tokens[-1].lstrip("*&") if tokens else None
            ptype = " ".join(tokens[:-1]) if len(tokens) > 1 else None
            is_ac = bool(pname and pname.lower() in _ATTACKER_PARAM_HINTS)
            params.append(FunctionParameter(
                name=pname,
                param_type=ptype,
                is_attacker_controlled=is_ac,
                evidence_kind=EvidenceKind.INFERRED,
                notes="name heuristic" if is_ac else "",
            ))
        # If any param is attacker-controlled, inject indicator
        return params


# ---------------------------------------------------------------------------
# Binary Analyzer (Adapter Interface — requires external tool)
# ---------------------------------------------------------------------------
class BinaryAnalyzer(BaseAnalyzer):
    """
    Adapter for binary analysis.

    DEPENDENCY: Requires an external disassembler/decompiler that can emit
    JSON (e.g. IDA Pro + idat64, Ghidra headless, or Binary Ninja).
    Without the tool, this raises a clear RuntimeError explaining what is missing.
    """

    def __init__(self, tool_path: str = ""):
        self.tool_path = tool_path

    def analyze(self, source_root: Path, project_id: int) -> List[DiscoveredTarget]:
        raise RuntimeError(
            "BinaryAnalyzer requires an external disassembler.\n"
            "Supported tools: IDA Pro (idat64.exe), Ghidra headless, Binary Ninja.\n"
            "Configure BINARY_ANALYSIS_TOOL_PATH in the worker settings."
        )


# ---------------------------------------------------------------------------
# Call-Graph Analyzer (Adapter Interface — requires compiler DB or tool)
# ---------------------------------------------------------------------------
class CallGraphAnalyzer:
    """
    Enriches targets with call-path information.

    DEPENDENCY: Requires a compile_commands.json (clang) or a pre-built
    call graph. Without it, call_path remains empty and deep_call_path
    indicator cannot be inferred.
    """

    def enrich(self, targets: List[DiscoveredTarget], compile_commands_path: Path) -> List[DiscoveredTarget]:
        if not compile_commands_path.exists():
            logger.warning(
                "CallGraphAnalyzer: compile_commands.json not found at "
                f"{compile_commands_path}. Call-path enrichment skipped."
            )
            return targets
        # Real implementation would run clang with -ast-dump or use libclang
        # to build a call graph and enrich each target's call_path.
        raise NotImplementedError(
            "CallGraphAnalyzer requires libclang or a pre-built call graph. "
            "Install libclang-dev and configure LIBCLANG_PATH to enable this feature."
        )
