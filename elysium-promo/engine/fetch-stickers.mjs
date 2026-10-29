// Download a Telegram sticker pack into assets/stickers/ via the Bot API.
//
//   TELEGRAM_BOT_TOKEN=123:abc node engine/fetch-stickers.mjs HariShimSing
//
// A bot token is free from @BotFather. Static stickers (WebP) are converted to
// PNG; video stickers (WebM) get a first-frame PNG for the preview and a
// ProRes 4444 .mov with alpha for After Effects; animated TGS (Lottie) files
// are saved as-is (import them in AE with a Lottie plug-in). A manifest.json
// lists every sticker with its emoji so scenes can pick poses by index.
// Needs ffmpeg on PATH.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const SET = process.argv[2] || 'HariShimSing';
const OUT = path.join(ROOT, 'assets', 'stickers');

if (!TOKEN) {
  console.error('✖ TELEGRAM_BOT_TOKEN is not set (create a bot with @BotFather; never commit the token).');
  process.exit(1);
}
const api = async (method, params) => {
  const r = await fetch(`https://api.telegram.org/bot${TOKEN}/${method}?${new URLSearchParams(params)}`);
  const j = await r.json();
  if (!j.ok) throw new Error(`${method}: ${j.description}`);
  return j.result;
};
const ff = (args) => spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...args], { stdio: 'inherit' }).status === 0;

const set = await api('getStickerSet', { name: SET });
console.log(`${set.title} — ${set.stickers.length} stickers`);
fs.mkdirSync(path.join(OUT, 'raw'), { recursive: true });
const manifest = { set: SET, title: set.title, stickers: [] };
for (const [i, s] of set.stickers.entries()) {
  const f = await api('getFile', { file_id: s.file_id });
  const ext = path.extname(f.file_path) || (s.is_video ? '.webm' : s.is_animated ? '.tgs' : '.webp');
  const base = String(i + 1).padStart(2, '0');
  const raw = path.join(OUT, 'raw', base + ext);
  const r = await fetch(`https://api.telegram.org/file/bot${TOKEN}/${f.file_path}`);
  fs.writeFileSync(raw, Buffer.from(await r.arrayBuffer()));
  const entry = { index: i + 1, emoji: s.emoji || '', type: s.is_video ? 'video' : s.is_animated ? 'lottie' : 'static', raw: path.relative(OUT, raw) };
  if (entry.type === 'static') {
    if (ff(['-i', raw, path.join(OUT, base + '.png')])) entry.png = base + '.png';
  } else if (entry.type === 'video') {
    // libvpx-vp9 decoder keeps the alpha channel
    if (ff(['-c:v', 'libvpx-vp9', '-i', raw, '-frames:v', '1', path.join(OUT, base + '.png')])) entry.png = base + '.png';
    if (ff(['-c:v', 'libvpx-vp9', '-i', raw, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', path.join(OUT, base + '.mov')])) entry.mov = base + '.mov';
  }
  manifest.stickers.push(entry);
  console.log(`  ${base} ${entry.emoji} ${entry.type}${entry.png ? ' → ' + entry.png : ''}`);
}
fs.writeFileSync(path.join(OUT, 'manifest.json'), JSON.stringify(manifest, null, 1));
console.log(`saved to ${path.relative(process.cwd(), OUT)} (manifest.json)`);
