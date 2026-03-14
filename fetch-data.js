/**
 * IOWN Market Data Fetcher — GitHub Actions version (v2)
 * Finnhub: 51 holdings quotes + company news + market news
 * FMP: Indices, VIX, Gold, Oil, BTC, Sectors + Economic Calendar
 * Output: latest.txt (same format as "Copy for Commentary")
 * Safeguards: market-hours block, AAPL canary check, fetch timestamp
 */

const fs = require('fs');

const FH_KEY = process.env.FINNHUB_KEY;
const FMP_KEY = process.env.FMP_KEY;

if (!FH_KEY || !FMP_KEY) {
  console.error('Missing API keys. Set FINNHUB_KEY and FMP_KEY as secrets.');
  process.exit(1);
}

// Manual trigger — no market-hours guard
// Canary check (AAPL date) below ensures data freshness
const now = new Date();
console.log(`Fetching at UTC ${now.getUTCHours()}:${String(now.getUTCMinutes()).padStart(2,'0')}`);

const DIV = ['ABT','A','ADI','ATO','ADP','BKH','CAT','CHD','CL','FAST','GD','GPC','LRCX','LMT','MATX','NEE','ORI','PCAR','QCOM','DGX','SSNC','STLD','SYK','TEL','VLO'];
const GRW = ['AMD','AEM','ATAT','CVX','CWAN','CNX','COIN','EIX','FINV','FTNT','GFI','SUPV','HRMY','HUT','KEYS','MARA','NVDA','NXPI','OKE','PDD','HOOD','SYF','TSM','TOL'];
const DIG = ['IBIT','ETHA'];
const ALL = [...DIV, ...GRW, ...DIG];

const FMP_BASE = 'https://financialmodelingprep.com/stable';
const FH_BASE = 'https://finnhub.io/api/v1';

function fmt(n, dec = 2) { return n != null ? n.toFixed(dec) : 'N/A'; }
function sign(n) { return n >= 0 ? '+' : ''; }
function fmtV(n) {
  if (!n) return '—';
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
  return n.toString();
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url.split('?')[0]}`);
  return res.json();
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function main() {
  const lines = [];
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
    timeZone: 'America/Chicago'
  });
  lines.push(`IOWN MARKET DATA — ${dateStr}`, '');

  // ── FMP: Macro data ──────────────────────────────────
  lines.push('## BROAD MARKET');

  const macroSyms = [
    { sym: '%5EGSPC', name: 'S&P 500' },
    { sym: '%5EDJI', name: 'Dow' },
    { sym: '%5EIXIC', name: 'Nasdaq' },
    { sym: '%5ERUT', name: 'Russell 2000' },
    { sym: '%5EVIX', name: 'VIX' },
    { sym: 'GCUSD', name: 'Gold', pre: '$' },
    { sym: 'BTCUSD', name: 'Bitcoin', pre: '$' },
  ];

  for (const m of macroSyms) {
    try {
      const data = await fetchJSON(`${FMP_BASE}/quote?symbol=${m.sym}&apikey=${FMP_KEY}`);
      const q = Array.isArray(data) ? data[0] : data;
      if (q && q.price) {
        const pct = q.changesPercentage || q.changePercentage || 0;
        const pre = m.pre || '';
        let val;
        if (m.name === 'Bitcoin') val = '$' + Math.round(q.price).toLocaleString();
        else if (m.name === 'VIX') val = fmt(q.price, 2);
        else if (m.pre) val = pre + q.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        else val = q.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        lines.push(`${m.name}: ${val} | ${sign(pct)}${fmt(pct, 2)}%`);
      }
    } catch (e) {
      console.error(`FMP ${m.name}: ${e.message}`);
    }
  }

  // Sectors — try stable API first, fall back to v3
  try {
    let sec;
    try {
      sec = await fetchJSON(`${FMP_BASE}/sector-performance?apikey=${FMP_KEY}`);
    } catch (e) {
      // Fallback to v3 API
      sec = await fetchJSON(`https://financialmodelingprep.com/api/v3/sector-performance?apikey=${FMP_KEY}`);
    }
    if (Array.isArray(sec) && sec.length) {
      lines.push('', '## SECTOR PERFORMANCE');
      const sorted = sec.sort((a, b) => {
        const av = parseFloat(a.changesPercentage || a.changePercentage || a.change) || 0;
        const bv = parseFloat(b.changesPercentage || b.changePercentage || b.change) || 0;
        return bv - av;
      });
      for (const s of sorted) {
        const pct = parseFloat(s.changesPercentage || s.changePercentage || s.change) || 0;
        const name = (s.sector || s.name || '').replace(/_/g, ' ');
        lines.push(`${name}: ${sign(pct)}${fmt(pct, 2)}%`);
      }
    }
  } catch (e) {
    console.error(`FMP sectors: ${e.message}`);
  }

  lines.push('');

  // ── Finnhub: Holdings ────────────────────────────────
  // Canary check: verify Finnhub is returning the current trading day's data
  const canary = await fetchJSON(`${FH_BASE}/quote?symbol=AAPL&token=${FH_KEY}`);
  const canaryTime = new Date(canary.t * 1000);
  const canaryDateET = canaryTime.toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
  const todayET = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
  const dayOfWeekET = new Date(new Date().toLocaleString('en-US', { timeZone: 'America/New_York' })).getDay();
  // On weekdays, canary should match today's ET date
  // On weekends (Sat=6, Sun=0), Friday data is fine
  if (canaryDateET !== todayET && dayOfWeekET >= 1 && dayOfWeekET <= 5) {
    console.error(`STALE DATA: Finnhub returning ${canaryDateET} but trading day is ${todayET}. Aborting.`);
    process.exit(1);
  }
  console.log(`Finnhub canary: AAPL=$${canary.c}, data date=${canaryDateET}, trading day=${todayET} ✓`);

  const R = {};

  for (let i = 0; i < ALL.length; i++) {
    const t = ALL[i];
    try {
      const d = await fetchJSON(`${FH_BASE}/quote?symbol=${t}&token=${FH_KEY}`);
      if (d.c && d.c > 0) {
        R[t] = { c: d.c, d: d.d, dp: d.dp, h: d.h, l: d.l, o: d.o, pc: d.pc };
      }
    } catch (e) {
      console.error(`Finnhub ${t}: ${e.message}`);
    }
    // Rate limit: 60/sec on Finnhub, be safe with 70ms delay
    if (i < ALL.length - 1) await sleep(70);
  }

  const groups = [
    ['DIVIDEND STRATEGY', DIV],
    ['GROWTH PORTFOLIO', GRW],
    ['DIGITAL ASSET ETFs', DIG],
  ];

  for (const [name, tickers] of groups) {
    lines.push(`## ${name}`);
    lines.push('TICKER | CLOSE | CHG | % CHG | HIGH | LOW');
    lines.push('-------|-------|-----|-------|------|----');
    for (const t of tickers) {
      const r = R[t];
      if (r && r.c > 0) {
        lines.push(`${t} | $${fmt(r.c)} | ${sign(r.d)}${fmt(r.d)} | ${sign(r.dp)}${fmt(r.dp)}% | $${fmt(r.h)} | $${fmt(r.l)}`);
      } else {
        lines.push(`${t} | N/A | N/A | N/A | N/A | N/A`);
      }
    }
    lines.push('');
  }

  // ── FMP: Economic Calendar (today's releases) ──────
  try {
    const todayISO = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const econ = await fetchJSON(`${FMP_BASE}/economic-calendar?from=${todayISO}&to=${todayISO}&apikey=${FMP_KEY}`);
    if (Array.isArray(econ) && econ.length) {
      lines.push('## ECONOMIC CALENDAR (TODAY)');
      // Filter to US events, sort by impact
      const usEvents = econ.filter(e => (e.country || '').toUpperCase() === 'US');
      const events = usEvents.length ? usEvents : econ.slice(0, 15);
      for (const ev of events.slice(0, 15)) {
        const name = ev.event || ev.name || 'Unknown';
        const actual = ev.actual != null ? ev.actual : '—';
        const estimate = ev.estimate != null ? ev.estimate : '—';
        const previous = ev.previous != null ? ev.previous : '—';
        const impact = ev.impact || '';
        lines.push(`${name} | Actual: ${actual} | Est: ${estimate} | Prev: ${previous} | ${impact}`);
      }
      lines.push('');
    }
  } catch (e) {
    console.error(`FMP economic calendar: ${e.message}`);
  }

  // ── Finnhub: Market News (top general headlines) ───
  try {
    const mktNews = await fetchJSON(`${FH_BASE}/news?category=general&token=${FH_KEY}`);
    if (Array.isArray(mktNews) && mktNews.length) {
      lines.push('## MARKET NEWS');
      const today = new Date();
      const oneDayAgo = today.getTime() / 1000 - 86400;
      const recent = mktNews.filter(n => n.datetime > oneDayAgo).slice(0, 10);
      for (const n of recent) {
        const time = new Date(n.datetime * 1000).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZone: 'America/Chicago' });
        const src = n.source || '';
        const headline = (n.headline || '').substring(0, 120);
        lines.push(`[${time}] ${src}: ${headline}`);
      }
      lines.push('');
    }
  } catch (e) {
    console.error(`Finnhub market news: ${e.message}`);
  }

  // ── Finnhub: Holdings News (company-specific) ─────
  try {
    const todayISO = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
    const holdingsNews = [];
    // Fetch news for each holding (rate-limited)
    for (let i = 0; i < ALL.length; i++) {
      try {
        const news = await fetchJSON(`${FH_BASE}/company-news?symbol=${ALL[i]}&from=${todayISO}&to=${todayISO}&token=${FH_KEY}`);
        if (Array.isArray(news)) {
          for (const n of news.slice(0, 2)) {
            holdingsNews.push({
              ticker: ALL[i],
              headline: (n.headline || '').substring(0, 120),
              source: n.source || '',
              category: n.category || '',
              datetime: n.datetime || 0
            });
          }
        }
      } catch (e) {
        // Skip individual ticker errors
      }
      if (i < ALL.length - 1) await sleep(70);
    }
    if (holdingsNews.length) {
      // Sort by time, most recent first, deduplicate by headline
      const seen = new Set();
      const unique = holdingsNews
        .sort((a, b) => b.datetime - a.datetime)
        .filter(n => {
          const key = n.headline.substring(0, 60);
          if (seen.has(key)) return false;
          seen.add(key);
          return true;
        });
      lines.push('## HOLDINGS NEWS');
      for (const n of unique.slice(0, 20)) {
        lines.push(`${n.ticker}: ${n.source} — ${n.headline}`);
      }
      lines.push('');
    }
  } catch (e) {
    console.error(`Finnhub holdings news: ${e.message}`);
  }

  // ── Write output ─────────────────────────────────────
  const fetchTime = new Date().toLocaleString('en-US', { timeZone: 'America/Chicago' });
  lines.push(`## FETCH INFO`);
  lines.push(`Fetched: ${fetchTime} CT`);
  lines.push(`Holdings: ${Object.keys(R).length}/${ALL.length}`);
  lines.push(`Canary: AAPL $${canary.c} (${canaryDateET})`);

  const output = lines.join('\n');
  fs.writeFileSync('latest.txt', output);
  console.log(`Done: ${Object.keys(R).length}/${ALL.length} holdings fetched`);
  console.log(output.substring(0, 500) + '...');
}

main().catch(e => { console.error(e); process.exit(1); });
