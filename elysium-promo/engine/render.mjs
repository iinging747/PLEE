// Compile storyboards in headless Chromium (real font metrics) and render
// preview MP4s with ffmpeg.
//   node engine/render.mjs                 compile + render both videos
//   node engine/render.mjs --compile-only  only write build/<id>.json
//   node engine/render.mjs --only pro --stills 1,5.5,12   PNG stills for QA
//   node engine/render.mjs --only easy --from 10 --to 20 --scale 0.5
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const require = createRequire(import.meta.url);
const { chromium } = require('playwright');
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const opt = (k, d) => {
  const i = args.indexOf('--' + k);
  return i < 0 ? d : args[i + 1] && !args[i + 1].startsWith('--') ? args[i + 1] : true;
};
const ids = opt('only') ? [opt('only')] : ['pro', 'easy'];
const OUT = { pro: 'Elysium_Advanced', easy: 'Elysium_Beginner' };

const TYPES = { '.png': 'image/png', '.webp': 'image/webp', '.jpg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.woff2': 'font/woff2', '.woff': 'font/woff' };
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
const port = server.address().port;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1000, height: 600 } });
page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && !/Failed to load resource/.test(m.text()) && console.log('[page]', m.text()));
page.on('pageerror', (e) => console.log('[pageerror]', e.message));
await page.goto(`http://127.0.0.1:${port}/engine/page.html`);
await page.waitForFunction(() => window.ready === true);

fs.mkdirSync(path.join(ROOT, 'build'), { recursive: true });
for (const id of ids) {
  const video = await page.evaluate((n) => window.compile(n), id);
  fs.writeFileSync(path.join(ROOT, 'build', id + '.json'), JSON.stringify(video));
  console.log(`[${id}] compiled: ${video.dur}s, ${Object.keys(video.scenes).length} scenes`);
  for (const w of video.warnings || []) console.log('  WARN', w);
  if (opt('compile-only')) continue;

  const { dur, fps } = await page.evaluate((n) => window.setup(n), id);
  if (opt('stills')) {
    const dir = path.join(ROOT, 'build', 'stills');
    fs.mkdirSync(dir, { recursive: true });
    for (const s of String(opt('stills')).split(',')) {
      const url = await page.evaluate((t) => window.frame(t), Number(s));
      const f = path.join(dir, `${id}_${s}.png`);
      fs.writeFileSync(f, Buffer.from(url.split(',')[1], 'base64'));
      console.log('  still', f);
    }
    continue;
  }
  const from = Number(opt('from', 0));
  const to = Math.min(Number(opt('to', dur)), dur);
  const scale = Number(opt('scale', 1));
  // ElevenLabs mix when it exists, otherwise the synthesised temp track
  const audio = [`${id}_mix.wav`, `${id}_mix.mp3`, `temp_music_${id}.mp3`, `temp_music_${id}.wav`].map((f) => path.join(ROOT, 'dist', 'audio', f)).find((f) => fs.existsSync(f)) || '';
  const outDir = path.join(ROOT, 'dist', 'preview');
  fs.mkdirSync(outDir, { recursive: true });
  const out = opt('out') || path.join(outDir, `${OUT[id]}${from || to < dur ? `_${from}-${to}` : ''}.mp4`);
  const ff = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-'];
  const withAudio = fs.existsSync(audio) && !opt('mute');
  if (withAudio) ff.push('-ss', String(from), '-t', String(to - from), '-i', audio);
  if (scale !== 1) ff.push('-vf', `scale=${Math.round(1920 * scale)}:-2`);
  ff.push('-c:v', 'libx264', '-preset', 'slow', '-crf', String(opt('crf', 17)), '-pix_fmt', 'yuv420p', '-tune', 'animation');
  if (withAudio) ff.push('-c:a', 'aac', '-b:a', '192k', '-shortest');
  ff.push('-movflags', '+faststart', out);
  const proc = spawn('ffmpeg', ff, { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((r) => proc.on('close', r));
  const n = Math.round((to - from) * fps);
  const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    const url = await page.evaluate((t) => window.frame(t), from + i / fps);
    const ok = proc.stdin.write(Buffer.from(url.split(',')[1], 'base64'));
    if (!ok) await new Promise((r) => proc.stdin.once('drain', r));
    if (i % 150 === 0) console.log(`  [${id}] frame ${i}/${n}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  proc.stdin.end();
  await done;
  console.log(`[${id}] wrote ${out}`);
}
await browser.close();
server.close();
