from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

@dataclass
class LogFinding:
    line_no: int
    keyword: str
    line: str

@dataclass
class LogParseResult:
    file: str
    total_lines: int
    matched_lines: int
    by_keyword: Dict[str, int]
    samples: List[LogFinding]

def parse_log_file(
    log_path: Path,
    keywords: List[str],
    *,
    case_insensitive: bool = True,
    max_samples: int = 50,
    max_line_length: int = 5000,
) -> LogParseResult:
    if not keywords:
        keywords = ["error"]

    flags = re.IGNORECASE if case_insensitive else 0
    patterns = [(kw, re.compile(re.escape(kw), flags)) for kw in keywords]

    total = 0
    matched = 0
    by_kw: Dict[str, int] = {kw: 0 for kw in keywords}
    samples: List[LogFinding] = []

    with log_path.open("r", encoding="utf-8", errors="replace") as f:
        for idx, line in enumerate(f, start=1):
            total += 1
            if len(line) > max_line_length:
                line = line[:max_line_length] + "…(truncated)"

            hit_any = False
            for kw, rx in patterns:
                if rx.search(line):
                    by_kw[kw] = by_kw.get(kw, 0) + 1
                    if len(samples) < max_samples:
                        samples.append(LogFinding(line_no=idx, keyword=kw, line=line.rstrip("\n")))
                    hit_any = True
            if hit_any:
                matched += 1

    return LogParseResult(
        file=str(log_path),
        total_lines=total,
        matched_lines=matched,
        by_keyword=by_kw,
        samples=samples,
    )
