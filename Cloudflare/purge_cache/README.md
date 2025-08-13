# Purge Cloudflare cache for all ACTIVE zones and write a timestamped CSV report.

This Python automation script purges the entire cache for **all active zones** in your Cloudflare account.  

---
## Features
- Purges cache (`purge_everything=true`) for every **active zone** available to your API token.
- Handles pagination and Cloudflare API rate limits automatically.
- Runs in **parallel** to speed up purging multiple zones.
- **Dry run** mode to preview without purging.
- Saves a **CSV report** with zone name, ID, status, and messages.

---
## Requirements
- Python 3.6+
- `requests` library (install via `pip install requests`)

---
## Cloudflare API Token Setup

Create a token in Cloudflare Dashboard:

**Minimum permissions:**
- `Zone → Zone: Read (so it can list your zones)`
- `Zone → Cache Purge: Purge (so it can purge caches)`

**Scope:**  
Set to `All zones` or only the specific zones you want purged.

---
Usage:
```
Usage:
  python purge_cf_cache_all.py                    # real run
  python purge_cf_cache_all.py --dry-run          # list what would be purged
  python purge_cf_cache_all.py --account-id ABC   # restrict to one account
  python purge_cf_cache_all.py --concurrency 8    # parallel workers
  python purge_cf_cache_all.py --windows-safe-name# replace : in filename
```

#Example Run
```
$ python purge_cf_cache_all.py
Fetching active zones…
Found 5 active zone(s):
  - example.com (id: 123abc456def)
  - another.com (id: 789ghi012jkl)

Purging caches (purge_everything=true)…
OK  - example.com
ERR - another.com: API error here

=== Summary ===
Purged successfully: 1
  ✓ example.com

Failed: 1
  ✗ another.com → API error here

Report written: Cloudflare_cache_clear_13-Aug-2025_17:34:11.csv
```
Example CSV contents:
```
timestamp,zone_name,zone_id,status,message
2025-08-13T17:34:11,example.com,123abc456def,success,"{}"
2025-08-13T17:34:12,another.com,789ghi012jkl,failed,"Error message here"
```
