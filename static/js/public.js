// ─── Helpers ──────────────────────────────────────────────────────────────────
function esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function toast(msg, duration = 3500) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.style.display = 'flex';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = 'none'; }, duration);
}

function currentJobId() {
  const parts = location.pathname.split('/').filter(Boolean);
  return parts[1] || '';
}

// ─── Job list page ─────────────────────────────────────────────────────────────
async function loadJobsList() {
  const list = document.getElementById('job-list');
  try {
    const res = await fetch('/api/public/jobs');
    const jobs = await res.json();

    if (!jobs.length) {
      list.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="7" width="20" height="14" rx="2" stroke="currentColor" stroke-width="1.75"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" stroke="currentColor" stroke-width="1.75"/></svg>
          </div>
          <h4>No open positions right now</h4>
          <p>Please check back soon — new roles are posted regularly.</p>
        </div>`;
      return;
    }

    list.innerHTML = jobs.map(j => {
      const parsed = j.parsed_json ? JSON.parse(j.parsed_json) : null;
      const meta = parsed
        ? [parsed.seniority_level, parsed.experience_years ? `${parsed.experience_years}+ yrs` : null].filter(Boolean).join(' · ')
        : 'Details inside';
      return `
        <a class="job-card" href="/jobs/${j.id}">
          <h3>${esc(j.title)}</h3>
          <div class="job-card-meta">${esc(meta)}</div>
          <span class="btn btn-secondary btn-sm">View & Apply</span>
        </a>`;
    }).join('');
  } catch (e) {
    list.innerHTML = `<p style="color:var(--red)">Could not load jobs right now.</p>`;
  }
}

// ─── Job detail page ────────────────────────────────────────────────────────────
async function loadJobDetail() {
  const wrap = document.getElementById('job-detail');
  const jobId = currentJobId();
  try {
    const res = await fetch(`/api/public/jobs/${jobId}`);
    if (!res.ok) {
      wrap.innerHTML = `
        <div class="job-closed">
          <h2>This job isn't accepting applications</h2>
          <p>It may have closed or the link is incorrect.</p>
          <p style="margin-top:16px"><a href="/jobs" class="btn btn-secondary btn-sm">← See all open positions</a></p>
        </div>`;
      return;
    }
    const jd = await res.json();
    const parsed = jd.parsed_json ? JSON.parse(jd.parsed_json) : null;
    document.title = jd.title + ' — Careers';
    document.getElementById('apply-modal-title').textContent = `Apply — ${jd.title}`;

    const applyBar = `<div class="apply-bar"><button class="btn btn-primary btn-lg" onclick="showPublicModal('apply-modal')">Apply for this role</button></div>`;

    wrap.innerHTML = `
      <div class="job-detail-hero">
        <h1>${esc(jd.title)}</h1>
        ${parsed ? `<div class="job-detail-meta">
          ${parsed.department ? `<span class="badge badge-blue">${esc(parsed.department)}</span>` : ''}
          ${parsed.seniority_level ? `<span class="badge badge-gray">${esc(parsed.seniority_level)}</span>` : ''}
          ${parsed.experience_years ? `<span class="badge badge-gray">${parsed.experience_years}+ yrs experience</span>` : ''}
        </div>` : ''}
      </div>

      ${applyBar}

      ${parsed && parsed.summary ? `<div class="job-detail-section"><h4>About the role</h4><p>${esc(parsed.summary)}</p></div>` : ''}

      ${parsed && parsed.responsibilities?.length ? `<div class="job-detail-section"><h4>Responsibilities</h4><ul>${parsed.responsibilities.map(r=>`<li>${esc(r)}</li>`).join('')}</ul></div>` : ''}

      ${parsed && parsed.required_skills?.length ? `<div class="job-detail-section"><h4>Required Skills</h4><div class="tags">${parsed.required_skills.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div></div>` : ''}

      ${parsed && parsed.preferred_skills?.length ? `<div class="job-detail-section"><h4>Preferred Skills</h4><div class="tags">${parsed.preferred_skills.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div></div>` : ''}

      ${!parsed ? `<div class="job-detail-section"><p>${esc(jd.raw_text)}</p></div>` : ''}

      ${applyBar}
    `;
  } catch (e) {
    wrap.innerHTML = `<p style="color:var(--red)">Could not load this job right now.</p>`;
  }
}

// ─── Apply modal ────────────────────────────────────────────────────────────────
function showPublicModal(id) { document.getElementById(id).style.display = 'flex'; }
function hidePublicModal(id) { document.getElementById(id).style.display = 'none'; }

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-overlay').forEach(el => {
    el.addEventListener('click', e => { if (e.target === el) el.style.display = 'none'; });
  });

  const zone = document.getElementById('apply-drop-zone');
  const input = document.getElementById('apply-file');
  if (!zone || !input) return;

  zone.addEventListener('click', () => input.click());
  input.addEventListener('change', () => updateApplyFileName());

  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (!file) return;
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
    updateApplyFileName();
  });
});

function updateApplyFileName() {
  const zone = document.getElementById('apply-drop-zone');
  const input = document.getElementById('apply-file');
  const nameEl = document.getElementById('apply-file-name');
  if (input.files && input.files[0]) {
    zone.classList.add('has-file');
    nameEl.textContent = '✓ ' + input.files[0].name;
  }
}

async function submitApplication() {
  const name = document.getElementById('apply-name').value.trim();
  const email = document.getElementById('apply-email').value.trim();
  const phone = document.getElementById('apply-phone').value.trim();
  const file = document.getElementById('apply-file').files[0];

  if (!name || !email) { toast('Please fill in your name and email'); return; }
  if (!file) { toast('Please attach your resume'); return; }

  const btn = document.getElementById('apply-submit-btn');
  btn.disabled = true;
  btn.textContent = 'Submitting…';

  try {
    const form = new FormData();
    form.append('jd_id', currentJobId());
    form.append('name', name);
    form.append('email', email);
    form.append('phone', phone);
    form.append('file', file);

    const res = await fetch('/api/public/apply', { method: 'POST', body: form });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }

    document.getElementById('apply-form-wrap').style.display = 'none';
    document.getElementById('apply-success').style.display = 'block';
    document.getElementById('apply-modal-footer').innerHTML =
      '<button class="btn btn-primary" onclick="location.href=\'/jobs\'">Back to Open Positions</button>';
  } catch (e) {
    toast(e.message);
    btn.disabled = false;
    btn.textContent = 'Submit Application';
  }
}
