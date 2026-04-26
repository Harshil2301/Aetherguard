// popup.js — AetherGuard Extension Popup Logic

// ── Status Check ─────────────────────────────────────────────────────────────
const statusDot  = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

async function checkStatus() {
  try {
    const res = await fetch('http://127.0.0.1:5000/api/status', {
      headers: { 'Authorization': 'Bearer admin_mock_token_123' }
    });
    if (res.ok) {
      statusDot.className  = 'status-dot online';
      statusText.className = 'status-text online';
      statusText.textContent = 'NODE ONLINE — Port 5000';
    } else {
      throw new Error();
    }
  } catch (_) {
    statusDot.className  = 'status-dot offline';
    statusText.className = 'status-text offline';
    statusText.textContent = 'OFFLINE — Start python app.py';
  }
}
checkStatus();

// ── Last Scan Display ─────────────────────────────────────────────────────────
const lastScanEl = document.getElementById('lastScan');

function renderLastScan(scan) {
  if (!scan) {
    lastScanEl.innerHTML = '<div class="no-scan">No scan yet — open an email in Gmail</div>';
    return;
  }
  const score = scan.score ?? 0;
  const color = score > 60 ? '#ef4444' : score > 30 ? '#f59e0b' : '#10b981';
  const barW  = Math.min(score, 100);
  const time  = scan.time ? new Date(scan.time).toLocaleTimeString() : '';

  lastScanEl.innerHTML = `
    <div class="scan-verdict" style="color:${color}">${scan.label || 'UNKNOWN'}</div>
    <div class="scan-score-row">
      <span class="scan-score-label">Risk Score</span>
      <span class="scan-score-val" style="color:${color}">${score}<span style="font-size:11px;color:#374151">/100</span></span>
    </div>
    <div class="scan-bar-track">
      <div class="scan-bar" style="width:${barW}%;background:${color};box-shadow:0 0 8px ${color}60"></div>
    </div>
    ${scan.reason ? `<div class="scan-reason">${scan.reason}</div>` : ''}
    <div class="scan-time">${time}</div>
  `;
}

chrome.storage.local.get('last_scan', ({ last_scan }) => renderLastScan(last_scan));

// Live refresh when popup is open (poll every 3s)
setInterval(() => {
  chrome.storage.local.get('last_scan', ({ last_scan }) => renderLastScan(last_scan));
}, 3000);

// ── Token Save ───────────────────────────────────────────────────────────────
const tokenInput  = document.getElementById('tokenInput');
const saveBtn     = document.getElementById('saveToken');
const tokenSaved  = document.getElementById('tokenSaved');

// Pre-fill saved token
chrome.storage.local.get('aether_token', ({ aether_token }) => {
  if (aether_token) tokenInput.value = aether_token;
});

saveBtn.addEventListener('click', () => {
  const token = tokenInput.value.trim();
  if (!token) return;
  chrome.storage.local.set({ aether_token: token }, () => {
    tokenSaved.style.display = 'block';
    setTimeout(() => { tokenSaved.style.display = 'none'; }, 3000);
  });
});
