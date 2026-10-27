/* Public HEAD freshness only. It never changes file, score, or upload verdict. */
(() => {
  const summary = document.getElementById('freshness-summary');
  const button = document.getElementById('refresh-sources');
  const rows = Array.from(document.querySelectorAll('[data-site]'));
  if (!summary || !button || rows.length === 0) return;
  let checking = false;

  async function timedFetch(url) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(url, { signal: controller.signal, cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  async function refresh() {
    if (checking) return;
    checking = true;
    button.disabled = true;
    summary.textContent = 'Checking public GitHub HEADs…';
    for (const row of rows) row.querySelector('.freshness').textContent = 'Checking source…';
    try {
      const baseline = await timedFetch('data/source_heads.json');
      let changed = 0, unavailable = 0;
      await Promise.all(rows.map(async (row) => {
        const label = row.querySelector('.freshness');
        const entry = baseline.sites && baseline.sites[row.dataset.site];
        try {
          if (!entry || !/^buffedlizard55-lab\/GEMSDOE\d+$/.test(entry.repo) || !/^[a-f0-9]{40}$/.test(entry.sha)) {
            throw new Error('Invalid baseline');
          }
          const latest = await timedFetch(`https://api.github.com/repos/${entry.repo}/commits/main`);
          if (!latest || !/^[a-f0-9]{40}$/.test(latest.sha)) throw new Error('Invalid HEAD');
          if (latest.sha === entry.sha) {
            label.textContent = 'No commit since snapshot';
            label.classList.remove('changed');
          } else {
            changed += 1;
            label.textContent = 'Updated since snapshot · not re-audited';
            label.classList.add('changed');
          }
        } catch (_) {
          unavailable += 1;
          label.textContent = 'Live source check unavailable';
          label.classList.remove('changed');
        }
      }));
      summary.textContent = `${rows.length - unavailable}/${rows.length} HEADs checked at ${new Date().toISOString()}; ${changed} of checked HEADs changed since ${baseline.observed_utc || "the baseline snapshot"}. HEAD checks do not update scores or audit new files.`;
    } catch (_) {
      for (const row of rows) row.querySelector('.freshness').textContent = 'Live source check unavailable';
      summary.textContent = 'Source check unavailable; the displayed audit is a dated snapshot, not a live score feed.';
    } finally {
      button.disabled = false;
      checking = false;
    }
  }
  button.addEventListener('click', refresh);
  refresh();
})();
