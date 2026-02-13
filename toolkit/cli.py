from __future__ import annotations
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .utils import ensure_dir, parse_csv_list, validate_file
from .system_health import collect_health_snapshot, HealthSnapshot
from .log_parser import parse_log_file, LogParseResult
from .report import export_csv, export_xlsx

def _print_header(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)

def _print_summary(snapshot: Optional[HealthSnapshot], log_result: Optional[LogParseResult]) -> Dict[str, str]:
    summary: Dict[str, str] = {}
    summary["generated_at"] = datetime.now().isoformat(timespec="seconds")

    if snapshot is not None:
        summary["hostname"] = snapshot.hostname
        summary["os"] = f"{snapshot.os} {snapshot.os_version}"
        summary["memory_used_percent"] = f"{snapshot.memory.used_percent}%" if snapshot.memory.used_percent is not None else "N/A"
        summary["disk_count"] = str(len(snapshot.disks))
        summary["service_checked"] = str(len(snapshot.services))

        disk_high = any((d.used_percent is not None and d.used_percent >= 90) for d in snapshot.disks)
        mem_high = (snapshot.memory.used_percent is not None and snapshot.memory.used_percent >= 90)
        cpu_high = (snapshot.cpu.load_percent is not None and snapshot.cpu.load_percent >= 90)
        summary["health_flag_disk_90"] = "YES" if disk_high else "NO"
        summary["health_flag_mem_90"] = "YES" if mem_high else "NO"
        summary["health_flag_cpu_90"] = "YES" if cpu_high else "NO"

    if log_result is not None:
        summary["log_file"] = log_result.file
        summary["log_total_lines"] = str(log_result.total_lines)
        summary["log_matched_lines"] = str(log_result.matched_lines)
        if log_result.by_keyword:
            kw, c = max(log_result.by_keyword.items(), key=lambda x: x[1])
            summary["log_top_keyword"] = kw
            summary["log_top_keyword_count"] = str(c)

    return summary

def _export(
    export_format: str,
    out_dir: Path,
    summary: Dict[str, str],
    snapshot: Optional[HealthSnapshot],
    log_result: Optional[LogParseResult],
) -> List[Path]:
    ensure_dir(out_dir)

    created: List[Path] = []
    export_format = export_format.lower().strip()

    if export_format == "xlsx":
        name = f"it_support_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        out_file = out_dir / name
        created.append(export_xlsx(out_file, summary, snapshot, log_result))
    elif export_format == "csv":
        run_dir = out_dir / f"it_support_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        created.extend(export_csv(run_dir, summary, snapshot, log_result))
    else:
        raise ValueError("export must be 'xlsx' or 'csv'")
    return created

def cmd_health(args: argparse.Namespace) -> int:
    services = parse_csv_list(args.services)
    _print_header("SYSTEM HEALTH CHECK")
    snap = collect_health_snapshot(services)

    print(f"Time      : {snap.timestamp}")
    print(f"Host      : {snap.hostname}")
    print(f"OS        : {snap.os} {snap.os_version}")
    print(f"CPU       : cores={snap.cpu.cores_logical or 'N/A'} load={snap.cpu.load_percent or 'N/A'}%")
    print(f"Memory    : total={snap.memory.total_gb or 'N/A'}GB used={snap.memory.used_gb or 'N/A'}GB ({snap.memory.used_percent or 'N/A'}%)")
    print("Disks     :")
    for d in snap.disks:
        print(f"  - {d.mount} total={d.total_gb or 'N/A'}GB used={d.used_gb or 'N/A'}GB ({d.used_percent or 'N/A'}%) free={d.free_gb or 'N/A'}GB")

    if services:
        print("Services  :")
        for s in snap.services:
            print(f"  - {s.name}: {s.status} {('(' + s.detail + ')') if s.detail else ''}")

    summary = _print_summary(snap, None)
    created = _export(args.export, Path(args.out), summary, snap, None)

    print("\nExported:")
    for p in created:
        print(f"  - {p}")
    return 0

def cmd_parse_log(args: argparse.Namespace) -> int:
    _print_header("LOG PARSER")
    log_path = validate_file(args.log)
    keywords = parse_csv_list(args.keywords) or ["error"]

    try:
        result = parse_log_file(log_path, keywords, case_insensitive=not args.case_sensitive)
    except Exception as e:
        print(f"ERROR: {e}")
        return 2

    print(f"File      : {result.file}")
    print(f"Total     : {result.total_lines} lines")
    print(f"Matched   : {result.matched_lines} lines")
    print("ByKeyword :")
    for kw, c in sorted(result.by_keyword.items(), key=lambda x: (-x[1], x[0])):
        print(f"  - {kw}: {c}")

    if result.samples:
        print("\nSample matches (first few):")
        for s in result.samples[:10]:
            print(f"  [{s.line_no}] ({s.keyword}) {s.line}")

    summary = _print_summary(None, result)
    created = _export(args.export, Path(args.out), summary, None, result)

    print("\nExported:")
    for p in created:
        print(f"  - {p}")
    return 0

def cmd_run(args: argparse.Namespace) -> int:
    services = parse_csv_list(args.services)
    log_path = validate_file(args.log)
    keywords = parse_csv_list(args.keywords) or ["error"]

    _print_header("FULL WORKFLOW: HEALTH + LOG + EXPORT")
    snap = collect_health_snapshot(services)

    try:
        log_result = parse_log_file(log_path, keywords, case_insensitive=not args.case_sensitive)
    except Exception as e:
        print(f"WARNING: log parse failed ({e}); continuing with system health only.")
        log_result = None

    summary = _print_summary(snap, log_result)
    created = _export(args.export, Path(args.out), summary, snap, log_result)

    print(f"Time      : {snap.timestamp}")
    print(f"Host      : {snap.hostname}")
    print(f"OS        : {snap.os} {snap.os_version}")
    print(f"CPU       : cores={snap.cpu.cores_logical or 'N/A'} load={snap.cpu.load_percent or 'N/A'}%")
    print(f"Memory    : total={snap.memory.total_gb or 'N/A'}GB used={snap.memory.used_gb or 'N/A'}GB ({snap.memory.used_percent or 'N/A'}%)")
    print("Disks     :")
    for d in snap.disks:
        print(f"  - {d.mount} total={d.total_gb or 'N/A'}GB used={d.used_gb or 'N/A'}GB ({d.used_percent or 'N/A'}%) free={d.free_gb or 'N/A'}GB")

    if services:
        print("Services  :")
        for s in snap.services:
            print(f"  - {s.name}: {s.status} {('(' + s.detail + ')') if s.detail else ''}")

    if log_result is not None:
        print("\nLog Summary:")
        print(f"  File    : {log_result.file}")
        print(f"  Total   : {log_result.total_lines}")
        print(f"  Matched : {log_result.matched_lines}")
        top = sorted(log_result.by_keyword.items(), key=lambda x: (-x[1], x[0]))
        for kw, c in top[:5]:
            print(f"  - {kw}: {c}")

    print("\nExported:")
    for p in created:
        print(f"  - {p}")
    return 0

def interactive_menu() -> int:
    while True:
        _print_header("IT SUPPORT AUTOMATION TOOLKIT")
        print("Pilih mode:")
        print("  1) Check system health (disk/RAM/CPU + services)")
        print("  2) Parse log file (filter keyword error)")
        print("  3) Full workflow (health + log + export)")
        print("  4) Exit")
        choice = input("Masukkan pilihan (1-4): ").strip()

        if choice == "4":
            print("Bye.")
            return 0

        export = input("Export format (xlsx/csv) [xlsx]: ").strip().lower() or "xlsx"
        out = input("Output folder [./reports]: ").strip() or "./reports"

        if choice == "1":
            svcs = input("Nama service (pisahkan koma) [kosong=skip]: ").strip()
            args = argparse.Namespace(services=svcs, export=export, out=out)
            try:
                return cmd_health(args)
            except Exception as e:
                print(f"ERROR: {e}")
                input("Tekan Enter untuk kembali ke menu...")
        elif choice == "2":
            log = input("Path file log: ").strip()
            kws = input("Keyword (pisahkan koma) [error]: ").strip()
            cs = input("Case-sensitive? (y/N): ").strip().lower() == "y"
            args = argparse.Namespace(log=log, keywords=kws, export=export, out=out, case_sensitive=cs)
            try:
                return cmd_parse_log(args)
            except Exception as e:
                print(f"ERROR: {e}")
                input("Tekan Enter untuk kembali ke menu...")
        elif choice == "3":
            svcs = input("Nama service (pisahkan koma) [kosong=skip]: ").strip()
            log = input("Path file log: ").strip()
            kws = input("Keyword (pisahkan koma) [error]: ").strip()
            cs = input("Case-sensitive? (y/N): ").strip().lower() == "y"
            args = argparse.Namespace(log=log, keywords=kws, services=svcs, export=export, out=out, case_sensitive=cs)
            try:
                return cmd_run(args)
            except Exception as e:
                print(f"ERROR: {e}")
                input("Tekan Enter untuk kembali ke menu...")
        else:
            print("Pilihan tidak valid. Masukkan 1-4.")
            input("Tekan Enter untuk kembali ke menu...")

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="toolkit",
        description="IT Support Automation Toolkit CLI: health check, log parsing, export CSV/XLSX.",
    )
    sub = p.add_subparsers(dest="cmd")

    p_health = sub.add_parser("health", help="Check system health (disk/RAM/CPU) + optional services.")
    p_health.add_argument("--services", default="", help="Comma-separated service names to check (Windows service name or systemd unit).")
    p_health.add_argument("--export", default="xlsx", choices=["xlsx", "csv"], help="Export format.")
    p_health.add_argument("--out", default="./reports", help="Output directory.")
    p_health.set_defaults(func=cmd_health)

    p_log = sub.add_parser("parse-log", help="Parse a log file and count keyword matches.")
    p_log.add_argument("--log", required=True, help="Path to log file.")
    p_log.add_argument("--keywords", default="error", help="Comma-separated keywords (default: error).")
    p_log.add_argument("--case-sensitive", action="store_true", help="Enable case-sensitive matching.")
    p_log.add_argument("--export", default="xlsx", choices=["xlsx", "csv"], help="Export format.")
    p_log.add_argument("--out", default="./reports", help="Output directory.")
    p_log.set_defaults(func=cmd_parse_log)

    p_run = sub.add_parser("run", help="Run full workflow: health + log + export.")
    p_run.add_argument("--log", required=True, help="Path to log file.")
    p_run.add_argument("--keywords", default="error", help="Comma-separated keywords (default: error).")
    p_run.add_argument("--services", default="", help="Comma-separated service names to check.")
    p_run.add_argument("--case-sensitive", action="store_true", help="Enable case-sensitive matching.")
    p_run.add_argument("--export", default="xlsx", choices=["xlsx", "csv"], help="Export format.")
    p_run.add_argument("--out", default="./reports", help="Output directory.")
    p_run.set_defaults(func=cmd_run)

    return p

def main(argv: Optional[List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        return interactive_menu()

    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        parser.print_help()
        return 1

    try:
        return int(args.func(args))
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 2
    except IsADirectoryError as e:
        print(f"ERROR: {e}")
        return 2
    except ValueError as e:
        print(f"ERROR: {e}")
        return 2
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 3

if __name__ == "__main__":
    raise SystemExit(main())
