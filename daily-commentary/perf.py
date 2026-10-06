#!/usr/bin/env python3
"""Paradiem FCI commentary figures, computed the way the dashboard computes them.

Verified against the live dashboard to the hundredth on 2026-09-28. Do every
figure on the page from this script's output rather than by hand.

Usage:
  python3 daily-commentary/perf.py QUOTES.json [--dashboard DIR] [--exdiv DVY=0.85 ...]

QUOTES.json maps each symbol to [price, previousClose] from FMP batch-quote,
for all 50 holdings plus DVY, SPY and IUSG (IBIT/ETHA optional), e.g.
  {"ABT": [98.17, 100.1], "ADI": [420.55, 419.1], ...}
--dashboard is the dashboard checkout (the folder that contains public/);
defaults to ../dashboard next to this repo.
--exdiv applies when a benchmark goes ex-dividend today (after the last date in
its benchmarks_tr series): pass the per-share dividend and the YTD base is
scaled by (1 - dividend / previousClose).

Prints a readable summary and writes perf_out.json next to QUOTES.json.
"""
import argparse
import datetime as dt
import json
import os
import sys

BASE = None  # last date <= Dec 31 of last year, set in main()
SLEEVES = (("dividend", ("DVY", "SPY")), ("growth", ("IUSG",)))


def last_le(rows, date, key):
    rows = [r for r in rows if r["date"] <= date]
    return rows[-1]["date"], rows[-1][key]


def r2(x):
    return round(x + 0.0, 2)


def main():
    global BASE
    ap = argparse.ArgumentParser()
    ap.add_argument("quotes")
    ap.add_argument("--dashboard")
    ap.add_argument("--exdiv", action="append", default=[])
    a = ap.parse_args()

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dash = a.dashboard or os.path.join(os.path.dirname(repo), "dashboard")
    pub = os.path.join(dash, "public")
    Q = {k: v for k, v in json.load(open(a.quotes)).items() if not k.startswith("_")}
    exdiv = {k: float(v) for k, v in (s.split("=") for s in a.exdiv)}
    BASE = f"{dt.date.today().year - 1}-12-31"

    out, flags, holdings = {}, [], {}
    for sleeve, bms in SLEEVES:
        d = json.load(open(os.path.join(pub, f"portfolio-history-{sleeve}.json")))
        h, cash = d["holdings"], d["cash"]
        holdings[sleeve] = h
        missing = [t for t in h if t not in Q]
        if missing:
            sys.exit(f"missing quotes for {sleeve}: {missing}")
        if len(h) != 25:
            flags.append(f"{sleeve} has {len(h)} holdings, expected 25")
        gen = dt.datetime.fromisoformat(d["generated"][:19])
        if (dt.datetime.utcnow() - gen).days > 3:
            flags.append(f"{sleeve} dashboard file generated {d['generated']} (more than 3 days old)")
        V = cash + sum(n * Q[t][0] for t, n in h.items())
        V0 = cash + sum(n * Q[t][1] for t, n in h.items())
        bdate, bval = last_le(d["portfolio"], BASE, "value")
        contrib = sorted(((n * (Q[t][0] - Q[t][1]) / V0 * 100, t) for t, n in h.items()), reverse=True)
        out[sleeve] = {"day": (V / V0 - 1) * 100, "ytd": (V / bval - 1) * 100,
                       "up": sum(Q[t][0] > Q[t][1] for t in h), "down": sum(Q[t][0] < Q[t][1] for t in h),
                       "contrib": [(t, r2(c)) for c, t in contrib]}
        for b in bms:
            if b not in Q:
                sys.exit(f"missing quote for benchmark {b}")
            bd, bc = last_le(d["benchmarks_tr"][b], BASE, "close")
            if b in exdiv:
                bc *= 1 - exdiv[b] / Q[b][1]
                flags.append(f"{b} ex-dividend today: YTD base scaled by dividend {exdiv[b]}")
            out[b] = {"day": (Q[b][0] / Q[b][1] - 1) * 100, "ytd": (Q[b][0] / bc - 1) * 100}

    disp = {k: {"day": r2(v["day"]), "ytd": r2(v["ytd"])} for k, v in out.items()}
    D, G = disp["dividend"], disp["growth"]
    res = {
        "display": disp,
        "spreads": {"dividend_vs_DVY": r2(D["ytd"] - disp["DVY"]["ytd"]),
                    "growth_vs_IUSG": r2(G["ytd"] - disp["IUSG"]["ytd"])},
        "day_gaps_pts": {"dividend_vs_DVY": r2(D["day"] - disp["DVY"]["day"]),
                         "dividend_vs_SPY": r2(D["day"] - disp["SPY"]["day"]),
                         "growth_vs_IUSG": r2(G["day"] - disp["IUSG"]["day"])},
        "holdings_up": {s: out[s]["up"] for s, _ in SLEEVES},
        "holdings_down": {s: out[s]["down"] for s, _ in SLEEVES},
        "contributions_pts": {s: out[s]["contrib"] for s, _ in SLEEVES},
        "flags": flags,
    }
    order = ["dividend", "DVY", "SPY", "growth", "IUSG"]
    mx = max(abs(disp[k]["day"]) for k in order) or 1
    res["bar_widths"] = {k: round(abs(disp[k]["day"]) / mx * 100) for k in order}
    movers = []
    for s, _ in SLEEVES:
        for t in holdings[s]:
            movers.append({"ticker": t, "sleeve": s, "pct": r2((Q[t][0] / Q[t][1] - 1) * 100), "price": Q[t][0]})
    movers.sort(key=lambda m: m["pct"], reverse=True)
    res["movers_top"], res["movers_bottom"] = movers[:8], movers[::-1][:8]
    res["other"] = {t: r2((Q[t][0] / Q[t][1] - 1) * 100) for t in ("IBIT", "ETHA") if t in Q}

    path = os.path.join(os.path.dirname(os.path.abspath(a.quotes)), "perf_out.json")
    json.dump(res, open(path, "w"), indent=1)

    f = lambda x: ("+" if x >= 0 else "−") + f"{abs(x):.2f}%"
    print(f"Dividend Strategy {f(D['day'])} (YTD {f(D['ytd'])}) | DVY {f(disp['DVY']['day'])} "
          f"(YTD {f(disp['DVY']['ytd'])}) | SPY {f(disp['SPY']['day'])} (YTD {f(disp['SPY']['ytd'])})")
    print(f"Growth Portfolio {f(G['day'])} (YTD {f(G['ytd'])}) | IUSG {f(disp['IUSG']['day'])} "
          f"(YTD {f(disp['IUSG']['ytd'])})")
    print("YTD spreads (pts):", res["spreads"], "| 1-day gaps (pts):", res["day_gaps_pts"])
    print("bar widths:", res["bar_widths"], "| holdings up:", res["holdings_up"])
    for s, _ in SLEEVES:
        c = out[s]["contrib"]
        print(f"{s} contributions — top: {c[:3]} bottom: {c[-3:]}")
    print("top movers:", [(m["ticker"], m["pct"]) for m in res["movers_top"][:6]])
    print("bottom movers:", [(m["ticker"], m["pct"]) for m in res["movers_bottom"][:6]])
    if flags:
        print("FLAGS:", *flags, sep="\n  ")
    print("wrote", path)


if __name__ == "__main__":
    main()
