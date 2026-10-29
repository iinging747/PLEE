// ---------------------------------------------------------------------------
// Runtime (ExtendScript / ES3). Builds compositions from DATA, which is the
// same compiled document the preview renderer plays.
// ---------------------------------------------------------------------------

var KIT = KeyframeInterpolationType;
var REPORT = { missingFonts: {}, warnings: [], krFamily: '' };

function log(s) { try { $.writeln('[Elysium] ' + s); } catch (e) {} }
function warn(s) { REPORT.warnings.push(s); log('WARN ' + s); }

function rgb(h) {
  var n = parseInt(h.substr(1), 16);
  return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255];
}
function rgba(h) { var c = rgb(h); return [c[0], c[1], c[2], 1]; }
function nl(s) { return String(s).replace(/\n/g, '\r'); }

// ---- fonts -----------------------------------------------------------------

var FONT_MAP = { kr: {}, krd: CONFIG.KR_DISPLAY_FONTS, en: CONFIG.EN_FONTS, mono: CONFIG.MONO_FONTS };

function hasFontsApi() {
  try { return !!(app.fonts && app.fonts.allFonts); } catch (e) { return false; }
}

function psExists(ps) {
  if (!hasFontsApi()) return true; // cannot check on AE < 24, assume installed
  try {
    var r = app.fonts.getFontsByPostScriptName(ps);
    return r && r.length > 0;
  } catch (e) { return true; }
}

// Find an installed family whose name matches `re` and map our weights onto
// its styles. Returns {400:ps,500:ps,700:ps,900:ps,family:name} or null.
function findFamily(re) {
  if (!hasFontsApi()) return null;
  var fams;
  try { fams = app.fonts.allFonts; } catch (e) { return null; }
  var WANT = {
    400: [/^regular$/i, /\brg\b/i, /^04/, /^book$/i, /^normal$/i, /^roman$/i],
    500: [/^medium$/i, /\bmd\b/i, /^05/],
    600: [/^semibold$/i, /\bsb\b/i, /^06/, /^demibold$/i],
    700: [/^bold$/i, /\bbd\b/i, /^07/],
    800: [/^extrabold$/i, /\beb\b/i, /^08/, /^heavy$/i],
    900: [/^heavy$/i, /^black$/i, /\bhv\b/i, /^09/]
  };
  var best = null;
  for (var i = 0; i < fams.length; i++) {
    var fam = fams[i];
    if (!fam || !fam.length) continue;
    var fname = fam[0].familyName || '';
    if (!re.test(fname)) continue;
    var map = { family: fname }, hits = 0;
    for (var w in WANT) {
      if (!WANT.hasOwnProperty(w)) continue;
      var pats = WANT[w];
      for (var p = 0; p < pats.length && !map[w]; p++) {
        for (var j = 0; j < fam.length; j++) {
          var f = fam[j];
          if (f.isSubstitute) continue;
          if (pats[p].test(f.styleName || '')) { map[w] = f.postScriptName; hits++; break; }
        }
      }
    }
    if (hits >= 2 && (!best || hits > best.hits)) { map.hits = hits; best = map; }
  }
  if (!best) return null;
  // fill gaps with the nearest available weight
  var order = [400, 500, 600, 700, 800, 900];
  for (var k = 0; k < order.length; k++) {
    if (best[order[k]]) continue;
    for (var d = 1; d < 6 && !best[order[k]]; d++) {
      if (k - d >= 0 && best[order[k - d]]) best[order[k]] = best[order[k - d]];
      else if (k + d < order.length && best[order[k + d]]) best[order[k]] = best[order[k + d]];
    }
  }
  return best;
}

// Korean text family for one video. 'sandoll' tries the installed Sandoll
// Cloud families in CONFIG.SANDOLL_PREFS[videoId] order (그레타산스, 고딕Neo3, …),
// then falls back to the presets in CONFIG.KR_AUTO_ORDER.
function chooseKoreanFont(videoId) {
  var pick = CONFIG.KR_FONT;
  var P = CONFIG.KR_PRESETS;
  if (CONFIG.KR_FONT_OVERRIDE && CONFIG.KR_FONT_OVERRIDE[700]) {
    REPORT.krFamily = 'override';
    return CONFIG.KR_FONT_OVERRIDE;
  }
  if (pick === 'sandoll') {
    var prefs = (CONFIG.SANDOLL_PREFS && CONFIG.SANDOLL_PREFS[videoId]) || [];
    for (var j = 0; j < prefs.length; j++) {
      var fam = findFamily(new RegExp(prefs[j], 'i'));
      if (fam) { REPORT.krFamily = fam.family; return fam; }
    }
    var any = findFamily(/sandoll|산돌/i);
    if (any) { REPORT.krFamily = any.family; return any; }
    if (hasFontsApi()) warn('No Sandoll family found; using ' + P[CONFIG.KR_AUTO_ORDER[0]].label + '.');
    pick = 'auto';
  }
  if (pick === 'auto') {
    // presets in priority order, first one that is installed
    var order = CONFIG.KR_AUTO_ORDER;
    if (!hasFontsApi()) {
      // AE < 24 cannot list fonts: use the design font and report it
      REPORT.krFamily = P[order[0]].label + ' (please make sure it is installed)';
      return P[order[0]];
    }
    for (var i = 0; i < order.length; i++) {
      var pr = P[order[i]];
      if (psExists(pr[700])) {
        REPORT.krFamily = pr.label;
        return pr;
      }
    }
    REPORT.krFamily = P[order[0]].label + ' (not found - please install)';
    return P[order[0]];
  }
  REPORT.krFamily = P[pick].label;
  return P[pick];
}

function fontFor(f, w) {
  var m = FONT_MAP[f] || FONT_MAP.kr;
  var ps = m[w];
  if (!ps) {
    var keys = [500, 600, 700, 400, 800, 900];
    for (var i = 0; i < keys.length && !ps; i++) ps = m[keys[i]];
  }
  if (!psExists(ps)) {
    REPORT.missingFonts[ps] = true;
    // missing display/Latin faces -> use the Korean text family so nothing renders as a substitute font
    if (f !== 'kr') ps = FONT_MAP.kr[f === 'krd' ? 800 : w >= 600 ? 700 : 500] || FONT_MAP.kr[700] || ps;
  }
  return ps;
}

// ---- properties & keyframes --------------------------------------------------

function dimsOf(prop) {
  var t = prop.propertyValueType;
  if (t === PropertyValueType.ThreeD_SPATIAL || t === PropertyValueType.ThreeD) return 3;
  if (t === PropertyValueType.TwoD_SPATIAL || t === PropertyValueType.TwoD) return 2;
  return 1;
}
function isSpatial(prop) {
  var t = prop.propertyValueType;
  return t === PropertyValueType.ThreeD_SPATIAL || t === PropertyValueType.TwoD_SPATIAL;
}
// pad / trim array values to the property's dimension (z: 0 for position, 100 for scale)
function fit(prop, v, z) {
  if (!(v instanceof Array)) return v;
  var n = dimsOf(prop);
  if (n === 3 && v.length === 2) return [v[0], v[1], z];
  if (n === 2 && v.length === 3) return [v[0], v[1]];
  return v;
}

function easeArr(n, infl) {
  var a = [];
  var v = Math.max(0.1, Math.min(100, infl * 100));
  for (var i = 0; i < n; i++) a.push(new KeyframeEase(0, v));
  return a;
}
function setEase(prop, k, inInf, outInf) {
  var n = isSpatial(prop) ? 1 : dimsOf(prop);
  var tries = [n, 1, 2, 3];
  for (var i = 0; i < tries.length; i++) {
    try { prop.setTemporalEaseAtKey(k, easeArr(tries[i], inInf), easeArr(tries[i], outInf)); return; } catch (e) {}
  }
}
function interpOf(seg, side) {
  if (seg === 'h') return side === 'out' ? KIT.HOLD : KIT.LINEAR;
  if (!seg || seg === 'l') return KIT.LINEAR;
  return KIT.BEZIER;
}

function applyKF(prop, kf, z) {
  if (!kf || !kf.length) return;
  var times = [], vals = [], i;
  for (i = 0; i < kf.length; i++) { times.push(kf[i][0]); vals.push(fit(prop, kf[i][1], z)); }
  prop.setValuesAtTimes(times, vals);
  for (i = 0; i < kf.length; i++) {
    var k = prop.nearestKeyIndex(kf[i][0]);
    var segOut = kf[i][2] || 'l';
    var segIn = i > 0 ? (kf[i - 1][2] || 'l') : segOut;
    var tin = interpOf(segIn, 'in'), tout = interpOf(segOut, 'out');
    try { prop.setInterpolationTypeAtKey(k, tin, tout); } catch (e) {}
    if (tin === KIT.BEZIER || tout === KIT.BEZIER) {
      var ei = tin === KIT.BEZIER ? DATA_EASES[segIn][1] : 0.1667;
      var eo = tout === KIT.BEZIER ? DATA_EASES[segOut][0] : 0.1667;
      setEase(prop, k, ei, eo);
    }
    if (isSpatial(prop)) {
      try { prop.setSpatialAutoBezierAtKey(k, false); } catch (e1) {}
      try { prop.setSpatialContinuousAtKey(k, false); } catch (e2) {}
      try { prop.setSpatialTangentsAtKey(k, [0, 0, 0], [0, 0, 0]); } catch (e3) {
        try { prop.setSpatialTangentsAtKey(k, [0, 0], [0, 0]); } catch (e4) {}
      }
    }
  }
}

// value | keyframes | expression on one property
function drive(prop, staticVal, kf, expr, z) {
  if (expr) { prop.expression = expr; if (staticVal !== undefined) try { prop.setValue(fit(prop, staticVal, z)); } catch (e) {} return; }
  if (kf && kf.length) { applyKF(prop, kf, z); return; }
  if (staticVal !== undefined) prop.setValue(fit(prop, staticVal, z));
}

function addEffect(layer, matchName) {
  var parade = layer.property('ADBE Effect Parade');
  parade.addProperty(matchName);
  return layer.property('ADBE Effect Parade').property(layer.property('ADBE Effect Parade').numProperties);
}

// ---- layer builders ------------------------------------------------------------

function buildText(comp, L) {
  var str = L.cnt ? L.cntFinal : L.tx;
  var lay = comp.layers.addText(nl(str));
  var stp = lay.property('ADBE Text Properties').property('ADBE Text Document');
  var td = stp.value;
  try { td.resetCharStyle(); } catch (e) {}
  try { td.resetParagraphStyle(); } catch (e2) {}
  td.text = nl(str);
  td.font = fontFor(L.f, L.w);
  td.fontSize = L.sz;
  td.applyFill = true;
  td.fillColor = rgb(L.c);
  td.applyStroke = false;
  td.tracking = L.tr;
  td.justification = L.al === 'c' ? ParagraphJustification.CENTER_JUSTIFY : L.al === 'r' ? ParagraphJustification.RIGHT_JUSTIFY : ParagraphJustification.LEFT_JUSTIFY;
  try { td.autoLeading = false; td.leading = L.ld; } catch (e3) {}
  stp.setValue(td);
  if (L.cntAE) stp.expression = L.cntAE;
  if (L.trk) {
    try {
      var ta = lay.property('ADBE Text Properties').property('ADBE Text Animators');
      ta.addProperty('ADBE Text Animator');
      var tn = lay.property('ADBE Text Properties').property('ADBE Text Animators').numProperties;
      var tAn = lay.property('ADBE Text Properties').property('ADBE Text Animators').property(tn);
      tAn.name = 'Tracking';
      tAn.property('ADBE Text Animator Properties').addProperty('ADBE Text Tracking Amount');
      tAn = lay.property('ADBE Text Properties').property('ADBE Text Animators').property(tn);
      applyKF(tAn.property('ADBE Text Animator Properties').property('ADBE Text Tracking Amount'), L.trk);
    } catch (e5) { warn('tracking animation skipped on "' + L.n + '": ' + e5); }
  }
  if (L.rv) {
    try {
      var anims = lay.property('ADBE Text Properties').property('ADBE Text Animators');
      anims.addProperty('ADBE Text Animator');
      var ai = lay.property('ADBE Text Properties').property('ADBE Text Animators').numProperties;
      var an = lay.property('ADBE Text Properties').property('ADBE Text Animators').property(ai);
      an.name = 'Reveal';
      an.property('ADBE Text Animator Properties').addProperty('ADBE Text Opacity');
      an = lay.property('ADBE Text Properties').property('ADBE Text Animators').property(ai);
      an.property('ADBE Text Animator Properties').property('ADBE Text Opacity').setValue(0);
      an.property('ADBE Text Selectors').addProperty('ADBE Text Selector');
      an = lay.property('ADBE Text Properties').property('ADBE Text Animators').property(ai);
      var start = an.property('ADBE Text Selectors').property(1).property('ADBE Text Percent Start');
      applyKF(start, [[L.rv.t0, 0, L.rv.e], [L.rv.t1, 100, 'l']]);
    } catch (e4) { warn('text reveal skipped on "' + L.n + '": ' + e4); }
  }
  return lay;
}

function vecs(lay, gi) {
  return lay.property('ADBE Root Vectors Group').property(gi).property('ADBE Vectors Group');
}

function buildItem(lay, it) {
  var root = lay.property('ADBE Root Vectors Group');
  root.addProperty('ADBE Vector Group');
  var gi = lay.property('ADBE Root Vectors Group').numProperties;
  var geo = it.t === 'rect' ? 'ADBE Vector Shape - Rect' : it.t === 'ell' ? 'ADBE Vector Shape - Ellipse' : 'ADBE Vector Shape - Group';
  vecs(lay, gi).addProperty(geo);
  if (it.tm) vecs(lay, gi).addProperty('ADBE Vector Filter - Trim');
  if (it.st) vecs(lay, gi).addProperty('ADBE Vector Graphic - Stroke');
  if (it.fl) vecs(lay, gi).addProperty('ADBE Vector Graphic - Fill');

  var g = vecs(lay, gi).property(geo);
  if (it.t === 'rect') {
    g.property('ADBE Vector Rect Size').setValue(it.sz);
    g.property('ADBE Vector Rect Position').setValue(it.ps);
    if (it.rd) g.property('ADBE Vector Rect Roundness').setValue(Math.min(it.rd, it.sz[0] / 2, it.sz[1] / 2));
  } else if (it.t === 'ell') {
    g.property('ADBE Vector Ellipse Size').setValue(it.sz);
    g.property('ADBE Vector Ellipse Position').setValue(it.ps);
  } else {
    var sh = new Shape();
    sh.vertices = it.v;
    if (it.ti) { sh.inTangents = it.ti; sh.outTangents = it.to; }
    sh.closed = !!it.cl;
    g.property('ADBE Vector Shape').setValue(sh);
  }
  if (it.tm) {
    var tm = vecs(lay, gi).property('ADBE Vector Filter - Trim');
    if (typeof it.tm.s === 'number') tm.property('ADBE Vector Trim Start').setValue(it.tm.s); else if (it.tm.s) applyKF(tm.property('ADBE Vector Trim Start'), it.tm.s);
    if (typeof it.tm.e === 'number') tm.property('ADBE Vector Trim End').setValue(it.tm.e); else if (it.tm.e) applyKF(vecs(lay, gi).property('ADBE Vector Filter - Trim').property('ADBE Vector Trim End'), it.tm.e);
  }
  if (it.st) {
    var st = vecs(lay, gi).property('ADBE Vector Graphic - Stroke');
    st.property('ADBE Vector Stroke Color').setValue(rgba(it.st.c));
    st.property('ADBE Vector Stroke Opacity').setValue(it.st.o === undefined ? 100 : it.st.o);
    st.property('ADBE Vector Stroke Width').setValue(it.st.w);
    try { st.property('ADBE Vector Stroke Line Cap').setValue(it.st.cap === 'b' ? 1 : 2); } catch (e) {}
    try { st.property('ADBE Vector Stroke Line Join').setValue(2); } catch (e2) {}
  }
  if (it.fl) {
    var fl = vecs(lay, gi).property('ADBE Vector Graphic - Fill');
    fl.property('ADBE Vector Fill Color').setValue(rgba(it.fl.c));
    fl.property('ADBE Vector Fill Opacity').setValue(it.fl.o);
  }
  // group transform: anchor at the item (or it.ga), so group scale pivots there
  var A = it.ga || (it.t === 'path' ? [0, 0] : it.ps);
  var gt = lay.property('ADBE Root Vectors Group').property(gi).property('ADBE Vector Transform Group');
  gt.property('ADBE Vector Anchor').setValue(A);
  var ge = it.geAE || {};
  var gk = it.gkf || {};
  drive(gt.property('ADBE Vector Position'), A, gk.p, ge.p, 0);
  drive(lay.property('ADBE Root Vectors Group').property(gi).property('ADBE Vector Transform Group').property('ADBE Vector Scale'), undefined, gk.s, ge.s, 100);
  drive(lay.property('ADBE Root Vectors Group').property(gi).property('ADBE Vector Transform Group').property('ADBE Vector Group Opacity'), it.go, gk.o, ge.o);
  if (gk.r || ge.r) drive(lay.property('ADBE Root Vectors Group').property(gi).property('ADBE Vector Transform Group').property('ADBE Vector Rotation'), undefined, gk.r, ge.r);
}

function buildShape(comp, L) {
  var lay = comp.layers.addShape();
  // reverse order: AE draws the top of the contents list in front
  for (var i = L.it.length - 1; i >= 0; i--) buildItem(lay, L.it[i]);
  return lay;
}

function buildRamp(comp, L) {
  var lay = comp.layers.addSolid(rgb(L.rp.c1), L.n, Math.round(L.sz[0]), Math.round(L.sz[1]), 1, comp.duration);
  var fx = addEffect(lay, 'ADBE Ramp');
  fx.property('ADBE Ramp-0001').setValue(L.rp.p1);
  fx.property('ADBE Ramp-0002').setValue(rgba(L.rp.c1));
  fx.property('ADBE Ramp-0003').setValue(L.rp.p2);
  fx.property('ADBE Ramp-0004').setValue(rgba(L.rp.c2));
  fx.property('ADBE Ramp-0005').setValue(L.rp.t === 'rad' ? 2 : 1);
  return lay;
}

function buildAdjust(comp, L) {
  var lay = comp.layers.addSolid([1, 1, 1], L.n, comp.width, comp.height, 1, comp.duration);
  lay.adjustmentLayer = true;
  if (L.fx && L.fx.noise) {
    try {
      var fx = addEffect(lay, 'ADBE Noise');
      fx.property('ADBE Noise-0001').setValue(L.fx.noise);
      try { fx.property('ADBE Noise-0002').setValue(0); } catch (e) {}
    } catch (e2) { warn('grain skipped: ' + e2); }
  }
  return lay;
}

var BLENDS = { screen: 'SCREEN', add: 'ADD', multiply: 'MULTIPLY', overlay: 'OVERLAY' };

function finishLayer(comp, lay, L, isMatte) {
  lay.name = L.n || lay.name;
  var nested = L.k === 'comp' || L.k === 'slot';
  if (nested) lay.startTime = L['in'] || 0;
  var inT = L['in'] || 0, outT = L.out === undefined ? comp.duration : L.out;
  try {
    if (!nested) lay.startTime = 0;
    lay.inPoint = Math.max(0, inT);
    lay.outPoint = Math.min(comp.duration, Math.max(inT + 1 / DATA_FPS, outT));
  } catch (e) {}
  var tr = lay.property('ADBE Transform Group');
  var ex = L.exAE || {};
  var kf = L.kf || {};
  if (L.a || L.k === 'text' || L.k === 'shape') tr.property('ADBE Anchor Point').setValue(fit(tr.property('ADBE Anchor Point'), L.a || [0, 0], 0));
  if (L.k === 'img' && L.pv) tr.property('ADBE Anchor Point').setValue(fit(tr.property('ADBE Anchor Point'), [L.pv[0] * L._fw, L.pv[1] * L._fh], 0));
  drive(tr.property('ADBE Position'), L.p || [0, 0], kf.p, ex.p, 0);
  var sk = L._k || 1;
  var sKf = kf.s;
  if (sk !== 1 && sKf) { sKf = []; for (var q = 0; q < kf.s.length; q++) sKf.push([kf.s[q][0], [kf.s[q][1][0] * sk, kf.s[q][1][1] * sk], kf.s[q][2]]); }
  var sVal = L.s ? [L.s[0] * sk, L.s[1] * sk] : (sk !== 1 ? [100 * sk, 100 * sk] : undefined);
  // image layers carry their fit factor, so a scale expression is multiplied by it
  var sEx = ex.s && sk !== 1 ? 'var _s = ' + ex.s + '; [_s[0]*' + sk + ', _s[1]*' + sk + ']' : ex.s;
  drive(lay.property('ADBE Transform Group').property('ADBE Scale'), sVal, sKf, sEx, 100);
  if (L.r !== undefined || kf.r || ex.r) drive(lay.property('ADBE Transform Group').property('ADBE Rotate Z'), L.r, kf.r, ex.r);
  drive(lay.property('ADBE Transform Group').property('ADBE Opacity'), L.o, kf.o, ex.o);
  if (L.bl && BLENDS[L.bl]) lay.blendingMode = BlendingMode[BLENDS[L.bl]];
  if (L.fx) {
    if (L.fx.tint) {
      try {
        var t = addEffect(lay, 'ADBE Tint');
        t.property('ADBE Tint-0001').setValue(rgba(L.fx.tint[0]));
        t.property('ADBE Tint-0002').setValue(rgba(L.fx.tint[1]));
        t.property('ADBE Tint-0003').setValue(100);
      } catch (e2) { warn('tint skipped: ' + e2); }
    }
    if (L.fx.blur || L.fx.blurKf) {
      var b = addEffect(lay, 'ADBE Gaussian Blur 2');
      if (L.fx.blurKf) applyKF(b.property('ADBE Gaussian Blur 2-0001'), L.fx.blurKf);
      else b.property('ADBE Gaussian Blur 2-0001').setValue(L.fx.blur);
      try { lay.property('ADBE Effect Parade').property(lay.property('ADBE Effect Parade').numProperties).property('ADBE Gaussian Blur 2-0003').setValue(1); } catch (e3) {}
    }
  }
  if (L.guide) lay.guideLayer = true;
  if (L.mt) {
    var m = buildLayer(comp, L.mt, true);
    setMatte(lay, m);
  }
  return lay;
}

function setMatte(lay, matte) {
  try {
    if (typeof lay.setTrackMatte === 'function') {
      lay.setTrackMatte(matte, TrackMatteType.ALPHA);
      matte.enabled = false;
      return;
    }
  } catch (e) {}
  // legacy: the matte is the layer directly above (it was created right after)
  lay.trackMatteType = TrackMatteType.ALPHA;
  matte.enabled = false;
}

var FOOTAGE = {};
// image layers (stickers): file path is relative to the project root (one level above this script)
function buildImage(comp, L) {
  var f = FOOTAGE[L.src];
  if (!f) {
    var file = new File(SCRIPT_DIR + '/../' + L.src);
    if (!file.exists) file = new File(SCRIPT_DIR + '/' + L.src);
    if (!file.exists) throw new Error('missing image ' + L.src);
    f = app.project.importFile(new ImportOptions(file));
    f.parentFolder = folder('05_CHARACTER', folder(CONFIG.ROOT_FOLDER));
    FOOTAGE[L.src] = f;
  }
  var lay = comp.layers.add(f);
  L._k = Math.min(L.fit[0] / f.width, L.fit[1] / f.height);
  L._fw = f.width;
  L._fh = f.height;
  return lay;
}

var CTX = null; // { video, scenes: {id: CompItem}, slots: {id: CompItem} }

function buildLayer(comp, L, isMatte) {
  var lay;
  if (L.k === 'text') lay = buildText(comp, L);
  else if (L.k === 'shape') lay = buildShape(comp, L);
  else if (L.k === 'ramp') lay = buildRamp(comp, L);
  else if (L.k === 'adjust') lay = buildAdjust(comp, L);
  else if (L.k === 'comp') lay = comp.layers.add(CTX.scenes[L.ref]);
  else if (L.k === 'slot') lay = comp.layers.add(CTX.slots[L.ref]);
  else if (L.k === 'img') lay = buildImage(comp, L);
  else throw new Error('unknown layer kind ' + L.k);
  return finishLayer(comp, lay, L, isMatte);
}

function fillComp(comp, layers) {
  for (var i = 0; i < layers.length; i++) {
    try { buildLayer(comp, layers[i]); } catch (e) { warn(comp.name + ' / ' + layers[i].n + ': ' + e.toString() + (e.line ? ' (line ' + e.line + ')' : '')); }
  }
}

// ---- project structure -----------------------------------------------------------

function folder(name, parent) {
  var items = app.project.items;
  for (var i = 1; i <= items.length; i++) {
    var it = items[i];
    if (it instanceof FolderItem && it.name === name && (!parent || it.parentFolder === parent)) return it;
  }
  var f = items.addFolder(name);
  if (parent) f.parentFolder = parent;
  return f;
}

var SLOT_CACHE = {};

function makeSlot(id, S, parent) {
  var key = S.name || id;
  if (SLOT_CACHE[key]) return SLOT_CACHE[key];
  var c = app.project.items.addComp(key, S.w, S.h, 1, S.dur, DATA_FPS);
  c.parentFolder = parent;
  c.bgColor = [0, 0, 0];
  SLOT_CACHE[key] = c;
  CTX.slots[id] = c;
  fillComp(c, S.layers || []);
  // guide note (never renders)
  var note = S.desc + (S.search ? '\r\r' + CONFIG.TXT_SEARCH + ' ' + S.search.join('  /  ') : '') + '\r\r' + CONFIG.TXT_SLOT_HOWTO;
  var g = comp_note(c, note);
  g.guideLayer = true;
  g.moveToEnd();
  return c;
}

function comp_note(comp, str) {
  var lay = comp.layers.addText(nl(str));
  var stp = lay.property('ADBE Text Properties').property('ADBE Text Document');
  var td = stp.value;
  td.text = nl(str);
  td.font = fontFor('kr', 500);
  td.fontSize = comp.height > 400 ? 34 : 20;
  td.applyFill = true;
  td.fillColor = [0.6, 0.98, 0.89];
  td.justification = ParagraphJustification.CENTER_JUSTIFY;
  stp.setValue(td);
  lay.name = 'README (guide layer)';
  lay.property('ADBE Transform Group').property('ADBE Position').setValue([comp.width / 2, comp.height / 2 - (comp.height > 400 ? 80 : 40)]);
  return lay;
}

function buildVideo(video, root) {
  CTX = { video: video, scenes: {}, slots: CTX ? CTX.slots : {} };
  var fScenes = folder('02_SCENES_' + video.id.toUpperCase(), root);
  var fSlots = folder(CONFIG.SLOT_FOLDER, root);
  var fMain = folder('01_MAIN', root);

  // slots first (shared LOGO comp is reused across videos)
  for (var sid in video.slots) {
    if (!video.slots.hasOwnProperty(sid)) continue;
    var S = video.slots[sid];
    if (sid === 'LOGO') S.dur = Math.max(S.dur, DATA_MAX_DUR);
    CTX.slots[sid] = makeSlot(sid, S, fSlots);
  }
  // scene precomps
  for (var i = 0; i < video.order.length; i++) {
    var o = video.order[i];
    var sc = video.scenes[o.id];
    var c = app.project.items.addComp(video.id.toUpperCase() + '_' + sc.name, video.w, video.h, 1, sc.dur, video.fps);
    c.parentFolder = fScenes;
    c.bgColor = rgb(DATA_BG);
    CTX.scenes[o.id] = c;
    fillComp(c, sc.layers);
    log('scene ' + c.name + ' done');
  }
  // main comp
  var main = app.project.items.addComp(video.name, video.w, video.h, 1, video.dur, video.fps);
  main.parentFolder = fMain;
  main.bgColor = rgb(DATA_BG);
  fillComp(main, video.layers);
  for (var m = 0; m < video.order.length; m++) {
    try { main.markerProperty.setValueAtTime(video.order[m].start, new MarkerValue(video.order[m].name)); } catch (e) {}
  }
  // soundtrack next to this script: audio/<id>_mix.wav (ElevenLabs) or audio/temp_music_<id>.wav
  try {
    var cands = [video.id + '_mix.wav', video.id + '_mix.mp3', 'temp_music_' + video.id + '.mp3', 'temp_music_' + video.id + '.wav'];
    var af = null, isMix = false;
    for (var ci = 0; ci < cands.length && !af; ci++) {
      var cf = new File(SCRIPT_DIR + '/audio/' + cands[ci]);
      if (cf.exists) { af = cf; isMix = ci < 2; }
    }
    if (af) {
      var fAudio = folder('04_AUDIO', root);
      var item = app.project.importFile(new ImportOptions(af));
      item.parentFolder = fAudio;
      var al = main.layers.add(item);
      al.name = isMix ? 'AUDIO MIX (ElevenLabs VO + music + SFX)' : 'TEMP MUSIC (replace with the ElevenLabs mix)';
      al.moveToEnd();
    }
  } catch (e2) { warn('music import skipped: ' + e2); }
  return main;
}

function main() {
  if (!app.project) app.newProject();
  app.beginUndoGroup('Build Elysium promo');
  var t0 = new Date().getTime();
  var fontsUsed = [];
  var root = folder(CONFIG.ROOT_FOLDER);
  var built = [];
  for (var i = 0; i < CONFIG.BUILD.length; i++) {
    var v = DATA.videos[CONFIG.BUILD[i]];
    if (!v) continue;
    FONT_MAP.kr = chooseKoreanFont(v.id);
    fontsUsed.push(v.id + ': ' + REPORT.krFamily);
    built.push(buildVideo(v, root));
  }
  app.endUndoGroup();
  if (built.length) built[0].openInViewer();
  var miss = [];
  for (var f in REPORT.missingFonts) if (REPORT.missingFonts.hasOwnProperty(f)) miss.push(f);
  var msg = CONFIG.TXT_DONE + ' (' + Math.round((new Date().getTime() - t0) / 1000) + 's)\r\r';
  msg += CONFIG.TXT_KR_FONT + ' ' + fontsUsed.join(' / ') + '\r';
  if (miss.length) msg += '\r' + CONFIG.TXT_MISSING + '\r' + miss.join(', ') + '\r';
  msg += '\r' + CONFIG.TXT_NEXT;
  if (REPORT.warnings.length) msg += '\r\r' + CONFIG.TXT_WARN + ' ' + REPORT.warnings.length + '\r' + REPORT.warnings.slice(0, 8).join('\r');
  alert(msg, 'Elysium Promo');
}

main();
