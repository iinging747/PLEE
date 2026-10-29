// Checks that every AE expression string computes the same values as the
// preview formula, for every procedural spec used in the compiled videos.
import fs from 'node:fs';
import vm from 'node:vm';
import { evalExpr, aeExpr, counterValue, counterAE } from './expr.js';

let n = 0;
let bad = 0;
const near = (a, b) => (Array.isArray(a) ? a.every((x, i) => Math.abs(x - b[i]) < 1e-6) : typeof a === 'string' ? a === b : Math.abs(a - b) < 1e-6);
const run = (src, t) => new vm.Script(`(function(time){ return eval(${JSON.stringify(src)}); })`).runInNewContext({ Math })(t);
function check(spec, isCounter) {
  for (const t of [0, 0.37, 1.234, 2.5, 7.9, 13.3]) {
    const a = isCounter ? counterValue(spec, t) : evalExpr(spec, t);
    const b = run(isCounter ? counterAE(spec) : aeExpr(spec), t);
    n++;
    if (!near(a, b)) {
      bad++;
      if (bad < 10) console.log('MISMATCH', spec.fn || 'counter', t, a, b);
    }
  }
}
function visit(L) {
  if (L.ex) Object.values(L.ex).forEach((e) => check(e));
  if (L.cnt) check(L.cnt, true);
  for (const it of L.it || []) if (it.ge) Object.values(it.ge).forEach((e) => check(e));
  if (L.mt) visit(L.mt);
}
for (const id of ['pro', 'easy']) {
  const v = JSON.parse(fs.readFileSync(new URL(`../build/${id}.json`, import.meta.url)));
  v.layers.forEach(visit);
  Object.values(v.scenes).forEach((s) => s.layers.forEach(visit));
  Object.values(v.slots).forEach((s) => (s.layers || []).forEach(visit));
}
console.log(`${n} samples, ${bad} mismatches`);
process.exit(bad ? 1 : 0);
