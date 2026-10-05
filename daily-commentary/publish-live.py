#!/usr/bin/env python3
"""Render and publish a Paradiem FCI Market Commentary to the live site.

The reader site (https://iown-data.pages.dev) is served by Cloudflare Pages from
the branch claude/live. This script lets the daily routine, which can push only
to claude/* branches, publish without depending on GitHub Actions.

Usage (run from anywhere inside the iown-data checkout):
  python3 daily-commentary/publish-live.py render  YYYY-MM-DD
      Render commentaries/Paradiem_FCI_Market_Commentary_YYYY-MM-DD.pdf from the
      HTML in the working tree and print its page count. Use this to check the
      two-page target before publishing.
  python3 daily-commentary/publish-live.py publish YYYY-MM-DD
      Render the PDF if it is missing, then rebuild claude/live as:
        origin/main
        + any commentary files and manifest entries that are on claude/live but
          never reached main (e.g. while GitHub Actions was down)
        + today's HTML, PDF and manifest entry (taken from the working tree)
      and push it (fast-forward, never force). Cloudflare deploys it in ~1 minute.

Inputs expected in the working tree before "publish":
  commentaries/Paradiem_FCI_Market_Commentary_YYYY-MM-DD.html
  commentary-manifest.json containing an entry whose "date" is YYYY-MM-DD

main stays the source of truth for everything else: the live branch is rebuilt
from main on every publish, and main's copy wins for any file both branches have.
The "Publish commentary from claude branch" Action still copies each edition to
main when Actions is healthy; nothing here depends on it.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

LIVE = "claude/live"
SITE = "https://iown-data.pages.dev"
MANIFEST = "commentary-manifest.json"


def sh(*args, check=True):
    r = subprocess.run(args, text=True, capture_output=True)
    if check and r.returncode != 0:
        sys.exit(f"command failed: {' '.join(args)}\n{r.stdout}{r.stderr}")
    return r


def git(*args, check=True):
    return sh("git", *args, check=check)


def paths(date):
    stem = f"commentaries/Paradiem_FCI_Market_Commentary_{date}"
    return stem + ".html", stem + ".pdf"


def dump_manifest(entries):
    # Same formatting as the existing file and the GitHub Action.
    return json.dumps(entries, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- rendering
def render(html_path, pdf_path):
    """Letter PDF via headless Chromium, with Gelasio/Carlito loaded from the
    repo so the output matches the GitHub-rendered PDFs even when Google Fonts
    is unreachable."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sh(sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "playwright")
        from playwright.sync_api import sync_playwright

    fonts_css = os.path.abspath("daily-commentary/fonts/fonts.css")
    src = open(html_path, encoding="utf-8").read()
    # Drop the Google Fonts links (blocked in cloud sessions) and use local copies.
    src = re.sub(r'<link[^>]+fonts\.(googleapis|gstatic)\.com[^>]*>\s*', "", src)
    src = src.replace("</head>", f'<link rel="stylesheet" href="file://{fonts_css}">\n</head>', 1)
    tmp = os.path.join(os.path.dirname(os.path.abspath(html_path)), ".render-tmp.html")
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(src)
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(args=["--no-sandbox"])
            except Exception:
                # Cloud sessions ship Chromium here; don't download another.
                browser = p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
                                            args=["--no-sandbox"])
            page = browser.new_page()
            page.goto("file://" + tmp, wait_until="networkidle", timeout=90000)
            page.evaluate("document.fonts ? document.fonts.ready.then(() => true) : true")
            page.pdf(path=pdf_path, print_background=True, prefer_css_page_size=True)
            browser.close()
    finally:
        os.remove(tmp)
    return page_count(pdf_path)


def page_count(pdf_path):
    try:
        from pypdf import PdfReader
    except ImportError:
        sh(sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "pypdf")
        from pypdf import PdfReader
    return len(PdfReader(pdf_path).pages)


# ---------------------------------------------------------------- publishing
def fetch():
    git("fetch", "-q", "origin", "+refs/heads/main:refs/remotes/origin/main")
    have_live = git("fetch", "-q", "origin", f"+refs/heads/{LIVE}:refs/remotes/origin/{LIVE}",
                    check=False).returncode == 0
    return have_live


def show(rev, path):
    r = git("show", f"{rev}:{path}", check=False)
    return r.stdout if r.returncode == 0 else None


def build_and_push(date, html, pdf, entry, html_bytes, pdf_bytes):
    have_live = fetch()
    base = f"origin/{LIVE}" if have_live else "origin/main"
    git("checkout", "-q", "-f", "-B", LIVE, base)
    # Index + working tree := main's tree (HEAD stays on claude/live so the push
    # is a fast-forward).
    git("read-tree", "-u", "--reset", "origin/main")

    main_entries = json.loads(show("origin/main", MANIFEST) or "[]")
    main_dates = {e.get("date") for e in main_entries}
    merged = list(main_entries)
    carried = []
    if have_live:
        ls = lambda rev: set(git("ls-tree", "-r", "--name-only", rev, "--", "commentaries/").stdout.split())
        only_live = sorted(ls(f"origin/{LIVE}") - ls("origin/main"))
        if only_live:
            git("checkout", f"origin/{LIVE}", "--", *only_live)
        live_entries = json.loads(show(f"origin/{LIVE}", MANIFEST) or "[]")
        for e in live_entries:
            if e.get("date") not in main_dates and e.get("date") != date:
                merged.append(e)
                carried.append(e.get("date"))

    merged = [e for e in merged if e.get("date") != date] + [entry]
    merged.sort(key=lambda e: e.get("date", ""), reverse=True)  # stable; newest first

    with open(html, "wb") as fh:
        fh.write(html_bytes)
    to_add = [html, MANIFEST]
    if pdf_bytes is not None:
        with open(pdf, "wb") as fh:
            fh.write(pdf_bytes)
        to_add.append(pdf)
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        fh.write(dump_manifest(merged))
    git("add", "--", *to_add)

    if have_live and git("write-tree").stdout.strip() == \
            git("rev-parse", f"origin/{LIVE}^{{tree}}").stdout.strip():
        return "unchanged (already live)", carried

    msg = f"Commentary {date}: {entry.get('headline', '').strip()}"
    git("commit", "-q", "-m", msg, "-m", "Published to claude/live by daily-commentary/publish-live.py")
    r = git("push", "-q", "origin", f"HEAD:refs/heads/{LIVE}", check=False)
    if r.returncode != 0:
        return "rejected:" + (r.stderr or r.stdout).strip(), carried
    return "pushed", carried


def publish(date):
    html, pdf = paths(date)
    if not os.path.isfile(html):
        sys.exit(f"missing {html}")
    entries = json.load(open(MANIFEST, encoding="utf-8"))
    entry = next((e for e in entries if e.get("date") == date), None)
    if entry is None:
        sys.exit(f"{MANIFEST} in the working tree has no entry for {date}")
    expected = os.path.basename(html)
    if entry.get("content") != expected:
        sys.exit(f'manifest entry "content" is {entry.get("content")!r}, expected {expected!r}')

    pages = None
    if not os.path.isfile(pdf):
        try:
            pages = render(html, pdf)
        except Exception as exc:  # publish the page anyway; the PDF can follow
            print(f"WARNING: PDF render failed ({exc}); publishing without a PDF")
    else:
        pages = page_count(pdf)
    html_bytes = open(html, "rb").read()
    pdf_bytes = open(pdf, "rb").read() if os.path.isfile(pdf) else None
    if pdf_bytes is None:
        entry = {k: v for k, v in entry.items() if k != "pdf"}
    elif entry.get("pdf") != os.path.basename(pdf):
        entry = {**entry, "pdf": os.path.basename(pdf)}

    for attempt in (1, 2, 3):
        status, carried = build_and_push(date, html, pdf, entry, html_bytes, pdf_bytes)
        if not status.startswith("rejected"):
            break
        print(f"push attempt {attempt} rejected; refetching and retrying")
    else:
        sys.exit(f"push to {LIVE} failed: {status}")

    sha = git("rev-parse", "--short", "HEAD").stdout.strip()
    print(f"{status}: {LIVE} @ {sha}")
    if carried:
        print("carried over editions not yet on main:", ", ".join(sorted(carried)))
    print(f"PDF pages: {pages if pages is not None else 'none'}")
    print(f"page: {SITE}/commentaries/{os.path.basename(html)}")
    print(f"reader: {SITE}/")


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("render", "publish") \
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", sys.argv[2]):
        sys.exit(__doc__)
    os.chdir(git("rev-parse", "--show-toplevel").stdout.strip())
    cmd, date = sys.argv[1], sys.argv[2]
    if cmd == "render":
        html, pdf = paths(date)
        print(f"{pdf}: {render(html, pdf)} pages")
    else:
        publish(date)


if __name__ == "__main__":
    main()
