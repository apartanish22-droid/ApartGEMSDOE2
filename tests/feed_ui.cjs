const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../docs/assets/feed.js'), 'utf8');

class Element {
  constructor() { this.textContent = ''; this.className = ''; this.children = []; }
  append(...children) { this.children.push(...children); }
  appendChild(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
}
async function run(feed, reject = false) {
  const nodes = Object.fromEntries(['leader-value', 'leader-age', 'feed-checked', 'feed-grid'].map(id => [id, new Element()]));
  const document = { getElementById: id => nodes[id] || null, createElement: () => new Element(), createTextNode: t => ({textContent: t}) };
  const fetch = () => reject ? Promise.reject(new Error('offline')) : Promise.resolve({ok: true, json: () => Promise.resolve(feed)});
  vm.runInNewContext(source, {document, fetch, Date, Object, String, Number, Error});
  await new Promise(resolve => setTimeout(resolve, 10));
  return nodes;
}
(async () => {
  const now = new Date().toISOString();
  const x = await run({updated_utc: now, leaderboard: {status:'ok', top_public_value:'0.4544', last_success_utc:now}, site_heads:{GEMSDOE24:{status:'ok', head_sha:'a'.repeat(40), audited_archive_ref:'b'.repeat(40), last_success_utc:now, changed_since_previous_check:false, differs_from_archive:false}, badkey:{status:'ok', last_success_utc:now}}});
  assert.equal(x['leader-value'].textContent, '0.4544');
  assert.match(x['leader-age'].textContent, /^Observed/);
  assert.match(x['feed-checked'].textContent, /^1\/9/);
  assert.equal(x['feed-grid'].children.length, 1);
  assert.match(x['feed-grid'].children[0].children[1].textContent, /not re-audited/);
  const stale = await run({updated_utc:now, leaderboard:{status:'stale',top_public_value:'0.4544',last_success_utc:now},site_heads:{}});
  assert.match(stale['leader-age'].textContent, /^STALE/);
  const partial = await run({updated_utc:now, leaderboard:{status:'unavailable'}, site_heads:{GEMSDOE24:{status:'ok', head_sha:'a'.repeat(40), last_success_utc:now}}});
  assert.equal(partial['leader-value'].textContent, '—');
  assert.match(partial['feed-checked'].textContent, /^1\/9/);
  assert.match(partial['feed-grid'].children[0].children[1].textContent, /archive reference unknown/);
  const offline = await run({}, true);
  assert.match(offline['leader-age'].textContent, /unavailable/);
  console.log('feed UI: success, stale and failure states passed');
})().catch(e => { console.error(e); process.exit(1); });
