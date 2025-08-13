### Purge Cloudflare cache for all ACTIVE zones and write a timestamped CSV report.
```
Usage:
  python purge_cf_cache_all.py                    # real run
  python purge_cf_cache_all.py --dry-run          # list what would be purged
  python purge_cf_cache_all.py --account-id ABC   # restrict to one account
  python purge_cf_cache_all.py --concurrency 8    # parallel workers
  python purge_cf_cache_all.py --windows-safe-name# replace : in filename
```
### Replace the placeholder string inside script with your actual token.
```
API_TOKEN = "PUT_YOUR_CLOUDFLARE_API_TOKEN_HERE"
```
### How to create the token in the Cloudflare dashboard:
1. Go to Profile → API Tokens → Create Token
2. Choose Custom Token
3. Add the permissions below-
    Zone → Zone: Read (so it can list your zones)
    Zone → Cache Purge: Purge (so it can purge caches)
4. Zone Resources: Scope the token to either All zones in your account or only the specific zones you want the script to purge.
5. Copy the token and paste it into the script where API_TOKEN is defined.



# Cloudflare Cache Purge for All Active Zones

This Python automation script purges the entire cache for **all active zones** in your Cloudflare account.  
It supports **parallel execution**, **retry handling**, and **CSV reporting** with timestamps for auditing.

---

## Features
- Purges cache (`purge_everything=true`) for every **active zone** available to your API token.
- Handles pagination and Cloudflare API rate limits automatically.
- Runs in **parallel** to speed up purging multiple zones.
- **Dry run** mode to preview without purging.
- Saves a **CSV report** with zone name, ID, status, and messages.
- Works with both new and old `urllib3` versions (compatibility fix for `allowed_methods` / `method_whitelist`).

---

## Requirements
- Python 3.6+
- `requests` library (install via `pip install requests`)

---

## Cloudflare API Token Setup

Create a token in Cloudflare Dashboard:

**Minimum permissions:**
- `Zone → Zone: Read`
- `Zone → Cache Purge: Edit`

**Optional (only if using `--account-id`):**
- `Account → Account Settings: Read`

**Scope:**  
Set to `All zones` or only the specific zones you want purged.

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/riponroy79/YOUR_REPO.git
   cd YOUR_REPO

Output
Console: Shows progress with OK / ERR status per zone.

CSV Report: Saved in the same directory with a name like:

Cloudflare_cache_clear_13-Aug-2025_17:34:11.csv

Example CSV contents:

timestamp,zone_name,zone_id,status,message
2025-08-13T17:34:11,example.com,123abc456def,success,"{}"
2025-08-13T17:34:12,another.com,789ghi012jkl,failed,"Error message here"

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
