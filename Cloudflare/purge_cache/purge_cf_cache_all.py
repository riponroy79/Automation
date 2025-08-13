
#!/usr/bin/env python3
"""
Created by: Ripan Kumar Ray
Purge Cloudflare cache for all ACTIVE zones and write a timestamped CSV report.

Usage:
  python purge_cf_cache_all.py                    # real run
  python purge_cf_cache_all.py --dry-run          # list what would be purged
  python purge_cf_cache_all.py --account-id ABC   # restrict to one account
  python purge_cf_cache_all.py --concurrency 8    # parallel workers
  python purge_cf_cache_all.py --windows-safe-name# replace : in filename

Token precedence:
  1) --token flag
  2) CLOUDFLARE_API_TOKEN env var
  3) API_TOKEN constant (hard-coded below)
"""

import os
import sys
import csv
import json
import argparse
from typing import List, Dict, Tuple
from datetime import datetime
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = "https://api.cloudflare.com/client/v4"

# ===========================
# 🔐 Hard-coded API Token
# ===========================
# Replace this with your actual API token (or use --token / env var).
API_TOKEN = "PUT_YOUR_CLOUDFLARE_API_TOKEN_HERE"

def _make_retry() -> Retry:
    """
    Build a Retry object compatible with both old and new urllib3:
      - urllib3 >= 1.26: uses 'allowed_methods'
      - urllib3 <  1.26: uses 'method_whitelist'
    """
    common_kwargs = dict(
        total=8,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
    )
    methods = frozenset(["GET", "POST"])
    try:
        # Newer urllib3
        return Retry(allowed_methods=methods, **common_kwargs)
    except TypeError:
        # Older urllib3
        return Retry(method_whitelist=methods, **common_kwargs)

def build_session(token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "cf-purge-all/1.2"
    })
    retry = _make_retry()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s

def list_active_zones(session: requests.Session, account_id: str = None) -> List[Dict]:
    zones = []
    page = 1
    per_page = 50
    while True:
        params = {
            "status": "active",
            "page": page,
            "per_page": per_page,
            "order": "name",
            "direction": "asc"
        }
        if account_id:
            params["account.id"] = account_id

        r = session.get(f"{API_BASE}/zones", params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
        if not data.get("success", False):
            raise RuntimeError(f"Failed listing zones: {data}")

        result = data.get("result", [])
        zones.extend(result)

        total_pages = data.get("result_info", {}).get("total_pages", page)
        if page >= total_pages:
            break
        page += 1
    return zones

def purge_zone_cache(session: requests.Session, zone_id: str) -> Dict:
    r = session.post(
        f"{API_BASE}/zones/{zone_id}/purge_cache",
        data=json.dumps({"purge_everything": True}),
        timeout=120
    )
    try:
        payload = r.json()
    except Exception:
        payload = {"raw_text": r.text}
    if not r.ok or not payload.get("success", False):
        raise RuntimeError(json.dumps(payload))
    return payload

def timestamp_for_filename(windows_safe: bool = False) -> str:
    # Example: 13-Aug-2025_17:34:11 (local time)
    ts = datetime.now().strftime("%d-%b-%Y_%H:%M:%S")
    return ts.replace(":", "-") if windows_safe else ts

def prepare_report_path(windows_safe: bool = False) -> Path:
    ts = timestamp_for_filename(windows_safe)
    name = f"Cloudflare_cache_clear_{ts}.csv"
    return Path.cwd() / name

def write_report(path: Path, rows: List[Dict]) -> None:
    fieldnames = [
        "timestamp",
        "zone_name",
        "zone_id",
        "status",      # success / failed / dry-run
        "message"      # response info or error
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Purge Cloudflare cache for all ACTIVE zones and write a CSV report.")
    parser.add_argument("--token", help="Cloudflare API Token (overrides others).")
    parser.add_argument("--account-id", help="(Optional) Restrict to a specific account ID.")
    parser.add_argument("--concurrency", type=int, default=6, help="Parallel purge workers (default: 6).")
    parser.add_argument("--dry-run", action="store_true", help="Show which zones would be purged; do not purge.")
    parser.add_argument("--windows-safe-name", action="store_true",
                        help="Use a filename that replaces ':' with '-' for Windows compatibility.")
    args = parser.parse_args()

    token = args.token or os.getenv("CLOUDFLARE_API_TOKEN") or API_TOKEN
    if not token or token == "PUT_YOUR_CLOUDFLARE_API_TOKEN_HERE":
        print("ERROR: Set your API token in the script, or pass --token, or set CLOUDFLARE_API_TOKEN.", file=sys.stderr)
        sys.exit(2)

    session = build_session(token)

    print("Fetching active zones…", flush=True)
    try:
        zones = list_active_zones(session, account_id=args.account_id)
    except Exception as e:
        print(f"ERROR listing zones: {e}", file=sys.stderr)
        # still write an empty report for traceability
        report_path = prepare_report_path(args.windows_safe_name)
        write_report(report_path, [])
        print(f"Empty report written: {report_path}")
        sys.exit(1)

    if not zones:
        print("No active zones found (nothing to purge).")
        report_path = prepare_report_path(args.windows_safe_name)
        write_report(report_path, [])
        print(f"Empty report written: {report_path}")
        return

    print(f"Found {len(zones)} active zone(s):")
    for z in zones:
        print(f"  - {z.get('name')} (id: {z.get('id')})")

    report_rows: List[Dict] = []
    if args.dry_run:
        print("\nDRY RUN: No purges executed.")
        now_iso = datetime.now().isoformat(timespec="seconds")
        for z in zones:
            report_rows.append({
                "timestamp": now_iso,
                "zone_name": z.get("name"),
                "zone_id": z.get("id"),
                "status": "dry-run",
                "message": "Would purge (purge_everything=true)"
            })
        report_path = prepare_report_path(args.windows_safe_name)
        write_report(report_path, report_rows)
        print(f"Report written: {report_path}")
        return

    print("\nPurging caches (purge_everything=true)…")
    successes: List[str] = []
    failures: List[Tuple[str, str]] = []

    def do_purge(z):
        name = z.get("name")
        zid = z.get("id")
        try:
            resp = purge_zone_cache(session, zid)
            successes.append(name)
            print(f"OK  - {name}")
            msg = json.dumps(resp.get("result", {})) if isinstance(resp, dict) else "success"
            return {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "zone_name": name,
                "zone_id": zid,
                "status": "success",
                "message": msg
            }
        except Exception as e:
            failures.append((name, str(e)))
            print(f"ERR - {name}: {e}", file=sys.stderr)
            return {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "zone_name": name,
                "zone_id": zid,
                "status": "failed",
                "message": str(e)
            }

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futures = [ex.submit(do_purge, z) for z in zones]
        for fut in as_completed(futures):
            report_rows.append(fut.result())

    report_path = prepare_report_path(args.windows_safe_name)
    write_report(report_path, report_rows)

    print("\n=== Summary ===")
    print(f"Purged successfully: {len(successes)}")
    for n in successes:
        print(f"  ✓ {n}")
    if failures:
        print(f"\nFailed: {len(failures)}")
        for n, err in failures:
            print(f"  ✗ {n} → {err}")

    print(f"\nReport written: {report_path}")
    sys.exit(0 if not failures else 1)

if __name__ == "__main__":
    main()
