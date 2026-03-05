# IOWN Market Data Auto-Fetcher

Runs every weekday at 3:05 PM CST via GitHub Actions. Fetches all 51 IOWN holdings from Finnhub + macro data from FMP. Output saved to `latest.txt`.

## Setup

1. Create this repo on GitHub (e.g. `richacarson/iown-data`)
2. Push all files
3. Go to **Settings → Secrets and variables → Actions**
4. Add two repository secrets:
   - `FINNHUB_KEY` — your Finnhub API key
   - `FMP_KEY` — your FMP API key
5. Go to **Settings → Pages** → Source: **Deploy from a branch** → Branch: **main** → Save
6. Go to **Settings → Actions → General** → Workflow permissions: **Read and write permissions** → Save

## How it works

- GitHub Action runs at 3:05 PM CST (21:05 UTC) on weekdays
- Fetches macro data from FMP (8 calls: indices, VIX, gold, oil, BTC, sectors)
- Fetches 51 holdings from Finnhub (51 calls with 70ms rate limiting)
- Writes `latest.txt` and commits to repo
- Claude reads `https://richacarson.github.io/iown-data/latest.txt` when you say "go"

## Manual trigger

You can also trigger a fetch anytime from the **Actions** tab → **IOWN Market Data Fetch** → **Run workflow**.

## DST note

The cron runs at 21:05 UTC = 3:05 PM CST. During daylight saving (CDT, mid-March to early November), change to `5 20 * * 1-5` for 3:05 PM CDT.
