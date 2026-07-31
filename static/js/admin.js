// ─── File upload helpers ─────────────────────────────────────────────────────
let _jdMode = 'file';
let _resumeMode = 'file';

function switchJDTab(mode, btn) {
  _jdMode = mode;
  document.querySelectorAll('#jd-modal .upload-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('jd-file-section').style.display = mode === 'file' ? 'block' : 'none';
  document.getElementById('jd-text-section').style.display = mode === 'text' ? 'block' : 'none';
}

function switchResumeTab(mode, btn) {
  _resumeMode = mode;
  document.querySelectorAll('#resume-modal .upload-tab').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('resume-file-section').style.display = mode === 'file' ? 'block' : 'none';
  document.getElementById('resume-text-section').style.display = mode === 'text' ? 'block' : 'none';
}

function onDragOver(e) {
  e.preventDefault();
  e.currentTarget.classList.add('dragover');
}
function onDragLeave(e, zoneId) {
  document.getElementById(zoneId).classList.remove('dragover');
}
function onDrop(e, inputId) {
  e.preventDefault();
  const zone = e.currentTarget;
  zone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (!file) return;
  const input = document.getElementById(inputId);
  const dt = new DataTransfer();
  dt.items.add(file);
  input.files = dt.files;
  const nameSpan = inputId === 'jd-file' ? 'jd-file-name' : 'resume-file-name';
  onFileSelect(input, zone.id, nameSpan);
}
function onFileSelect(input, zoneId, nameId) {
  const zone = document.getElementById(zoneId);
  const nameEl = document.getElementById(nameId);
  if (input.files && input.files[0]) {
    zone.classList.add('has-file');
    nameEl.textContent = '✓ ' + input.files[0].name;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  ['jd-drop-zone', 'resume-drop-zone'].forEach(zoneId => {
    const zone = document.getElementById(zoneId);
    if (!zone) return;
    zone.addEventListener('click', () => {
      const inputId = zoneId === 'jd-drop-zone' ? 'jd-file' : 'resume-file';
      document.getElementById(inputId).click();
    });
  });
});

// ─── Tab switching ────────────────────────────────────────────────────────────
const TAB_TITLES = {
  overview:     'Overview',
  jd:           'Job Descriptions',
  applications: 'Applications',
  screening:    'Screening',
  interview:    'Interview',
  decisions:    'Decisions',
};

const TAB_ACTIONS = {
  overview:     '',
  jd:           '<button class="btn btn-primary btn-sm" onclick="showModal(\'jd-modal\')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="margin-right:2px"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>New JD</button>',
  applications: '<button class="btn btn-primary btn-sm" onclick="showModal(\'resume-modal\')"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" style="margin-right:2px"><line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/><line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/></svg>Add Application</button>',
  screening:    '<button class="btn btn-secondary btn-sm" onclick="loadScreening()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="margin-right:2px"><polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Refresh</button>',
  interview:    '<button class="btn btn-secondary btn-sm" onclick="loadInterview()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="margin-right:2px"><polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Refresh</button>',
  decisions:    '<button class="btn btn-secondary btn-sm" onclick="loadDecisions()"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" style="margin-right:2px"><polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>Refresh</button>',
};

function switchTab(tab) {
  document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

  const btn = document.querySelector(`.nav-item[data-tab="${tab}"]`);
  const panel = document.getElementById('tab-' + tab);
  if (btn) btn.classList.add('active');
  if (panel) panel.classList.add('active');

  document.getElementById('page-title').textContent = TAB_TITLES[tab] || tab;
  document.getElementById('topbar-actions').innerHTML = TAB_ACTIONS[tab] || '';

  if (tab === 'applications') loadApplications();
  if (tab === 'screening')    loadScreening();
  if (tab === 'interview')    loadInterview();
  if (tab === 'decisions')    loadDecisions();
  if (tab === 'jd')           loadJDs();
  if (tab === 'overview')     loadOverview();
}

document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// ─── Modal helpers ────────────────────────────────────────────────────────────
function showModal(id) {
  document.getElementById(id).style.display = 'flex';
}
function hideModal(id) {
  document.getElementById(id).style.display = 'none';
}
document.querySelectorAll('.modal-overlay').forEach(el => {
  el.addEventListener('click', e => { if (e.target === el) el.style.display = 'none'; });
});

// ─── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, duration = 3500) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'flex';
  clearTimeout(t._timer);
  t._timer = setTimeout(() => { t.style.display = 'none'; }, duration);
}

// ─── API helpers ──────────────────────────────────────────────────────────────
async function api(method, path, body) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch('/api' + path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

// ─── Animate count ────────────────────────────────────────────────────────────
function animateCount(el, target) {
  if (!el) return;
  const start = 0;
  const duration = 600;
  const startTime = performance.now();
  function step(now) {
    const p = Math.min((now - startTime) / duration, 1);
    el.textContent = Math.round(start + (target - start) * easeOut(p));
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

// ─── Overview ─────────────────────────────────────────────────────────────────
async function loadOverview() {
  try {
    const [jds, candidates, pending] = await Promise.all([
      api('GET', '/jd'),
      api('GET', '/candidates'),
      api('GET', '/decisions/pending'),
    ]);

    animateCount(document.getElementById('stat-jd-count'), jds.length);
    animateCount(document.getElementById('stat-candidate-count'), candidates.length);

    const shortlisted = candidates.filter(c =>
      ['interview_scheduled','interview_in_progress','interview_complete','evaluated','selected'].includes(c.status)
    ).length;
    animateCount(document.getElementById('stat-shortlisted-count'), shortlisted);
    animateCount(document.getElementById('stat-pending-count'), pending.length);

    // Decisions badge
    const badge = document.getElementById('decisions-count');
    if (pending.length > 0) {
      badge.textContent = pending.length;
      badge.style.display = 'inline-flex';
    } else {
      badge.style.display = 'none';
    }

    // Recent JDs
    const overviewJDs = document.getElementById('overview-jds');
    const recentJDs = [...jds].reverse().slice(0, 5);
    if (!recentJDs.length) {
      overviewJDs.innerHTML = '<div class="overview-empty">No job descriptions yet</div>';
    } else {
      overviewJDs.innerHTML = recentJDs.map(j => `
        <div class="overview-row">
          <div class="overview-row-avatar">${esc(j.title.slice(0,2).toUpperCase())}</div>
          <div class="overview-row-info">
            <div class="overview-row-title">${esc(j.title)}</div>
            <div class="overview-row-sub">${new Date(j.created_at).toLocaleDateString()} &middot; ${j.parsed_json ? 'Parsed' : 'Parsing…'}</div>
          </div>
          ${j.parsed_json
            ? '<span class="badge badge-green" style="flex-shrink:0">Ready</span>'
            : '<span class="badge badge-yellow" style="flex-shrink:0">Parsing</span>'}
        </div>
      `).join('');
    }

    // Recent Candidates
    const overviewCandidates = document.getElementById('overview-candidates');
    const recentCandidates = [...candidates].reverse().slice(0, 5);
    if (!recentCandidates.length) {
      overviewCandidates.innerHTML = '<div class="overview-empty">No candidates yet</div>';
    } else {
      overviewCandidates.innerHTML = recentCandidates.map(c => `
        <div class="overview-row">
          <div class="overview-row-avatar">${esc(initials(c.name))}</div>
          <div class="overview-row-info">
            <div class="overview-row-title">${esc(c.name)}</div>
            <div class="overview-row-sub">${esc(c.email)}</div>
          </div>
          ${statusBadge(c.status)}
        </div>
      `).join('');
    }

  } catch(e) {
    console.error('Overview error:', e);
  }
}

// ─── Delete helpers ────────────────────────────────────────────────────────────
async function deleteJD(id, title) {
  if (!confirm(`Delete "${title}"?\n\nThis will also delete ALL candidates and their interview data. This cannot be undone.`)) return;
  try {
    await api('DELETE', `/jd/${id}`);
    toast('Job description deleted');
    loadJDs();
    loadOverview();
  } catch (e) { toast('Error: ' + e.message); }
}

async function togglePublish(id, isPublished) {
  try {
    await api('POST', `/jd/${id}/publish`, { published: !isPublished });
    toast(!isPublished ? 'Job published to the careers page' : 'Job unpublished');
    loadJDs();
  } catch (e) { toast('Error: ' + e.message); }
}

async function deleteCandidate(id, name) {
  if (!confirm(`Delete candidate "${name}"?\n\nThis will also delete their interview sessions, evaluations, and decisions.`)) return;
  try {
    await api('DELETE', `/candidates/${id}`);
    toast('Candidate deleted');
    reloadActiveCandidateTab();
    loadOverview();
  } catch (e) { toast('Error: ' + e.message); }
}

function reloadActiveCandidateTab() {
  const activeTab = document.querySelector('.nav-item.active')?.dataset.tab;
  if (activeTab === 'applications') loadApplications();
  if (activeTab === 'screening')    loadScreening();
  if (activeTab === 'interview')    loadInterview();
}

// ─── JD ───────────────────────────────────────────────────────────────────────
async function loadJDs() {
  const list = document.getElementById('jd-list');
  list.innerHTML = '<p class="loading">Loading…</p>';
  try {
    const jds = await api('GET', '/jd');
    const filters = [
      document.getElementById('applications-jd-filter'),
      document.getElementById('screening-jd-filter'),
      document.getElementById('interview-jd-filter'),
    ];
    const resumeSelect = document.getElementById('resume-jd-id');

    [...filters, resumeSelect].forEach(sel => {
      if (!sel) return;
      const curVal = sel.value;
      sel.innerHTML = sel === resumeSelect
        ? '<option value="">Select a job description…</option>'
        : '<option value="">All Job Descriptions</option>';
      jds.forEach(j => {
        const o = document.createElement('option');
        o.value = j.id; o.textContent = j.title;
        sel.appendChild(o);
      });
      if (curVal) sel.value = curVal;
    });

    if (!jds.length) {
      list.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="7" width="20" height="14" rx="2" stroke="currentColor" stroke-width="1.75"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" stroke="currentColor" stroke-width="1.75"/></svg>
          </div>
          <h4>No job descriptions yet</h4>
          <p>Create your first job description to start the hiring process</p>
          <button class="btn btn-primary btn-sm" style="margin-top:4px" onclick="showModal('jd-modal')">+ New JD</button>
        </div>`;
      return;
    }

    list.innerHTML = jds.map((j, i) => `
      <div class="card" style="--delay:${i * 55}ms">
        <div class="card-icon">
          <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="7" width="20" height="14" rx="2" stroke="currentColor" stroke-width="1.75"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" stroke="currentColor" stroke-width="1.75"/></svg>
        </div>
        <h4>${esc(j.title)}</h4>
        <div class="card-meta">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          ID: ${j.id.slice(0,8)}…
        </div>
        <div class="card-meta">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><rect x="3" y="4" width="18" height="18" rx="2" stroke="currentColor" stroke-width="2"/><line x1="16" y1="2" x2="16" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="8" y1="2" x2="8" y2="6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><line x1="3" y1="10" x2="21" y2="10" stroke="currentColor" stroke-width="2"/></svg>
          ${new Date(j.created_at).toLocaleDateString('en-US', {month:'short',day:'numeric',year:'numeric'})}
        </div>
        <span class="card-parsed ${j.parsed_json ? 'done' : 'pending'}">
          ${j.parsed_json ? '✓ Parsed' : '⏳ Parsing…'}
        </span>
        <span class="badge ${j.is_published ? 'badge-green' : 'badge-gray'}" style="margin-left:8px">
          ${j.is_published ? 'Published' : 'Draft'}
        </span>
        <div class="card-actions">
          <button class="btn btn-secondary btn-sm" onclick="viewJD('${j.id}')">View</button>
          <button class="btn ${j.is_published ? 'btn-ghost' : 'btn-success'} btn-sm" onclick="togglePublish('${j.id}', ${j.is_published ? 'true' : 'false'})">${j.is_published ? 'Unpublish' : 'Publish'}</button>
          <button class="btn btn-danger btn-sm" onclick="deleteJD('${j.id}','${esc(j.title)}')">Delete</button>
        </div>
      </div>
    `).join('');
  } catch (e) {
    list.innerHTML = `<p style="color:var(--red);padding:12px">${e.message}</p>`;
  }
}

async function viewJD(id) {
  try {
    const j = await api('GET', `/jd/${id}`);
    const parsed = j.parsed_json ? JSON.parse(j.parsed_json) : null;
    document.getElementById('detail-title').textContent = j.title;
    document.getElementById('detail-body').innerHTML = `
      <div class="detail-section">
        <h4>Raw Description</h4>
        <pre style="white-space:pre-wrap;font-size:0.8rem;color:var(--t2);max-height:200px;overflow-y:auto;background:var(--surf-1);padding:12px;border-radius:8px;border:1px solid var(--border)">${esc(j.raw_text)}</pre>
      </div>
      ${parsed ? `
      <div class="detail-section">
        <h4>Parsed Requirements</h4>
        <div class="detail-info-grid" style="margin-bottom:12px">
          <div class="info-item"><div class="info-label">Seniority</div><div class="info-val">${esc(parsed.seniority_level || '—')}</div></div>
          <div class="info-item"><div class="info-label">Experience</div><div class="info-val">${parsed.experience_years || 0}+ years</div></div>
        </div>
        <p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--t3);margin-bottom:8px">Required Skills</p>
        <div class="tags">${(parsed.required_skills||[]).map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div>
      </div>` : '<div class="detail-section"><p style="color:var(--t3)">Still parsing…</p></div>'}
    `;
    showModal('detail-modal');
  } catch (e) { toast(e.message); }
}

async function submitJD() {
  const title = document.getElementById('jd-title').value.trim();
  if (!title) { toast('Please enter a job title'); return; }
  try {
    if (_jdMode === 'file') {
      const file = document.getElementById('jd-file').files[0];
      if (!file) { toast('Please select a file'); return; }
      const form = new FormData();
      form.append('title', title);
      form.append('file', file);
      const res = await fetch('/api/jd/upload', { method: 'POST', body: form });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    } else {
      const text = document.getElementById('jd-text').value.trim();
      if (!text) { toast('Please paste the job description text'); return; }
      await api('POST', '/jd', { title, raw_text: text });
    }
    hideModal('jd-modal');
    document.getElementById('jd-title').value = '';
    document.getElementById('jd-file').value = '';
    document.getElementById('jd-file-name').textContent = 'Drag & drop or browse';
    document.getElementById('jd-drop-zone').classList.remove('has-file');
    toast('Job description submitted — AI is parsing it');
    loadJDs();
    loadOverview();
  } catch (e) { toast(e.message); }
}

// ─── Applications ─────────────────────────────────────────────────────────────
const APPLICATION_STATUSES = ['pending'];
const SCREENING_STATUSES   = ['screening', 'shortlisted', 'rejected_screening'];
const INTERVIEW_STATUSES   = ['interview_scheduled', 'interview_in_progress', 'interview_complete', 'evaluated'];

let selectedApplicationIds = new Set();

async function loadApplications() {
  const jdId = document.getElementById('applications-jd-filter').value;
  const body = document.getElementById('applications-body');
  body.innerHTML = '<tr><td colspan="6" class="loading">Loading applications…</td></tr>';
  selectedApplicationIds = new Set();
  updateSendToScreeningButton();
  document.getElementById('applications-select-all').checked = false;
  try {
    const path = jdId ? `/candidates?jd_id=${jdId}` : '/candidates';
    const all = await api('GET', path);
    const rows = all.filter(c => APPLICATION_STATUSES.includes(c.status));
    if (!rows.length) {
      body.innerHTML = `
        <tr><td colspan="6">
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg viewBox="0 0 24 24" fill="none"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="1.75"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="1.75"/></svg>
            </div>
            <h4>No applications yet</h4>
            <p>Candidates who apply via the public jobs page will show up here</p>
            <button class="btn btn-primary btn-sm" style="margin-top:4px" onclick="showModal('resume-modal')">Add Application</button>
          </div>
        </td></tr>`;
      return;
    }
    body.innerHTML = rows.map((c, i) => `
      <tr style="animation:cardIn .35s ease both;animation-delay:${i*40}ms">
        <td><input type="checkbox" class="application-row-check" data-id="${c.id}" onchange="toggleApplicationRow('${c.id}', this.checked)" /></td>
        <td>
          <div class="candidate-cell">
            <div class="candidate-avatar">${esc(initials(c.name))}</div>
            <div>
              <div class="candidate-name">${esc(c.name)}</div>
              <div class="candidate-email">${esc(c.email)}</div>
            </div>
          </div>
        </td>
        <td style="color:var(--t2);font-size:0.82rem">${c.jd_id.slice(0,8)}…</td>
        <td style="color:var(--t2);font-size:0.82rem">${esc(c.phone || '—')}</td>
        <td style="color:var(--t2);font-size:0.82rem">${new Date(c.created_at).toLocaleDateString()}</td>
        <td>
          <div style="display:flex;gap:6px">
            <button class="btn btn-secondary btn-sm" onclick="viewCandidate('${c.id}')">Details</button>
            <button class="btn btn-danger btn-sm" onclick="deleteCandidate('${c.id}','${esc(c.name)}')">Delete</button>
          </div>
        </td>
      </tr>`).join('');
  } catch (e) {
    body.innerHTML = `<tr><td colspan="6" style="color:var(--red);padding:12px">${e.message}</td></tr>`;
  }
}

function toggleApplicationRow(id, checked) {
  if (checked) selectedApplicationIds.add(id);
  else selectedApplicationIds.delete(id);
  updateSendToScreeningButton();
}

function toggleSelectAllApplications(checkbox) {
  document.querySelectorAll('.application-row-check').forEach(cb => {
    cb.checked = checkbox.checked;
    if (checkbox.checked) selectedApplicationIds.add(cb.dataset.id);
    else selectedApplicationIds.delete(cb.dataset.id);
  });
  updateSendToScreeningButton();
}

function updateSendToScreeningButton() {
  const btn = document.getElementById('send-to-screening-btn');
  const count = document.getElementById('send-to-screening-count');
  count.textContent = selectedApplicationIds.size;
  btn.style.display = selectedApplicationIds.size > 0 ? 'inline-flex' : 'none';
}

async function sendToScreening() {
  const ids = Array.from(selectedApplicationIds);
  if (!ids.length) return;
  try {
    const res = await api('POST', '/candidates/screen', { candidate_ids: ids });
    toast(res.message || 'Sent to screening');
    loadApplications();
    loadOverview();
  } catch (e) { toast(e.message); }
}

// ─── Screening ────────────────────────────────────────────────────────────────
async function loadScreening() {
  const jdId = document.getElementById('screening-jd-filter').value;
  const body = document.getElementById('screening-body');
  body.innerHTML = '<tr><td colspan="5" class="loading">Loading screening results…</td></tr>';
  try {
    const path = jdId ? `/candidates?jd_id=${jdId}` : '/candidates';
    const all = await api('GET', path);
    const rows = all.filter(c => SCREENING_STATUSES.includes(c.status));
    if (!rows.length) {
      body.innerHTML = `
        <tr><td colspan="5">
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="1.75"/><line x1="21" y1="21" x2="16.65" y2="16.65" stroke="currentColor" stroke-width="1.75" stroke-linecap="round"/></svg>
            </div>
            <h4>No candidates in screening</h4>
            <p>Send applications to screening from the Applications tab</p>
          </div>
        </td></tr>`;
      return;
    }
    body.innerHTML = rows.map((c, i) => {
      const score = c.screening_score;
      const scoreCls = score == null ? 'none' : score >= 70 ? 'high' : score >= 50 ? 'mid' : 'low';
      const scoreStr = score != null ? score.toFixed(1) : '—';
      const inviteBtn = c.status === 'screening'
        ? `<span class="badge badge-yellow">Screening…</span>`
        : `<button class="btn btn-primary btn-sm" onclick="sendInterviewInvite('${c.id}')">Send Interview Invite</button>`;
      return `
        <tr style="animation:cardIn .35s ease both;animation-delay:${i*40}ms">
          <td>
            <div class="candidate-cell">
              <div class="candidate-avatar">${esc(initials(c.name))}</div>
              <div>
                <div class="candidate-name">${esc(c.name)}</div>
                <div class="candidate-email">${esc(c.email)}</div>
              </div>
            </div>
          </td>
          <td style="color:var(--t2);font-size:0.82rem">${c.jd_id.slice(0,8)}…</td>
          <td><span class="score-pill ${scoreCls}">${scoreStr}</span></td>
          <td>${statusBadge(c.status)}</td>
          <td>
            <div style="display:flex;gap:6px">
              <button class="btn btn-secondary btn-sm" onclick="viewCandidate('${c.id}')">Details</button>
              ${inviteBtn}
            </div>
          </td>
        </tr>`;
    }).join('');
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" style="color:var(--red);padding:12px">${e.message}</td></tr>`;
  }
}

async function sendInterviewInvite(id) {
  try {
    const res = await api('POST', `/candidates/${id}/schedule`, {});
    toast(res.message || 'Interview invite sent');
    loadScreening();
    loadInterview();
    loadOverview();
  } catch (e) { toast(e.message); }
}

// ─── Interview ────────────────────────────────────────────────────────────────
async function loadInterview() {
  const jdId = document.getElementById('interview-jd-filter').value;
  const body = document.getElementById('interview-body');
  body.innerHTML = '<tr><td colspan="4" class="loading">Loading interviews…</td></tr>';
  try {
    const path = jdId ? `/candidates?jd_id=${jdId}` : '/candidates';
    const all = await api('GET', path);
    const rows = all.filter(c => INTERVIEW_STATUSES.includes(c.status));
    if (!rows.length) {
      body.innerHTML = `
        <tr><td colspan="4">
          <div class="empty-state">
            <div class="empty-state-icon">
              <svg viewBox="0 0 24 24" fill="none"><rect x="2" y="4" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.75"/><path d="M17 9l5-3v12l-5-3" stroke="currentColor" stroke-width="1.75" stroke-linejoin="round"/></svg>
            </div>
            <h4>No interviews yet</h4>
            <p>Send an interview invite from the Screening tab</p>
          </div>
        </td></tr>`;
      return;
    }
    body.innerHTML = rows.map((c, i) => {
      const complete = ['interview_complete', 'evaluated'].includes(c.status);
      const stageBadge = complete
        ? `<span class="badge badge-green">Complete</span>`
        : `<span class="badge badge-yellow">Pending</span>`;
      return `
        <tr style="animation:cardIn .35s ease both;animation-delay:${i*40}ms">
          <td>
            <div class="candidate-cell">
              <div class="candidate-avatar">${esc(initials(c.name))}</div>
              <div>
                <div class="candidate-name">${esc(c.name)}</div>
                <div class="candidate-email">${esc(c.email)}</div>
              </div>
            </div>
          </td>
          <td style="color:var(--t2);font-size:0.82rem">${c.jd_id.slice(0,8)}…</td>
          <td>${stageBadge}</td>
          <td>
            <div style="display:flex;gap:6px">
              <button class="btn btn-secondary btn-sm" onclick="viewCandidate('${c.id}')">Details</button>
            </div>
          </td>
        </tr>`;
    }).join('');
  } catch (e) {
    body.innerHTML = `<tr><td colspan="4" style="color:var(--red);padding:12px">${e.message}</td></tr>`;
  }
}

async function viewCandidate(id) {
  try {
    const c = await api('GET', `/candidates/${id}`);
    const screening = c.screening_json ? JSON.parse(c.screening_json) : null;
    const ev = c.evaluation ? (typeof c.evaluation.result_json === 'string' ? JSON.parse(c.evaluation.result_json) : c.evaluation) : null;
    const dec = c.decision;

    document.getElementById('detail-title').textContent = c.name;
    document.getElementById('detail-body').innerHTML = `
      <div class="detail-section">
        <h4>Profile</h4>
        <div class="detail-info-grid">
          <div class="info-item"><div class="info-label">Email</div><div class="info-val">${esc(c.email)}</div></div>
          <div class="info-item"><div class="info-label">Status</div><div class="info-val">${statusBadge(c.status)}</div></div>
          ${c.meeting_token ? `<div class="info-item" style="grid-column:1/-1"><div class="info-label">Interview Link</div><div class="info-val"><a href="/interview/${c.meeting_token}" target="_blank" style="color:var(--accent)">Open Interview Room ↗</a></div></div>` : ''}
        </div>
      </div>
      ${screening ? `
      <div class="detail-section">
        <h4>Screening Results — ${screening.overall_score?.toFixed(1)}/100</h4>
        ${scoreRow('Overall', screening.overall_score)}
        ${scoreRow('Skill Match', screening.skill_match_score)}
        ${scoreRow('Experience', screening.experience_score)}
        ${screening.strengths?.length ? `<p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin:12px 0 6px">Strengths</p><div class="tags">${screening.strengths.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div>` : ''}
        ${screening.gaps?.length ? `<p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin:12px 0 6px">Gaps</p><div class="tags">${screening.gaps.map(g=>`<span class="tag tag-red">${esc(g)}</span>`).join('')}</div>` : ''}
      </div>` : ''}
      ${ev ? `
      <div class="detail-section">
        <h4>Interview Evaluation — ${ev.overall_score?.toFixed(1)}/100</h4>
        <p style="margin-bottom:12px">Recommendation: <strong style="color:var(--accent)">${ev.recommendation}</strong></p>
        ${dimensionRow('Technical', ev.technical_competency?.score)}
        ${dimensionRow('Communication', ev.communication?.score)}
        ${dimensionRow('Problem Solving', ev.problem_solving?.score)}
        ${dimensionRow('Cultural Fit', ev.cultural_fit?.score)}
        ${ev.key_strengths?.length ? `<p style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--t3);margin:12px 0 6px">Key Strengths</p><div class="tags">${ev.key_strengths.map(s=>`<span class="tag">${esc(s)}</span>`).join('')}</div>` : ''}
        ${ev.detailed_feedback ? `<p style="margin-top:12px;font-size:0.84rem;color:var(--t2);line-height:1.6;padding:12px;background:var(--surf-1);border-radius:8px;border:1px solid var(--border)">${esc(ev.detailed_feedback)}</p>` : ''}
      </div>` : ''}
      ${dec ? `
      <div class="detail-section">
        <h4>AI Decision</h4>
        <p style="margin-bottom:6px">Recommendation: <strong style="color:var(--accent)">${dec.ai_recommendation}</strong> &nbsp;·&nbsp; Confidence: <strong>${((dec.confidence_score||0)*100).toFixed(0)}%</strong></p>
        <p style="font-size:0.83rem;color:var(--t2);margin-bottom:14px;line-height:1.6">${esc(dec.reasoning||'')}</p>
        ${!dec.admin_decision ? `
        <div class="admin-decision-box">
          <textarea id="admin-notes-${dec.id}" placeholder="Admin notes (optional)…" rows="2" class="decision-notes"></textarea>
          <div style="display:flex;gap:8px">
            <button class="btn btn-success btn-sm" onclick="decide('${dec.id}','selected')">✓ Select</button>
            <button class="btn btn-danger btn-sm" onclick="decide('${dec.id}','rejected')">✕ Reject</button>
          </div>
        </div>` : `<p>Admin Decision: <strong style="color:var(--t1)">${dec.admin_decision}</strong></p>`}
      </div>` : ''}
    `;
    showModal('detail-modal');
  } catch (e) { toast(e.message); }
}

async function decide(decisionId, outcome) {
  const notes = document.getElementById(`admin-notes-${decisionId}`)?.value || '';
  try {
    await api('POST', `/decisions/${decisionId}`, { decision: outcome, notes });
    hideModal('detail-modal');
    toast(`Candidate ${outcome} — email sent`);
    reloadActiveCandidateTab();
    loadDecisions();
    loadOverview();
  } catch (e) { toast(e.message); }
}

async function submitResume() {
  const jd_id = document.getElementById('resume-jd-id').value;
  const name = document.getElementById('resume-name').value.trim();
  const email = document.getElementById('resume-email').value.trim();
  const phone = document.getElementById('resume-phone').value.trim();
  if (!jd_id || !name || !email) { toast('Please fill in all fields'); return; }
  try {
    if (_resumeMode === 'file') {
      const file = document.getElementById('resume-file').files[0];
      if (!file) { toast('Please select a resume file'); return; }
      const form = new FormData();
      form.append('jd_id', jd_id);
      form.append('candidate_name', name);
      form.append('candidate_email', email);
      form.append('phone', phone);
      form.append('file', file);
      const res = await fetch('/api/resume/upload', { method: 'POST', body: form });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
    } else {
      const resume_text = document.getElementById('resume-text').value.trim();
      if (!resume_text) { toast('Please paste the resume text'); return; }
      await api('POST', '/resume', { jd_id, candidate_name: name, candidate_email: email, resume_text, phone });
    }
    hideModal('resume-modal');
    document.getElementById('resume-name').value = '';
    document.getElementById('resume-email').value = '';
    document.getElementById('resume-phone').value = '';
    document.getElementById('resume-file').value = '';
    document.getElementById('resume-file-name').textContent = 'Drag & drop or browse';
    document.getElementById('resume-drop-zone').classList.remove('has-file');
    toast('Application added — send to screening when ready');
    loadApplications();
    loadOverview();
  } catch (e) { toast(e.message); }
}

// ─── Decisions ────────────────────────────────────────────────────────────────
async function loadDecisions() {
  const list = document.getElementById('decisions-list');
  list.innerHTML = '<p class="loading">Loading…</p>';
  try {
    const decisions = await api('GET', '/decisions/pending');
    if (!decisions.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">
            <svg viewBox="0 0 24 24" fill="none"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="1.75"/><polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <h4>No pending decisions</h4>
          <p>All candidates have been reviewed</p>
        </div>`;
      return;
    }
    list.innerHTML = decisions.map((d, i) => `
      <div class="decision-card" style="--delay:${i*60}ms">
        <div class="decision-card-header">
          <h4>Candidate ${d.candidate_id.slice(0,8)}…</h4>
          <span class="badge ${d.ai_recommendation === 'hire' ? 'badge-green' : d.ai_recommendation === 'reject' ? 'badge-red' : 'badge-yellow'}">
            AI: ${d.ai_recommendation}
          </span>
        </div>
        <div class="decision-meta">
          <span>Confidence: <strong>${((d.confidence_score||0)*100).toFixed(0)}%</strong></span>
          <span>Created: <strong>${new Date(d.created_at).toLocaleString()}</strong></span>
        </div>
        <div class="decision-reasoning">${esc((d.reasoning||'').slice(0,320))}${(d.reasoning||'').length > 320 ? '…' : ''}</div>
        <textarea id="dnotes-${d.id}" placeholder="Admin notes (optional)…" rows="2" class="decision-notes"></textarea>
        <div class="decision-actions">
          <button class="btn btn-success btn-sm" onclick="quickDecide('${d.id}','selected')">✓ Select Candidate</button>
          <button class="btn btn-danger btn-sm" onclick="quickDecide('${d.id}','rejected')">✕ Reject Candidate</button>
        </div>
      </div>
    `).join('');

    // Update badge
    const badge = document.getElementById('decisions-count');
    badge.textContent = decisions.length;
    badge.style.display = 'inline-flex';
  } catch (e) {
    list.innerHTML = `<p style="color:var(--red);padding:12px">${e.message}</p>`;
  }
}

async function quickDecide(decisionId, outcome) {
  const notes = document.getElementById(`dnotes-${decisionId}`)?.value || '';
  try {
    await api('POST', `/decisions/${decisionId}`, { decision: outcome, notes });
    toast(`Decision recorded — ${outcome} email sent`);
    loadDecisions();
    loadOverview();
  } catch (e) { toast(e.message); }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function initials(name) {
  const parts = String(name || '').trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return String(name || '?').slice(0,2).toUpperCase();
}

function statusBadge(status) {
  const map = {
    pending:              'gray',
    screening:            'yellow',
    shortlisted:          'blue',
    rejected_screening:   'red',
    interview_scheduled:  'blue',
    interview_in_progress:'yellow',
    interview_complete:   'blue',
    evaluated:            'blue',
    selected:             'green',
    rejected_final:       'red',
    email_sent:           'green',
  };
  const cls = map[status] || 'gray';
  return `<span class="badge badge-${cls}">${(status||'').replace(/_/g,' ')}</span>`;
}

function scoreRow(label, score) {
  const pct = Math.max(0, Math.min(100, score || 0));
  const color = pct >= 70 ? 'var(--green)' : pct >= 50 ? 'var(--yellow)' : 'var(--red)';
  return `<div class="score-row">
    <span class="score-label">${esc(label)}</span>
    <div class="score-bar-wrap"><div class="score-bar" style="width:${pct}%;background:${color}"></div></div>
    <span class="score-num">${pct.toFixed(0)}</span>
  </div>`;
}

function dimensionRow(label, score) {
  const pct = Math.max(0, Math.min(10, score || 0)) * 10;
  const color = pct >= 70 ? 'var(--green)' : pct >= 50 ? 'var(--yellow)' : 'var(--red)';
  return `<div class="score-row">
    <span class="score-label">${esc(label)}</span>
    <div class="score-bar-wrap"><div class="score-bar" style="width:${pct}%;background:${color}"></div></div>
    <span class="score-num">${(score||0).toFixed(1)}</span>
  </div>`;
}

// ─── Init ─────────────────────────────────────────────────────────────────────
// Set default topbar action for overview
document.getElementById('topbar-actions').innerHTML = TAB_ACTIONS['overview'] || '';

loadOverview();
loadJDs();

setInterval(() => {
  const activeTab = document.querySelector('.nav-item.active')?.dataset.tab;
  if (activeTab === 'overview' || activeTab === 'jd') loadJDs();
  if (activeTab === 'overview')  loadOverview();
  if (activeTab === 'screening') loadScreening();
  if (activeTab === 'interview') loadInterview();
}, 12000);
