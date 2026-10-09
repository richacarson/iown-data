# Paradiem FCI Market Commentary — daily routine

These are the complete, current instructions for the Market Commentary routine
(weekdays, starting 3:03 PM Central, with a closing-price update at 3:36 PM
Central). The routine's own prompt only points here, so change the process by
editing this file.

You produce and publish today's commentary end to end with no human in the
loop. Carson Rich gets a notification when you finish and reads your final
message on his phone. Work autonomously and don't stop to ask questions. It
publishes under the Paradiem name, so accuracy and compliance come before
speed. All times below are America/Chicago.

## Timing: publish first, then update

A normal day has two publishes:

1. **First publish, as soon as the edition is ready.** Once the page passes QA,
   the independent fact-check and the two-page check (usually 3:10–3:25 PM),
   publish it right away with the prices you have. Never hold the first publish
   to wait for official closes. Carson and the Tuesday Update are waiting on it.
2. **Closing-price update at 3:36 PM (Step 6).** Re-pull the official closes and
   republish only if a displayed figure changed.

Skip the first publish only when the edition isn't ready until 3:36 PM or
later. In that case, re-pull the official closes and publish once (Step 5.4).

**How to wait.** Whenever a step says to wait (until 3:03 in Step 0, until
3:36 in Step 6, or for Cloudflare), wait inside the session with foreground
`sleep` commands of at most 9 minutes each (`sleep 540`), checking the clock
between them.
- Don't end your turn while waiting, and don't run the wait as a background
  task.
- Having the edition unpublished on your working branch while you wait is
  expected. If a stop hook asks you to commit or push, don't. Carry on with
  the steps; `publish-live.py` does the pushing.

## How publishing works

The reader site is https://iown-data.pages.dev, served by Cloudflare Pages from
the branch `claude/live` of richacarson/iown-data. This routine can push only
to `claude/*` branches. `daily-commentary/publish-live.py` renders the PDF and
publishes: it rebuilds `claude/live` from main plus today's edition (and any
earlier edition that hasn't reached main yet) and pushes it fast-forward;
Cloudflare deploys it in about a minute. A GitHub Action then copies the
edition to main; the live site doesn't depend on it. Never push to main, never
force-push, and never use a personal token.

## Authoritative context

If memory tools are available, read these first; they hold format, voice and
pipeline rules: `/projects/019cb5b1-f18e-7673-8867-c23239106740/overview.md`,
`commentary-format.md`, `daily-workflow.md`, `tools-and-resources.md`. This file
overrides older pipeline details in memory (push steps, CI PDF, file naming)
and in `COMMENTARY-INSTRUCTIONS.md`. Where newer memory conflicts with this
file on voice or format, follow the memory and say so in one line of the final
message.

## FMP connector: retry before giving up

FMP (the connector) is the only source for prices and the performance figures.
Its connection sometimes drops ("session expired", tools disappearing).

- If any FMP call fails or the FMP tools are missing, wait 60 seconds, reload
  them with ToolSearch (for example `select:mcp__FMP__quote,mcp__FMP__indexes,mcp__FMP__commodity,mcp__FMP__economics,mcp__FMP__marketHours,mcp__FMP__calendar,mcp__FMP__chart`,
  or a keyword search for "FMP quote"), and try again. Keep retrying for up to
  15 minutes.
- Never substitute another source (Yahoo, Stooq, web pages, a direct API call)
  for FMP in the performance figures, the market ticker or mover returns. If
  FMP is still unavailable after 15 minutes, publish nothing and say so in the
  final message.

## Step 0 — Guards

1. If it is earlier than 3:00 PM (the schedule can shift with daylight saving
   time), wait until 3:03 PM before doing anything else.
2. If today is not a US equity trading day (FMP market hours/holidays), stop:
   publish nothing and reply with one line saying so.
3. In the iown-data checkout: `git fetch origin main claude/live`. If
   `origin/main:commentary-manifest.json` or
   `origin/claude/live:commentary-manifest.json` already has an entry for today,
   stop: publish nothing and reply with one line saying so.
4. Create a working branch from main:
   `git checkout -B claude/commentary-YYYY-MM-DD origin/main`.
5. rich-report and dashboard: use the attached checkouts (`git pull` first); if
   they aren't attached, `git clone --depth 1` https://github.com/richacarson/rich-report
   and https://github.com/richacarson/dashboard next to iown-data.

## Step 1 — Performance figures

All figures come from `daily-commentary/perf.py`, which reproduces the
dashboard's Trailing Total Returns exactly (verified to the hundredth on
2026-09-28). Don't compute returns, spreads, gaps, bar widths, counts or
contributions by hand.

1. Pull FMP `batch-quote` (not `batch-quote-short` for this first pull) for all
   50 holdings plus DVY, SPY, IUSG, IBIT and ETHA, in calls of 28 or fewer
   symbols. The holdings are the keys of `"holdings"` in
   `dashboard/public/portfolio-history-dividend.json` and
   `portfolio-history-growth.json`.
2. Write them to a scratch file (not in the repo), e.g. `/tmp/quotes.json`,
   as `{"SYMBOL": [price, previousClose], ...}`.
3. Check FMP `dividends-calendar` for today. If DVY, SPY or IUSG goes
   ex-dividend today, pass `--exdiv SYMBOL=amount` and note it in the final
   message.
4. Run `python3 daily-commentary/perf.py /tmp/quotes.json --dashboard <path to dashboard checkout>`.
   It prints and saves (`perf_out.json` next to the quotes file): sleeve and
   benchmark 1-day and YTD (displayed, two decimals), YTD spreads (Dividend vs
   DVY, Growth vs IUSG), 1-day gaps in points, bar widths, holdings up/down,
   per-holding contributions, top and bottom movers, IBIT/ETHA, and flags
   (stale dashboard data, holding counts). Carry any flags to the final message.

## Step 2 — Market data and narrative

- Today's Morning Brief (`rich-report/briefs/YYYY-MM-DD.html`) is silent
  context only: connect the morning thesis to how the session resolved without
  repeating it.
- FMP `index-quote` for ^GSPC, ^IXIC, ^DJI, ^VIX (one call each).
- Brent: FMP `commodities-quote` BZUSD, cross-checked against a news source.
  FMP's previousClose can belong to a different contract month (on 2026-09-29
  it showed a false −9%), so always confirm the day's Brent move against the
  news and name the contract month if it matters.
- Treasury yields: FMP `economics` `treasury-rates` for the official 10-year and
  30-year. Today's official row often posts late in the afternoon; if it's not
  there yet, use a reputable market quote for now and replace it with the
  official figure in the 3:36 update.
- 8–10 web searches for the session narrative and for the catalysts behind the
  notable movers. Don't draft the commentary in chat first.
- Keep a source log as you go: for every fact that doesn't come from FMP or
  perf.py, record the publisher, title, date and URL. It becomes the Sources
  section.
- Roster check: confirm the holdings in the dashboard files match
  `iown-data/fetch-data.js` and note any change. Never present EIX, CTRA or DVN
  as holdings. IBIT and ETHA are digital-asset ETFs: mention them in prose
  only, never as movers.

## Step 3 — Build the page

Use the most recent published edition in `commentaries/` as the layout base. It
carries the current head, CSS (including the `.sources` styles), embedded logo,
running head/foot and section wrappers. Replace everything between
`<tbody><tr><td>` and `</td></tr></tbody>`, update the date in the `<title>` and
the running head, and save as
`commentaries/Paradiem_FCI_Market_Commentary_YYYY-MM-DD.html`.

Structure, as in recent issues:
- Cover: kicker, headline with the emphasis phrase in `<i>`, subhead ending with
  each sleeve's day return vs its benchmarks.
- Market ticker: S&P 500, Nasdaq, Dow, VIX, Brent.
- Two sleeve cards with bars and the YTD line.
- The Session, inside `<div class="flow cmt-flow">`: three paragraphs (market;
  Dividend Strategy; Growth Portfolio) plus a centered pull quote ending
  "<b>Think Like an Owner.</b>"
- FCI Holdings · Notable Movers: four winners and four decliners, each group in
  `<div class="movers movers-grid">`.
- Year-to-Date Standing band with the `.bs` spread lines.
- Sources (see below), the last block before `</td></tr></tbody>`.

Mechanics:
- Every `up`/`dn`/`flat` class and every ▲ (`&#9650;`) / ▼ (`&#9660;`) arrow
  matches the figure's actual sign.
- Bar widths come from perf.py.
- Sleeve tags: "Beat DVY + SPY" / "Trailed DVY + SPY", or the combined format
  when a sleeve beats one benchmark and trails the other ("Beat DVY · Trailed
  SPY"). Growth: "Beat IUSG" / "Trailed IUSG".
- Echo both YTD spreads once in the closing sentence of the Growth paragraph.
- Negatives use the Unicode minus − (U+2212), never a hyphen.

### Voice: a CIO wrote this

The commentary reads as if Paradiem's CIO wrote it: measured,
ownership-minded, direct about numbers, never breathless or alarmist (Eric's
standing directive).

- **No sources in the body.** No "per CNBC", "according to Yahoo", "Benzinga
  reports", "Reuters said", "data from…", "X attributes the move to…". State
  the facts plainly; the sources go in the Sources section at the bottom.
  - Before: "…its first close above 7,800 per CNBC… Vistra rose 10.77% as
    nuclear generators rallied on the Google–Constellation agreement, per
    24/7 Wall St…"
  - After: "…its first close above 7,800… Vistra rose 10.77% as investors
    repriced nuclear generators around the Google–Constellation agreement…"
- Describing what a company, agency or official did is reporting, not
  attribution, and is fine: "Marvell set a fiscal 2031 revenue target…", "the
  Department of Energy offered the company a conditional loan…". At most one
  named analyst action per edition.
- Verification doesn't relax because the source moved. Every claim must be
  checked against a reliable source in the source log. Never claim "record",
  "all-time high", "first since" or "highest/lowest since" unless you've verified
  it (for index milestones, with FMP's EOD history) and listed a source.
- When you find no catalyst, write "without a company-specific catalyst" (or
  just end the sentence) rather than inventing one. Don't write "no news":
  a company may have issued a routine release that didn't move the stock.
- Banned words: "destroyed", "carnage", "cratered", "exploded", "hammered",
  "bloodbath" and similar fear language. No recommendations or price targets.
- Branding: Paradiem / FCI only; never "IOWN". Always "Growth Portfolio", never
  "Growth Hybrid".

### Sources section

```html
  <!-- ══ SOURCES ══ -->
  <div class="sources">
    <div class="src-h">Sources</div>
    <ol>
      <li>Publisher, &ldquo;<a href="URL">Title</a>,&rdquo; Oct. 6, 2026.</li>
      ...
      <li>Market data: Financial Modeling Prep. Strategy returns: Paradiem FCI portfolio records.</li>
    </ol>
  </div>
```

- Works-cited style: Publisher, "Title" (linked), abbreviated date. For a press
  release, the company is the publisher. For Treasury yields:
  "U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates, <dates>."
- One entry per source actually relied on, in order of first use. Usually 5–8,
  and no more than 9 including the closing market-data line.
- Every non-FMP fact on the page traces to an entry, and every entry supports
  something on the page.

## Step 4 — QA, then an independent fact-check

Automated QA (strip the base64 logo and the `<style>` block before scanning):
- zero leftover ⟪⟫ tokens and no leftover text from the prior issue (its date,
  headline or figures);
- U+2212 for every negative; no banned vocabulary; no "IOWN" or "Growth
  Hybrid";
- no inline attributions in the body (case-insensitive scan above the Sources
  block for "per ", "according to", "reports", "reported", "said", "says",
  "data from", and publisher names such as CNBC, Reuters, Bloomberg, Yahoo,
  Benzinga, MarketWatch, Barron's, WSJ, TheStreet, 24/7, Motley Fool,
  Investing.com, Zacks; review each hit, since some are legitimate company
  actions);
- no non-roster tickers as movers;
- every figure matches perf.py (`perf_out.json`): sleeve and benchmark
  returns, YTD, spreads, gaps, bar widths, counts, contributions and mover
  percentages;
- up/dn classes and arrows match each sign.

Then launch a separate agent that hasn't seen your reasoning. Give it the file
path, the quotes file, `perf_out.json`, the index/Brent/Treasury quotes and the
source log. Have it:
- recompute every number with perf.py's method;
- check every factual claim against the listed sources;
- confirm each Sources entry is accurate and actually supports a claim;
- flag inline attributions and compliance problems.

Fix everything it finds.

## Step 5 — Publish

1. Prepend today's entry at index 0 of `commentary-manifest.json` (dedupe by
   date first; keep the existing JSON formatting). Fields: date, headline,
   subhead, direction (`up`/`down` by the S&P 500), content (HTML file name),
   pdf (PDF file name).
2. `python3 daily-commentary/publish-live.py render YYYY-MM-DD`: it prints the
   page count, using the fonts in `daily-commentary/fonts/` because Google Fonts
   is blocked here. Verify the PDF with pypdf: exactly two pages, headline words
   present (check individual words, since pypdf collapses spaces at italic
   boundaries), no leftover tokens, correct minus signs.
3. Two-page fit: page 2 starts at the pull quote, so only page-2 content
   (Growth paragraph, mover notes, band, Sources) affects overflow. If it runs
   to three pages, shorten the Growth paragraph and the mover notes (one or two
   lines each) and render again. Don't shrink the Sources type below 8px or
   change the page's other CSS.
4. Only if it is already 3:36 PM or later: re-pull all quotes and indexes first
   and rebuild the figures from fresh `perf.py` output (official closes are in
   by then), so Step 6 isn't needed. Before 3:36 PM, don't wait: publish now
   and do Step 6 afterward.
5. `python3 daily-commentary/publish-live.py publish YYYY-MM-DD`. It must print
   "pushed: claude/live @ <sha>" (or "unchanged (already live)"). Don't push any
   other branch.
6. Verify live: wait about 90 seconds, then WebFetch
   `https://iown-data.pages.dev/commentary-manifest.json?v=<unix time>` and
   confirm today's entry is first, and WebFetch
   `https://iown-data.pages.dev/commentaries/Paradiem_FCI_Market_Commentary_YYYY-MM-DD.html?v=<unix time>`
   and confirm the headline. Retry every 60 seconds for up to 6 minutes.
7. If the script's push fails, fall back:
   - `git checkout -B claude/commentary-YYYY-MM-DD origin/main`;
   - add the HTML, PDF and manifest and commit ("Commentary YYYY-MM-DD: <headline>");
   - `git push -u origin claude/commentary-YYYY-MM-DD`, and say so in the final
     message. The GitHub Action publishes it to main when Actions is running.

## Step 6 — Closing-price update at 3:36 PM

At 3:03 FMP still shows the last trade before the closing auction; official
closing prints are in by about 3:36 PM. If you published before 3:36 PM:

1. Wait until 3:36 PM, using foreground sleeps (see "Timing").
2. Re-pull every quote with `batch-quote` (all holdings, DVY, SPY, IUSG, IBIT,
   ETHA), the four index quotes, BZUSD, and FMP `treasury-rates` (today's
   official row, if posted). Write a new quotes file and re-run perf.py.
3. Compare every displayed figure with the published page: sleeve and benchmark
   returns, YTD, spreads, gaps, bars, counts, contributions, mover percentages
   and prices, index levels and changes, VIX, the 10-year.
4. If nothing displayed changed, you're done; note "closing-price check: no
   changes" in the final message.
5. If anything changed:
   - update it everywhere it appears (cover subhead, ticker, cards, bars, prose,
     movers, YTD band and the manifest subhead), and the mover lists if the
     ranking changed;
   - re-run the automated QA and have the fact-check agent re-verify only the
     changed figures;
   - re-render, confirm two pages, and run `publish-live.py publish YYYY-MM-DD`
     again (it replaces today's entry);
   - verify live as in Step 5, and list what changed in the final message.

## Final message (for Carson's phone, no preamble)

- The headline.
- One line each for the Dividend Strategy and the Growth Portfolio: day and YTD
  vs benchmarks and the YTD spread.
- The reader link https://iown-data.pages.dev/.
- Any flags: data gaps, stale dashboard data, ex-dividend adjustments, contract
  rolls, fact-check fixes, FMP retries, and the result of the 3:36 closing-price
  update.
