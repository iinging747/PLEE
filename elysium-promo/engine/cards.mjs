// Render card news (HTML, one <section class="card"> per card) to PNGs.
//   node engine/cards.mjs [cards/news.html] [out-dir]
// Cards are 1080 x 1350 and saved as <out>/<id>.png.
import { createRequire } from 'node:module';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const page = process.argv[2] || 'cards/news.html';
const out = path.resolve(ROOT, process.argv[3] || 'dist/cards/news');

const TYPES = { '.png': 'image/png', '.jpg': 'image/jpeg', '.html': 'text/html', '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) {
    res.writeHead(404);
    return res.end();
  }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));

const browser = await chromium.launch();
const tab = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
await tab.goto(`http://127.0.0.1:${server.address().port}/${page}`, { waitUntil: 'networkidle' });
await tab.evaluate(async () => {
  await document.fonts.ready;
  // make sure every glyph subset used on the page is loaded
  const txt = document.body.innerText;
  await Promise.all([500, 600, 700, 800, 900].map((w) => document.fonts.load(`${w} 40px "Noto Sans KR"`, txt)));
});
fs.mkdirSync(out, { recursive: true });
for (const el of await tab.$$('section.card')) {
  const id = await el.getAttribute('id');
  await el.screenshot({ path: path.join(out, `${id}.png`) });
  console.log('card', path.relative(ROOT, path.join(out, `${id}.png`)));
}
await browser.close();
server.close();
