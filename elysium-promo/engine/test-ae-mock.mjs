// Smoke test for dist/Elysium_Promo_AE.jsx without After Effects: runs the
// script against a strict mock of the AE scripting DOM. The mock knows the
// match names the runtime relies on, checks value dimensions, keyframe ease
// array sizes, and compiles + evaluates every expression the script sets.
//   node engine/test-ae-mock.mjs [--fonts-api]
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const JSX = path.join(ROOT, 'dist', 'Elysium_Promo_AE.jsx');
const withFontsApi = process.argv.includes('--fonts-api');
const errors = [];
const stats = { comps: 0, layers: 0, keys: 0, exprs: 0, effects: 0 };
const fail = (m) => {
  errors.push(m);
  throw new Error(m);
};

const PVT = { NO_VALUE: 0, ThreeD_SPATIAL: 1, ThreeD: 2, TwoD_SPATIAL: 3, TwoD: 4, OneD: 5, COLOR: 6, CUSTOM_VALUE: 7, MARKER: 8, LAYER_INDEX: 9, MASK_INDEX: 10, SHAPE: 11, TEXT_DOCUMENT: 12 };

// schema: matchName -> leaf value type, or group spec {fixed:{...}, add:{...}}
const LEAF = (t) => ({ leaf: t });
const TRANSFORM = { fixed: { 'ADBE Anchor Point': LEAF('ThreeD_SPATIAL'), 'ADBE Position': LEAF('ThreeD_SPATIAL'), 'ADBE Scale': LEAF('ThreeD'), 'ADBE Rotate Z': LEAF('OneD'), 'ADBE Opacity': LEAF('OneD') } };
const EFFECTS = {
  'ADBE Ramp': { fixed: { 'ADBE Ramp-0001': LEAF('TwoD_SPATIAL'), 'ADBE Ramp-0002': LEAF('COLOR'), 'ADBE Ramp-0003': LEAF('TwoD_SPATIAL'), 'ADBE Ramp-0004': LEAF('COLOR'), 'ADBE Ramp-0005': LEAF('OneD'), 'ADBE Ramp-0006': LEAF('OneD'), 'ADBE Ramp-0007': LEAF('OneD') } },
  'ADBE Tint': { fixed: { 'ADBE Tint-0001': LEAF('COLOR'), 'ADBE Tint-0002': LEAF('COLOR'), 'ADBE Tint-0003': LEAF('OneD') } },
  'ADBE Gaussian Blur 2': { fixed: { 'ADBE Gaussian Blur 2-0001': LEAF('OneD'), 'ADBE Gaussian Blur 2-0002': LEAF('OneD'), 'ADBE Gaussian Blur 2-0003': LEAF('OneD') } },
  'ADBE Noise': { fixed: { 'ADBE Noise-0001': LEAF('OneD'), 'ADBE Noise-0002': LEAF('OneD'), 'ADBE Noise-0003': LEAF('OneD') } },
};
const VEC_TRANSFORM = { fixed: { 'ADBE Vector Anchor': LEAF('TwoD_SPATIAL'), 'ADBE Vector Position': LEAF('TwoD_SPATIAL'), 'ADBE Vector Scale': LEAF('TwoD'), 'ADBE Vector Rotation': LEAF('OneD'), 'ADBE Vector Group Opacity': LEAF('OneD') } };
const VEC_ITEMS = {
  'ADBE Vector Shape - Rect': { fixed: { 'ADBE Vector Rect Size': LEAF('TwoD'), 'ADBE Vector Rect Position': LEAF('TwoD_SPATIAL'), 'ADBE Vector Rect Roundness': LEAF('OneD') } },
  'ADBE Vector Shape - Ellipse': { fixed: { 'ADBE Vector Ellipse Size': LEAF('TwoD'), 'ADBE Vector Ellipse Position': LEAF('TwoD_SPATIAL') } },
  'ADBE Vector Shape - Group': { fixed: { 'ADBE Vector Shape': LEAF('SHAPE') } },
  'ADBE Vector Filter - Trim': { fixed: { 'ADBE Vector Trim Start': LEAF('OneD'), 'ADBE Vector Trim End': LEAF('OneD'), 'ADBE Vector Trim Offset': LEAF('OneD') } },
  'ADBE Vector Graphic - Stroke': { fixed: { 'ADBE Vector Stroke Color': LEAF('COLOR'), 'ADBE Vector Stroke Opacity': LEAF('OneD'), 'ADBE Vector Stroke Width': LEAF('OneD'), 'ADBE Vector Stroke Line Cap': LEAF('OneD'), 'ADBE Vector Stroke Line Join': LEAF('OneD') } },
  'ADBE Vector Graphic - Fill': { fixed: { 'ADBE Vector Fill Color': LEAF('COLOR'), 'ADBE Vector Fill Opacity': LEAF('OneD') } },
};
VEC_ITEMS['ADBE Vector Group'] = { fixed: { 'ADBE Vectors Group': { add: VEC_ITEMS }, 'ADBE Vector Transform Group': VEC_TRANSFORM } };
const TEXT_ANIMATOR = {
  fixed: {
    'ADBE Text Animator Properties': { add: { 'ADBE Text Opacity': LEAF('OneD'), 'ADBE Text Tracking Amount': LEAF('OneD') } },
    'ADBE Text Selectors': { add: { 'ADBE Text Selector': { fixed: { 'ADBE Text Percent Start': LEAF('OneD'), 'ADBE Text Percent End': LEAF('OneD'), 'ADBE Text Percent Offset': LEAF('OneD') } } } },
  },
};

class Prop {
  constructor(matchName, type, layer) {
    this.matchName = matchName;
    this.name = matchName;
    this.propertyValueType = PVT[type];
    this._type = type;
    this._layer = layer;
    this.keys = [];
    this.value = type === 'TEXT_DOCUMENT' ? new TextDocument('') : undefined;
    this._expr = '';
  }
  _dims() {
    return { ThreeD_SPATIAL: 3, ThreeD: 3, TwoD_SPATIAL: 2, TwoD: 2, OneD: 1, COLOR: 4 }[this._type];
  }
  _check(v) {
    const t = this._type;
    if (t === 'TEXT_DOCUMENT') {
      if (!(v instanceof TextDocument)) fail(`${this.matchName}: expected TextDocument`);
      return;
    }
    if (t === 'SHAPE') {
      if (!(v instanceof Shape) || !Array.isArray(v.vertices) || v.vertices.length < 2) fail(`${this.matchName}: bad Shape`);
      for (const k of ['inTangents', 'outTangents']) if (v[k] && v[k].length !== v.vertices.length) fail(`${this.matchName}: ${k} length mismatch`);
      return;
    }
    const d = this._dims();
    if (d === 1) {
      if (typeof v !== 'number' || !isFinite(v)) fail(`${this.matchName}: expected number, got ${JSON.stringify(v)}`);
      return;
    }
    if (!Array.isArray(v) || v.some((x) => typeof x !== 'number' || !isFinite(x))) fail(`${this.matchName}: expected numeric array, got ${JSON.stringify(v)}`);
    if (t === 'COLOR' && v.length !== 4) fail(`${this.matchName}: color needs 4 values`);
    if ((t === 'TwoD' || t === 'TwoD_SPATIAL') && v.length !== 2) fail(`${this.matchName}: needs 2 values, got ${v.length}`);
    if ((t === 'ThreeD' || t === 'ThreeD_SPATIAL') && v.length !== 2 && v.length !== 3) fail(`${this.matchName}: needs 2-3 values`);
  }
  setValue(v) {
    this._check(v);
    if (this.keys.length) fail(`${this.matchName}: setValue on keyframed property`);
    this.value = v;
  }
  setValuesAtTimes(ts, vs) {
    if (ts.length !== vs.length) fail('setValuesAtTimes length mismatch');
    ts.forEach((t, i) => {
      if (typeof t !== 'number' || !isFinite(t)) fail(`${this.matchName}: bad key time ${t}`);
      this._check(vs[i]);
      this.keys.push({ t, v: vs[i] });
      stats.keys++;
    });
    this.keys.sort((a, b) => a.t - b.t);
    for (let i = 1; i < this.keys.length; i++) if (this.keys[i].t === this.keys[i - 1].t) fail(`${this.matchName}: duplicate key time ${this.keys[i].t} on ${this._layer && this._layer.name}`);
  }
  get numKeys() {
    return this.keys.length;
  }
  nearestKeyIndex(t) {
    let best = 1;
    let bd = Infinity;
    this.keys.forEach((k, i) => {
      const d = Math.abs(k.t - t);
      if (d < bd) {
        bd = d;
        best = i + 1;
      }
    });
    return best;
  }
  _key(k) {
    if (k < 1 || k > this.keys.length) fail(`${this.matchName}: key index ${k} out of range`);
    return this.keys[k - 1];
  }
  setInterpolationTypeAtKey(k, a, b) {
    this._key(k);
    if (![6612, 6613, 6614].includes(a) || (b !== undefined && ![6612, 6613, 6614].includes(b))) fail('bad interpolation type');
  }
  setTemporalEaseAtKey(k, a, b) {
    this._key(k);
    const spatial = this._type.endsWith('SPATIAL');
    const need = spatial ? 1 : this._dims() === 4 ? 1 : this._dims();
    if (a.length !== need || b.length !== need) throw new Error('ease array length');
    for (const e of [...a, ...b]) if (!(e instanceof KeyframeEase) || e.influence < 0.1 || e.influence > 100) fail('bad KeyframeEase');
  }
  setSpatialAutoBezierAtKey(k) {
    this._key(k);
  }
  setSpatialContinuousAtKey(k) {
    this._key(k);
  }
  setSpatialTangentsAtKey(k, a, b) {
    this._key(k);
    const d = this._dims();
    if (a.length !== d || b.length !== d) throw new Error('tangent dims');
  }
  get expression() {
    return this._expr;
  }
  set expression(s) {
    stats.exprs++;
    this._expr = s;
    let r;
    try {
      r = new vm.Script(`(function(time){ return eval(${JSON.stringify(s)}); })`).runInNewContext({ Math })(1.234);
    } catch (e) {
      fail(`${this.matchName}: expression error ${e.message}: ${s}`);
    }
    if (this._type === 'TEXT_DOCUMENT') {
      if (typeof r !== 'string') fail(`${this.matchName}: text expression must return string`);
    } else {
      const d = this._dims();
      if (d === 1 && typeof r !== 'number') fail(`${this.matchName}: expression must return number: ${s}`);
      if (d > 1 && (!Array.isArray(r) || r.length < 2 || r.some((x) => !isFinite(x)))) fail(`${this.matchName}: expression must return array: ${s}`);
    }
  }
}

class Group {
  constructor(matchName, spec, layer) {
    this.matchName = matchName;
    this.name = matchName;
    this._spec = spec;
    this._layer = layer;
    this._kids = [];
    for (const [mn, sp] of Object.entries(spec.fixed || {})) this._kids.push(make(mn, sp, layer));
  }
  get numProperties() {
    return this._kids.length;
  }
  property(key) {
    if (typeof key === 'number') {
      if (key < 1 || key > this._kids.length) fail(`${this.matchName}: index ${key} out of range`);
      return this._kids[key - 1];
    }
    const k = this._kids.find((c) => c.matchName === key);
    if (!k) fail(`${this.matchName}: no child "${key}"`);
    return k;
  }
  addProperty(mn) {
    const sp = (this._spec.add || {})[mn];
    if (!sp) fail(`${this.matchName}: cannot add "${mn}"`);
    if (this.matchName === 'ADBE Effect Parade') stats.effects++;
    const p = make(mn, sp, this._layer);
    this._kids.push(p);
    return p;
  }
}
const make = (mn, sp, layer) => (sp.leaf ? new Prop(mn, sp.leaf, layer) : new Group(mn, sp, layer));

class TextDocument {
  constructor(t) {
    this.text = t;
  }
  resetCharStyle() {}
  resetParagraphStyle() {}
}
class Shape {}
class KeyframeEase {
  constructor(speed, influence) {
    this.speed = speed;
    this.influence = influence;
  }
}
class MarkerValue {
  constructor(c) {
    this.comment = c;
  }
}
class ImportOptions {
  constructor(f) {
    this.file = f;
  }
}
class FolderItem {
  constructor(name) {
    this.name = name;
    this.parentFolder = null;
  }
}

class Layer {
  constructor(comp, kind, extra = {}) {
    this.containingComp = comp;
    this.kind = kind;
    this.name = kind;
    this.startTime = 0;
    this.inPoint = 0;
    this.outPoint = comp.duration;
    this.enabled = true;
    this.trackMatteType = 0;
    Object.assign(this, extra);
    const groups = { 'ADBE Transform Group': TRANSFORM, 'ADBE Effect Parade': { add: EFFECTS }, 'ADBE Mask Parade': { add: {} } };
    if (kind === 'text') groups['ADBE Text Properties'] = { fixed: { 'ADBE Text Document': LEAF('TEXT_DOCUMENT'), 'ADBE Text Animators': { add: { 'ADBE Text Animator': TEXT_ANIMATOR } } } };
    if (kind === 'shape') groups['ADBE Root Vectors Group'] = { add: { 'ADBE Vector Group': VEC_ITEMS['ADBE Vector Group'] } };
    this._root = new Group('root', { fixed: groups }, this);
    stats.layers++;
  }
  property(k) {
    return this._root.property(k);
  }
  moveToEnd() {
    const L = this.containingComp.layers._list;
    L.splice(L.indexOf(this), 1);
    L.push(this);
  }
  set parent(p) {
    if (p !== null && (!(p instanceof Layer) || p.containingComp !== this.containingComp)) fail('parent must be a layer in the same comp');
    this._parent = p;
  }
  get parent() {
    return this._parent || null;
  }
  setTrackMatte(m) {
    if (!(m instanceof Layer)) fail('setTrackMatte needs a layer');
    this._matte = m;
  }
  openInViewer() {}
}

class Comp {
  static seq = 0;
  constructor(name, w, h, par, dur, fps) {
    if (!(dur > 0) || !(fps > 0) || !(w > 0)) fail(`bad comp params ${name}`);
    Object.assign(this, { name, width: w, height: h, duration: dur, frameRate: fps, parentFolder: null, id: ++Comp.seq });
    const comp = this;
    this.layers = {
      _list: [],
      _push(l) {
        this._list.unshift(l);
        return l;
      },
      addText: (s) => {
        const l = comp.layers._push(new Layer(comp, 'text'));
        l.property('ADBE Text Properties').property('ADBE Text Document').value = new TextDocument(s);
        return l;
      },
      addShape: () => comp.layers._push(new Layer(comp, 'shape')),
      addNull: (d) => {
        if (!(d > 0)) fail('bad addNull duration');
        return comp.layers._push(new Layer(comp, 'null'));
      },
      addSolid: (c, n, w2, h2, p, d) => {
        if (c.length !== 3 || !(w2 >= 1) || !(h2 >= 1) || !(d > 0)) fail('bad addSolid args');
        return comp.layers._push(new Layer(comp, 'solid', { name: n }));
      },
      add: (item) => {
        if (!(item instanceof Comp) && !(item && item._footage)) fail(`layers.add got ${item}`);
        return comp.layers._push(new Layer(comp, 'av', { source: item }));
      },
    };
    this.markerProperty = { setValueAtTime() {} };
    stats.comps++;
  }
  openInViewer() {}
}

const items = { length: 0 };
const pushItem = (it) => {
  items.length++;
  items[items.length] = it;
  return it;
};
items.addComp = (...a) => pushItem(new Comp(...a));
items.addFolder = (n) => pushItem(new FolderItem(n));

function FileFn(p) {
  return { fsName: p, exists: fs.existsSync(p), parent: { fsName: path.dirname(p) } };
}
const fontFamilies = [
  ['Pretendard', ['Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold'], 'Pretendard'],
  ['Noto Sans KR', ['Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold', 'Black'], 'NotoSansKR'],
  ['Sandoll GothicNeo3', ['04 Rg', '05 Md', '06 Sb', '07 Bd', '08 Eb'], 'SDGothicNeo3'],
  ['Sandoll Greta Sans', ['Regular', 'Medium', 'SemiBold', 'Bold', 'ExtraBold'], 'SandollGretaSans'],
  ['DM Sans', ['Regular', 'Medium', 'SemiBold', 'Bold'], 'DMSans'],
  ['DM Mono', ['Regular', 'Medium'], 'DMMono'],
].map(([f, styles, ps]) => styles.map((s) => ({ familyName: f, styleName: s, postScriptName: `${ps}-${s.replace(/\s/g, '')}`, isSubstitute: false })));

const sandbox = {
  app: {
    version: '24.0',
    project: { items, importFile: (o) => { if (!o.file.exists) fail('importFile: missing ' + o.file.fsName); return pushItem({ _footage: true, name: path.basename(o.file.fsName), parentFolder: null, width: 512, height: 512 }); } },
    newProject() {},
    beginUndoGroup() {},
    endUndoGroup() {},
    fonts: withFontsApi ? { allFonts: fontFamilies, getFontsByPostScriptName: (ps) => fontFamilies.flat().filter((f) => f.postScriptName === ps) } : undefined,
  },
  $: { fileName: JSX, os: 'Windows/64 10.0', writeln: () => {} },
  File: FileFn,
  Folder: { desktop: { fsName: '/tmp' } },
  alert: (m) => {
    sandbox.__alert = m;
  },
  KeyframeEase,
  KeyframeInterpolationType: { LINEAR: 6612, BEZIER: 6613, HOLD: 6614 },
  PropertyValueType: PVT,
  ParagraphJustification: { LEFT_JUSTIFY: 1, CENTER_JUSTIFY: 2, RIGHT_JUSTIFY: 3 },
  BlendingMode: { SCREEN: 1, ADD: 2, MULTIPLY: 3, OVERLAY: 4 },
  TrackMatteType: { ALPHA: 1 },
  Shape,
  TextDocument,
  MarkerValue,
  ImportOptions,
  FolderItem,
};

let src = fs.readFileSync(JSX, 'utf8').replace(/^﻿/, '');
if (/[^\x00-\x7f]/.test(src.slice(src.indexOf('(function () {')))) errors.push('non-ASCII characters in code section');
try {
  vm.runInNewContext(src, sandbox, { filename: 'Elysium_Promo_AE.jsx' });
} catch (e) {
  errors.push('script threw: ' + e.stack.split('\n').slice(0, 3).join(' | '));
}
const msg = sandbox.__alert || '(no alert)';
console.log(`fonts api: ${withFontsApi}`);
console.log(`comps ${stats.comps}, layers ${stats.layers}, keys ${stats.keys}, expressions ${stats.exprs}, effects ${stats.effects}`);
console.log('--- alert ---\n' + msg.replace(/\r/g, '\n'));
const warnCount = (msg.match(/경고 (\d+)/) || [])[1];
if (errors.length) {
  console.log('--- mock errors ---');
  [...new Set(errors)].slice(0, 30).forEach((e) => console.log(' ', e));
  process.exit(1);
}
if (warnCount) process.exit(1);
console.log('OK');
