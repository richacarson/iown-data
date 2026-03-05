/**
 * IOWN Market Data Fetcher — GitHub Actions version
 * Finnhub: 51 holdings quotes
 * FMP: Indices, VIX, Gold, Oil, BTC, Sectors
 * Output: latest.txt (same format as "Copy for Commentary")
 */

const fs = require('fs');

const FH_KEY = process.env.FINNHUB_KEY;
const FMP_KEY = process.env.FMP_KEY;

if (!FH_KEY || !FMP_KEY) {
  console.error('Missing API keys. Set FINNHUB_KEY and FMP_KEY as secrets.');
  process.exit(1);
}

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
    { sym: 'CLUSD', name: 'WTI Crude', pre: '$' },
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

  // Sectors
  try {
    const sec = await fetchJSON(`${FMP_BASE}/sector-performance?apikey=${FMP_KEY}`);
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

  // ── Write output ─────────────────────────────────────
  const output = lines.join('\n');
  fs.writeFileSync('latest.txt', output);
  console.log(`Done: ${Object.keys(R).length}/${ALL.length} holdings fetched`);
  console.log(output.substring(0, 500) + '...');
}

main().catch(e => { console.error(e); process.exit(1); });
