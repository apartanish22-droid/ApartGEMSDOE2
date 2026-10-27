const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname, '../../docs/app.js'), 'utf8');

function label() {
  return { textContent: '', classList: { add() {}, remove() {} } };
}
function setup(fetchImpl) {
  const summary = { textContent: '' }, button = { disabled: false, addEventListener(_name, cb) { this.click = cb; } };
  const items = ['GEMSDOE24', 'GEMSDOE25', 'GEMSDOE27'].map(site => ({
    dataset: { site }, el: label(), querySelector() { return this.el; }
  }));
  const document = {
    getElementById(id) { return id === 'freshness-summary' ? summary : button; },
    querySelectorAll() { return items; }
  };
  vm.runInNewContext(code, { document, fetch: fetchImpl, AbortController, setTimeout, clearTimeout, Date, Promise });
  return { summary, button, items };
}
const tick = () => new Promise(resolve => setImmediate(resolve));

test('freshness detects changed heads and failures without changing verdict', async () => {
  const sha = 'a'.repeat(40), newer = 'b'.repeat(40);
  const baseline = { sites: Object.fromEntries(['24', '25', '27'].map(n => [
    `GEMSDOE${n}`, { repo: `buffedlizard55-lab/GEMSDOE${n}`, sha }
  ])) };
  const fetch = async (url) => {
    if (url === 'data/source_heads.json') return { ok: true, json: async () => baseline };
    if (url.includes('GEMSDOE27')) return { ok: false, status: 403 };
    return { ok: true, json: async () => ({ sha: url.includes('GEMSDOE25') ? newer : sha }) };
  };
  const ui = setup(fetch); await tick(); await tick();
  assert.equal(ui.items[0].el.textContent, 'No commit since snapshot');
  assert.match(ui.items[1].el.textContent, /Updated since snapshot/);
  assert.equal(ui.items[2].el.textContent, 'Live source check unavailable');
  assert.match(ui.summary.textContent, /2\/3 HEADs checked/);
  assert.match(ui.summary.textContent, /1 of checked HEADs changed/);
  assert.equal(ui.button.disabled, false);
});

test('missing baseline remains explicitly unavailable', async () => {
  const ui = setup(async () => ({ ok: false, status: 404 }));
  await tick(); await tick();
  assert.match(ui.summary.textContent, /dated snapshot/);
  assert.ok(ui.items.every(item => item.el.textContent === 'Live source check unavailable'));
  assert.equal(ui.button.disabled, false);
});
