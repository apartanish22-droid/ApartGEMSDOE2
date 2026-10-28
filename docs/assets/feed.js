(function () {
  'use strict';
  const value = document.getElementById('leader-value');
  const age = document.getElementById('leader-age');
  const siteCheck = document.getElementById('feed-checked');
  const grid = document.getElementById('feed-grid');
  if (!value || !age) return;
  const maxAge = 24 * 3600 * 1000;
  function isStale(status, date) {
    const time = new Date(date).getTime();
    return status !== 'ok' || Number.isNaN(time) || Date.now() - time > maxAge || time > Date.now() + 300000;
  }
  function siteIsStale(item) {
    return !item || !/^[0-9a-f]{40}$/.test(item.head_sha || '') || isStale(item.status, item.last_success_utc);
  }
  function archiveDrift(item) {
    if (!item || !/^[0-9a-f]{40}$/.test(item.head_sha || '') || !/^[0-9a-f]{40}$/.test(item.audited_archive_ref || '')) return null;
    return item.head_sha !== item.audited_archive_ref;
  }
  fetch('data/source_feed.json', { cache: 'no-store' })
    .then(response => { if (!response.ok) throw new Error('Feed unavailable'); return response.json(); })
    .then(feed => {
      const l = feed.leaderboard || {};
      const observed = new Date(l.last_success_utc);
      if (!/^(?:0(?:\.\d+)?|1(?:\.0+)?)$/.test(String(l.top_public_value || '')) || !l.last_success_utc || Number.isNaN(observed.getTime())) {
        value.textContent = '—';
        age.textContent = 'Leaderboard unavailable · check official page';
      } else {
        const stale = isStale(l.status, l.last_success_utc);
        value.textContent = l.top_public_value;
        age.textContent = (stale ? 'STALE · ' : 'Observed · ') + observed.toISOString().replace('T', ' ').slice(0, 16) + ' UTC';
      }
      if (siteCheck) {
        const entries = Object.entries(feed.site_heads || {}).filter(([name]) => /^GEMSDOE(?:24|25|27|28|30|31|32|33|36)$/.test(name));
        const current = entries.filter(([, item]) => !siteIsStale(item)).length;
        const updated = feed.updated_utc ? String(feed.updated_utc).replace('T', ' ').slice(0, 16) + ' UTC' : 'unknown';
        siteCheck.textContent = current + '/9 source heads recently checked · last check ' + updated;
        if (grid) {
          grid.replaceChildren();
          entries.sort(([a], [b]) => Number(a.slice(7)) - Number(b.slice(7))).forEach(([name, item]) => {
            const entry = document.createElement('div');
            const drift = archiveDrift(item);
            entry.className = 'feed-entry' + (drift === true ? ' changed' : '');
            const label = document.createElement('strong');
            label.textContent = name;
            const state = siteIsStale(item) ? 'stale' : drift === true ? 'differs from pinned archive; not re-audited' : drift === false ? 'at pinned archive commit' : 'archive reference unknown';
            entry.append(label, document.createTextNode(' · ' + state));
            grid.appendChild(entry);
          });
        }
      }
    })
    .catch(() => { value.textContent = '—'; age.textContent = 'Feed unavailable · check official leaderboard'; if (siteCheck) siteCheck.textContent = 'Source feed unavailable'; });
})();
