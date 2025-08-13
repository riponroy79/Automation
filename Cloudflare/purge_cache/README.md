## Purge Cloudflare cache for all ACTIVE zones and write a timestamped CSV report.
```
Usage:
  python purge_cf_cache_all.py                    # real run
  python purge_cf_cache_all.py --dry-run          # list what would be purged
  python purge_cf_cache_all.py --account-id ABC   # restrict to one account
  python purge_cf_cache_all.py --concurrency 8    # parallel workers
  python purge_cf_cache_all.py --windows-safe-name# replace : in filename
```
# Replace the placeholder string inside script with your actual token.
```
API_TOKEN = "PUT_YOUR_CLOUDFLARE_API_TOKEN_HERE"
```
# How to create the token in the Cloudflare dashboard:
1. Go to Profile → API Tokens → Create Token
2. Choose Custom Token
3. Add the permissions below-
    Zone → Zone: Read (so it can list your zones)
    Zone → Cache Purge: Purge (so it can purge caches)
4. Zone Resources: Scope the token to either All zones in your account or only the specific zones you want the script to purge.
5. Copy the token and paste it into the script where API_TOKEN is defined.
