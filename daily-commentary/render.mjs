// Render self-contained commentary HTML -> Letter PDF via headless Chrome.
// Usage: node daily-commentary/render.mjs [commentaries/FILE.html ...]
// With no args: render every self-contained commentaries/*.html that lacks a PDF.
import puppeteer from 'puppeteer';
import fs from 'node:fs';
import path from 'node:path';

const COMM_DIR = 'commentaries';

const isDoc = (p) => {
  try {
    const head = fs.readFileSync(p, 'utf8').slice(0, 500).toLowerCase();
    return head.includes('<!doctype html') || head.includes('<html');
  } catch { return false; }
};

let targets = process.argv.slice(2).filter((f) => f && f.endsWith('.html'));
if (targets.length === 0) {
  targets = fs.readdirSync(COMM_DIR)
    .filter((f) => f.endsWith('.html'))
    .map((f) => path.join(COMM_DIR, f))
    .filter((p) => !fs.existsSync(p.replace(/\.html$/, '.pdf')));
}
// only render true self-contained documents that exist (skip old fragments)
targets = [...new Set(targets)].filter((p) => fs.existsSync(p) && isDoc(p));

if (targets.length === 0) {
  console.log('No self-contained commentary HTML to render.');
  process.exit(0);
}

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

for (const html of targets) {
  const abs = 'file://' + path.resolve(html);
  const out = html.replace(/\.html$/, '.pdf');
  const page = await browser.newPage();
  await page.goto(abs, { waitUntil: 'networkidle0', timeout: 90000 });
  try { await page.evaluate(async () => { if (document.fonts) await document.fonts.ready; }); } catch {}
  await page.pdf({ path: out, printBackground: true, preferCSSPageSize: true });
  await page.close();
  console.log('Rendered', out);
}

await browser.close();
