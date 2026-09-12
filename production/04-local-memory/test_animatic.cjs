// Deterministic DOM-state checks; not a substitute for visual/audio review.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = fs.readFileSync(path.join(__dirname, 'animatic.html'), 'utf8');
const evidence = html.match(/<script id="evidence" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const nodes = new Map();
const document = {getElementById(id) {
  if (!nodes.has(id)) nodes.set(id, {textContent: id === 'evidence' ? evidence : '', attrs: {},
    setAttribute(k, v) { this.attrs[k] = v; }});
  return nodes.get(id);
}};
const context = {document, window: {}, performance: {now: () => 0}, requestAnimationFrame: () => {}};
vm.createContext(context);
vm.runInContext(code, context);
for (const [frame, total, cache, over] of [[0, 9, 580, true], [120, 6, 145, false], [450, 9, 580, true]]) {
  context.window.renderFrame(frame);
  assert.equal(nodes.get('total').textContent, `TOTAL: ${total.toFixed(2)} GiB`);
  assert.equal(nodes.get('cache').attrs.width, cache);
  assert.equal(nodes.get('status').textContent, over ? 'status = over_budget' : 'status = under_budget_not_verified');
}
context.window.renderFrame(240);
const firstWidth = nodes.get('cache').attrs.width;
context.window.renderFrame(270);
assert.ok(nodes.get('cache').attrs.width > firstWidth, 'cache geometry must actually change');
context.window.renderFrame(890);
context.window.renderFrame(0);
assert.equal(nodes.get('headline').attrs.opacity, 1, 'seeking resets derived state');
assert.equal(nodes.get('headline').textContent, 'THE MODEL FITS. THE WORKLOAD?');
assert.equal(nodes.get('progress').attrs.width, 0, 'seeking resets progress');
console.log('Animatic: 13 deterministic state assertions passed; no browser/audio QA claimed.');
