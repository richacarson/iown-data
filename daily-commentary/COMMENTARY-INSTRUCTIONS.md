# Paradiem · FCI Market Commentary — Daily Build Guide

One self-contained HTML file per day **is** both the web page and the print-to-PDF
source. No Python, no build step, no ReportLab. Your Claude project fills the
template and commits it.

## Files
- **`commentary-template.html`** — the empty template. Copy it each day.
- **`commentary-example.html`** — a fully filled reference (2026-07-16). Open it to
  see the target result.
- **`paradiem-logo.png`** — the masthead logo (already in the repo). Keep the
  template in the same folder so `src="paradiem-logo.png"` resolves.

## Daily workflow
1. Copy `commentary-template.html` → `commentaries/IOWN_Market_Commentary_YYYY-MM-DD.html`.
2. Replace every `⟪TOKEN⟫`. Repeat the `.mover` rows for as many holdings as you list.
3. Commit. The page is viewable directly in a browser.
4. **PDF:** open the file in Chrome → Print → *Save as PDF* → paper **Letter**,
   margins **Default**, **Background graphics ON**. The `@page` rules size it correctly.

## Field reference
| Token | What goes there |
|---|---|
| `⟪DATE_LONG⟫` | `Thursday, July 16 2026` (appears in title + header) |
| `⟪HEADLINE_A⟫` / `⟪HEADLINE_EMPHASIS⟫` | Headline split in two. The emphasis half renders **gold italic** — put the punchy word(s) there (e.g. `Health Over` + `Hardware`). |
| `⟪SUBHEAD⟫` | One-to-two sentence deck. |
| `⟪SP_PCT⟫ ⟪NAS_PCT⟫ ⟪DOW_PCT⟫ ⟪VIX⟫ ⟪BRENT⟫` | Ticker values (magnitude only — the arrow + color are set by class, see below). |
| `⟪DIV_TAG⟫` / `⟪GRW_TAG⟫` | Short status, e.g. `Beat SPY`, `Trailed IUSG`. |
| `⟪DIV_PCT⟫ ⟪GRW_PCT⟫` | The sleeve's 1-day return (used in the big number AND the FCI bar row). |
| `⟪DVY_PCT⟫ ⟪SPY_PCT⟫ ⟪IUSG_PCT⟫` | Benchmark 1-day returns. |
| `⟪*_W⟫` | Bar width percentages — **computed**, see below. |
| `⟪DIV_YTD⟫ ⟪GRW_YTD⟫ ⟪DVY_YTD⟫ ⟪SPY_YTD⟫ ⟪IUSG_YTD⟫` | YTD figures (used in the sleeve YTD line AND the navy band). |
| `⟪LEAD_BOLD_SENTENCE⟫ + ⟪LEAD_REST⟫` | First paragraph. The bold sentence gets the drop cap. |
| `⟪SESSION_PARA_2⟫ ⟪PULL_QUOTE⟫ ⟪SESSION_PARA_3⟫` | Body + centered pull quote. |
| Movers: `⟪TKR⟫ ⟪PCT⟫ ⟪STRATEGY⟫ ⟪CATALYST⟫` | One `.mover` per holding. `⟪STRATEGY⟫` = `Dividend` or `Growth`. |
| `⟪NEWS_HEAD_n⟫ ⟪NEWS_BODY_n⟫` | Holdings-news items. |

## Direction & color (important — keeps it on-brand)
Green/red are **status colors, used on figures only**. You set them via a CSS class:
- Positive → class **`up`** (forest green). Negative → class **`dn`** (oxblood). VIX/neutral → **`flat`**.
- **Ticker & tags:** also swap the arrow glyph — up = `&#9650;` (▲), down = `&#9660;` (▼).
  Example down item: `<span class="tk-v dn">&#9660;&thinsp;1.45%</span>`.
- **Sleeve `up`/`dn`:** applies to the big number, the FCI bar value, and the tag.
  A trailing sleeve: big number `dn`, tag class `dn`, tag text `Trailed …`, arrow ▼.
- **Bars:** the FCI row bar carries class `me` (navy); benchmark bars stay taupe. Never
  color the bars green/red — only the value text.
- Write negatives with a real minus sign `−` (U+2212), not a hyphen.

## Bar-width math (`⟪*_W⟫`)
Bars show **magnitude**, left-anchored, on a shared scale so the two sleeves compare.
1. `MAXABS` = the largest absolute 1-day return among **all** rows in **both** sleeves
   (FCI + every benchmark shown).
2. For each row: `width = round( |return| / MAXABS * 100 )`.

Example (2026-07-16): rows are +1.19, +1.70, −0.52, −3.04, −1.69 → MAXABS = 3.04 →
FCI 39, DVY 56, SPY 17, Growth-FCI 100, IUSG 56.

## Optional / variable sections
- **No holdings news that day?** Delete the entire `Holdings News` block (its `.sec`
  heading + the `.flow` after it).
- **More or fewer movers?** Add/remove `.mover` rows freely; they reflow into two columns.
- **Longer days** paginate automatically in print; the header/footer repeat per page.

## Optional: wire into the existing reader
If you keep `index.html` (gate + archive), point each entry's link at the new file and
open it in a new tab, or drop the `.doc` inner markup in as the fragment. Either way the
standalone file is the source of truth and the PDF.
