// ElevenLabs audio pipeline: narration (TTS), background music and SFX, then
// a ducked mix that the preview render and the AE script both pick up.
//
//   ELEVENLABS_API_KEY=...  node engine/elevenlabs.mjs all
//
// Steps (each can be run alone): voice | music | sfx | mix | all
//   voice  TTS per narration line of both videos -> dist/audio/vo/<video>/<line>.mp3
//          and build/narration_<video>.json (real line lengths). The storyboards
//          re-time their shots to these lengths on the next compile.
//   music  one instrumental track per video, exactly as long as the video
//   sfx    one sound per cue type used by the storyboards (whoosh, impact, ...)
//   mix    ffmpeg: VO + music (ducked under VO) + SFX -> dist/audio/<id>_mix.wav
//
// Optional env: ELEVENLABS_VOICE_ID (otherwise a native Korean expert narrator
// is cast from the Voice Library), per video ELEVENLABS_VOICE_ID_PRO / _EASY,
// ELEVENLABS_MODEL (default eleven_multilingual_v2), ELEVENLABS_SPEED (explainer,
// default 1.05), ELEVENLABS_SPEED_PRO (default 0.98). Needs ffmpeg/ffprobe.
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const API = 'https://api.elevenlabs.io';
const KEY = process.env.ELEVENLABS_API_KEY;
const MODEL = process.env.ELEVENLABS_MODEL || 'eleven_multilingual_v2';
const SPEED = Number(process.env.ELEVENLABS_SPEED || 1.05);
const AUDIO = path.join(ROOT, 'dist', 'audio');
const step = process.argv[2] || 'all';
const force = process.argv.includes('--force');

const MUSIC = {
  pro: 'Premium minimal tech commercial score, 120 BPM, confident and sleek. Deep sub-bass pulses on the beat, crisp tight hi-hats, glassy airy pads, subtle digital textures. Starts sparse with a rising swell for 3 seconds, a clean impact at 7 seconds, steady driving pulse through the middle, and a wide cinematic resolve in the last 6 seconds. Instrumental, no vocals.',
  easy: 'Light, friendly explainer background music, 100 BPM. Soft plucked synths and warm marimba, gentle kick and shaker, bright but calm and unobtrusive so a voiceover sits clearly on top. Curious, optimistic, modern. Steady energy without big drops, soft ending. Instrumental, no vocals.',
};
const SFX = {
  whoosh: { text: 'soft airy whoosh transition, short and clean', d: 0.8 },
  impact: { text: 'deep cinematic sub impact hit, clean tail', d: 1.5 },
  boom: { text: 'big cinematic logo reveal boom with shimmering tail', d: 2.5 },
  hit: { text: 'tight punchy digital click hit, minimal UI accent', d: 0.5 },
  riser: { text: 'smooth rising synth swell building tension', d: 3.0 },
  ticks: { text: 'fast precise digital ticking clock, tiny clicks', d: 1.4 },
};
const SFX_GAIN = { whoosh: 0.35, impact: 0.6, boom: 0.7, hit: 0.35, riser: 0.45, ticks: 0.25 };

function need(cond, msg) {
  if (!cond) {
    console.error('✖ ' + msg);
    process.exit(1);
  }
}
const sh = (cmd, args) => execFileSync(cmd, args, { encoding: 'utf8' }).trim();
const durOf = (f) => Number(sh('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]));
const video = (id) => JSON.parse(fs.readFileSync(path.join(ROOT, 'build', id + '.json'), 'utf8'));
const compile = () => {
  const r = spawnSync('node', [path.join(ROOT, 'engine', 'render.mjs'), '--compile-only'], { stdio: 'inherit' });
  need(r.status === 0, 'compile failed');
};

async function post(url, body, out) {
  for (let attempt = 1; attempt <= 4; attempt++) {
    const r = await fetch(API + url, { method: 'POST', headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json', Accept: 'audio/mpeg' }, body: JSON.stringify(body) });
    if (r.ok) {
      fs.mkdirSync(path.dirname(out), { recursive: true });
      fs.writeFileSync(out, Buffer.from(await r.arrayBuffer()));
      return out;
    }
    const msg = await r.text();
    if ((r.status === 429 || r.status >= 500) && attempt < 4) {
      await new Promise((res) => setTimeout(res, 2000 * 2 ** attempt));
      continue;
    }
    throw new Error(`${url} -> ${r.status}: ${msg.slice(0, 400)}`);
  }
}

// Voice casting: an env voice id wins; otherwise search the shared Voice
// Library for a native Korean narrator matching the brief (trustworthy expert:
// male, middle-aged, informative), add it to the account, and cache the choice
// in build/voice.json so every rerun uses the same voice.
const CASTING = {
  brief: 'trustworthy Korean expert narrator',
  queries: [
    { language: 'ko', gender: 'male', age: 'middle_aged', use_cases: 'informative_educational' },
    { language: 'ko', gender: 'male', use_cases: 'narrative_story' },
    { language: 'ko', gender: 'male' },
    { language: 'ko' },
  ],
  fallback: 'nPczCjzI2devNBz1zQrb', // premade "Brian": deep, resonant
};

async function getJSON(url) {
  const r = await fetch(API + url, { headers: { 'xi-api-key': KEY } });
  if (!r.ok) throw new Error(`${url} -> ${r.status}: ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

async function castVoice() {
  if (process.env.ELEVENLABS_VOICE_ID) return process.env.ELEVENLABS_VOICE_ID;
  const cache = path.join(ROOT, 'build', 'voice.json');
  if (!force && fs.existsSync(cache)) return JSON.parse(fs.readFileSync(cache, 'utf8')).voice_id;
  for (const q of CASTING.queries) {
    try {
      const j = await getJSON(`/v1/shared-voices?${new URLSearchParams({ page_size: '10', sort: 'cloned_by_count', ...q })}`);
      const v = (j.voices || [])[0];
      if (!v) continue;
      const r = await fetch(`${API}/v1/voices/add/${v.public_owner_id}/${v.voice_id}`, { method: 'POST', headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ new_name: `Elysium narrator - ${v.name}` }) });
      const added = r.ok ? await r.json() : {};
      const voiceId = added.voice_id || v.voice_id;
      fs.mkdirSync(path.dirname(cache), { recursive: true });
      fs.writeFileSync(cache, JSON.stringify({ voice_id: voiceId, name: v.name, description: v.description, query: q }, null, 1));
      console.log(`voice: ${v.name} (${voiceId}) — ${CASTING.brief}`);
      return voiceId;
    } catch (e) {
      console.warn(`voice search ${JSON.stringify(q)} failed: ${e.message}`);
    }
  }
  console.warn('No Korean library voice found; using the premade "Brian" voice. Set ELEVENLABS_VOICE_ID to choose one.');
  return CASTING.fallback;
}

// One trusted narrator for both videos; the commercial reads calm and measured,
// the explainer a little warmer and quicker.
const VOICE = {
  pro: { env: 'ELEVENLABS_VOICE_ID_PRO', settings: { stability: 0.62, similarity_boost: 0.82, style: 0.1, use_speaker_boost: true, speed: Number(process.env.ELEVENLABS_SPEED_PRO || 0.97) } },
  easy: { env: 'ELEVENLABS_VOICE_ID_EASY', settings: { stability: 0.5, similarity_boost: 0.8, style: 0.25, use_speaker_boost: true, speed: SPEED } },
};

async function voice() {
  const narrator = await castVoice();
  for (const id of ['pro', 'easy']) {
    const v = video(id);
    const n = v.narration;
    if (!n.length) continue;
    const voiceId = process.env[VOICE[id].env] || narrator;
    const dir = path.join(AUDIO, 'vo', id);
    const lines = {};
    for (let i = 0; i < n.length; i++) {
      const l = n[i];
      const out = path.join(dir, l.id + '.mp3');
      if (force || !fs.existsSync(out)) {
        process.stdout.write(`  tts ${id}/${l.id} ${l.text}\n`);
        await post(`/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`, {
          text: l.say,
          model_id: MODEL,
          previous_text: i > 0 ? n[i - 1].say : undefined,
          next_text: i < n.length - 1 ? n[i + 1].say : undefined,
          voice_settings: VOICE[id].settings,
        }, out);
      }
      lines[l.id] = Math.round(durOf(out) * 100) / 100;
    }
    fs.writeFileSync(path.join(ROOT, 'build', `narration_${id}.json`), JSON.stringify({ voice: voiceId, model: MODEL, lines }, null, 1));
    console.log(`narration ${id}: ${Object.keys(lines).length} lines, ${Object.values(lines).reduce((a, b) => a + b, 0).toFixed(1)}s`);
  }
  console.log('re-timing storyboards to the real narration');
  compile();
}

async function music() {
  for (const id of ['pro', 'easy']) {
    const v = video(id);
    const out = path.join(AUDIO, `music_${id}.mp3`);
    if (!force && fs.existsSync(out) && Math.abs(durOf(out) - v.dur) < 1) continue;
    console.log(`  music ${id} ${v.dur}s`);
    await post('/v1/music?output_format=mp3_44100_128', { prompt: MUSIC[id], music_length_ms: Math.round(v.dur * 1000), model_id: 'music_v1', force_instrumental: true }, out);
  }
}

async function sfx() {
  const types = new Set();
  for (const id of ['pro', 'easy']) for (const c of video(id).cues || []) types.add(c.type);
  for (const t of types) {
    const out = path.join(AUDIO, 'sfx', t + '.mp3');
    if (!force && fs.existsSync(out)) continue;
    console.log('  sfx', t);
    await post('/v1/sound-generation?output_format=mp3_44100_128', { text: SFX[t].text, duration_seconds: SFX[t].d, prompt_influence: 0.45 }, out);
  }
}

function mix() {
  for (const id of ['pro', 'easy']) {
    const v = video(id);
    const musicFile = path.join(AUDIO, `music_${id}.mp3`);
    if (!fs.existsSync(musicFile)) {
      console.warn(`skip mix ${id}: no music`);
      continue;
    }
    const inputs = ['-i', musicFile];
    const parts = [];
    let idx = 1;
    const vo = [];
    {
      for (const l of v.narration) {
        const f = path.join(AUDIO, 'vo', id, l.id + '.mp3');
        if (!fs.existsSync(f)) continue;
        inputs.push('-i', f);
        const ms = Math.round(l.start * 1000);
        parts.push(`[${idx}:a]aresample=48000,adelay=${ms}|${ms},apad[v${idx}]`);
        vo.push(`[v${idx}]`);
        idx++;
      }
    }
    const fx = [];
    for (const c of v.cues || []) {
      const f = path.join(AUDIO, 'sfx', c.type + '.mp3');
      if (!fs.existsSync(f)) continue;
      inputs.push('-i', f);
      const ms = Math.max(0, Math.round((c.type === 'riser' ? c.t : c.t - 0.03) * 1000));
      parts.push(`[${idx}:a]aresample=48000,volume=${SFX_GAIN[c.type] ?? 0.4},adelay=${ms}|${ms},apad[s${idx}]`);
      fx.push(`[s${idx}]`);
      idx++;
    }
    const D = v.dur.toFixed(2);
    parts.push(`[0:a]aresample=48000,volume=${id === 'easy' ? 0.55 : 0.9},afade=t=in:d=0.4,afade=t=out:st=${(v.dur - 1.2).toFixed(2)}:d=1.2,atrim=0:${D}[m]`);
    let musicBus = '[m]';
    const buses = [];
    if (vo.length) {
      parts.push(`${vo.join('')}amix=inputs=${vo.length}:normalize=0,atrim=0:${D}[vo]`);
      parts.push('[vo]asplit=2[vomix][vokey]');
      parts.push('[m][vokey]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=450[mduck]');
      musicBus = '[mduck]';
      buses.push('[vomix]');
    }
    buses.push(musicBus);
    if (fx.length) {
      parts.push(`${fx.join('')}amix=inputs=${fx.length}:normalize=0,atrim=0:${D}[fx]`);
      buses.push('[fx]');
    }
    parts.push(`${buses.join('')}amix=inputs=${buses.length}:normalize=0,atrim=0:${D},loudnorm=I=-14:TP=-1.5:LRA=11[out]`);
    const out = path.join(AUDIO, `${id}_mix.wav`);
    const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...inputs, '-filter_complex', parts.join(';'), '-map', '[out]', '-ar', '48000', '-ac', '2', out], { stdio: 'inherit' });
    need(r.status === 0, 'ffmpeg mix failed for ' + id);
    spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-b:a', '256k', out.replace(/\.wav$/, '.mp3')], { stdio: 'inherit' });
    console.log('  mix', out, '(+ .mp3)');
  }
}

need(KEY || step === 'mix', 'ELEVENLABS_API_KEY is not set (add it as an environment variable; never commit it).');
fs.mkdirSync(AUDIO, { recursive: true });
if (!fs.existsSync(path.join(ROOT, 'build', 'easy.json'))) compile();
if (step === 'voice' || step === 'all') await voice();
if (step === 'music' || step === 'all') await music();
if (step === 'sfx' || step === 'all') await sfx();
if (step === 'mix' || step === 'all') mix();
console.log('done. Next: npm run jsx && npm run render');
