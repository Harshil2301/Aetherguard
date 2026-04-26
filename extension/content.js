/**
 * AetherGuard Gmail Content Script v3.0
 * ─────────────────────────────────────
 * Real-time email scanning with full result display,
 * auth token forwarding (Telemetry Node integration),
 * link neutering on high-risk emails.
 */

const API_BASE   = 'http://127.0.0.1:5000/api';
const BADGE_ID   = 'aetherguard-gmail-badge';
const DEBOUNCE_MS = 1500;

let lastScannedText = '';
let scanTimeout     = null;
let currentBadgeTimer = null;

// ── Token helper: read from localStorage so scans link to logged-in user ──
function getToken() {
  try {
    // localStorage is partitioned per origin — extension can't read gmail's localStorage.
    // We store the token in chrome.storage.local from the popup or from a background message.
    // For now, return empty string (unauthenticated scan). Token wiring done via popup auth.
    return '';
  } catch (e) { return ''; }
}

// ── Badge rendering ──────────────────────────────────────────────────────────
function removeBadge() {
  clearTimeout(currentBadgeTimer);
  const existing = document.getElementById(BADGE_ID);
  if (existing) {
    existing.style.opacity = '0';
    existing.style.transform = 'translateY(16px)';
    setTimeout(() => existing.remove(), 300);
  }
}

function showScanning() {
  removeBadge();
  const badge = document.createElement('div');
  badge.id = BADGE_ID;
  badge.innerHTML = `
    <button class="ag-close" title="Dismiss">×</button>
    <div class="ag-header"><span class="ag-dot"></span> AETHERGUARD SCAN</div>
    <div class="ag-scanning-row">
      <div class="ag-pulse"></div>
      <span class="ag-scanning-text">Analyzing email…</span>
    </div>
    <div class="ag-progress-track"><div class="ag-progress-bar ag-animate"></div></div>
  `;
  badge.querySelector('.ag-close').addEventListener('click', removeBadge);
  document.body.appendChild(badge);
}

function showResult(score, topReason, isSafe) {
  removeBadge();

  const HIGH   = score > 60;
  const MEDIUM = score > 30;
  const color  = HIGH   ? '#ef4444'
               : MEDIUM ? '#f59e0b'
               :           '#10b981';
  const icon   = HIGH   ? '⚠'  : MEDIUM ? '⚡' : '✓';
  const label  = HIGH   ? 'HIGH RISK — Likely Phishing'
               : MEDIUM ? 'SUSPICIOUS — Proceed Carefully'
               :           'SAFE — No Threats Detected';

  const badge = document.createElement('div');
  badge.id = BADGE_ID;
  badge.style.borderColor = `${color}40`;
  badge.style.boxShadow = `0 8px 32px rgba(0,0,0,0.7), 0 0 24px ${color}18`;

  const barWidth = Math.min(score, 100);
  badge.innerHTML = `
    <button class="ag-close" title="Dismiss">×</button>
    <div class="ag-header"><span class="ag-dot" style="background:${color};box-shadow:0 0 8px ${color}"></span> AETHERGUARD SCAN</div>
    <div class="ag-verdict" style="color:${color}">${icon} ${label}</div>
    <div class="ag-score-row">
      <span class="ag-score-label">Risk Score</span>
      <span class="ag-score-value" style="color:${color}">${score}<span class="ag-score-denom">/100</span></span>
    </div>
    <div class="ag-progress-track">
      <div class="ag-progress-bar" style="width:${barWidth}%;background:${color};box-shadow:0 0 8px ${color}60"></div>
    </div>
    ${topReason ? `<div class="ag-reason">${topReason}</div>` : ''}
    <a class="ag-link" href="http://localhost:5173/dashboard" target="_blank">Open Dashboard →</a>
  `;

  badge.querySelector('.ag-close').addEventListener('click', removeBadge);
  document.body.appendChild(badge);

  // Auto-dismiss safe emails after 8s; keep threats visible until dismissed
  if (!HIGH && !MEDIUM) {
    currentBadgeTimer = setTimeout(removeBadge, 8000);
  }
}

// ── Core scan function ───────────────────────────────────────────────────────
async function scanEmailText(emailText) {
  if (!emailText || emailText.trim().length < 30) return;
  if (emailText.trim() === lastScannedText.trim()) return;
  lastScannedText = emailText.trim();

  showScanning();

  try {
    // Use FormData (multipart) — matches what the Flask /api/scan endpoint expects
    const formData = new FormData();
    formData.append('text', emailText.substring(0, 4000));

    // Try to grab auth token from chrome.storage
    let token = '';
    try {
      const stored = await chrome.storage.local.get('aether_token');
      token = stored.aether_token || '';
    } catch (_) {}

    const headers = { 'X-Scan-Source': 'Gmail Extension' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/scan`, {
      method: 'POST',
      body: formData,
      headers,
    });

    if (!res.ok) {
      console.warn(`[AetherGuard] Backend returned HTTP ${res.status}`);
      showResult(0, `Server Error (HTTP ${res.status}). Ensure backend is running.`, true);
      return;
    }

    const data = await res.json();
    const score = data.final_risk_score ?? 0;

    // Top flagged reason from breakdown
    const topReason = data.risk_breakdown?.[0]?.detail || '';

    showResult(score, topReason);

    // Neuter links + images on high-risk emails
    if (score > 60) {
      neuterEmail();
    }

    // Store result for popup display
    try {
      chrome.storage.local.set({
        last_scan: {
          score,
          label: score > 60 ? 'HIGH RISK' : score > 30 ? 'SUSPICIOUS' : 'SAFE',
          reason: topReason,
          time: new Date().toISOString(),
        }
      });
    } catch (_) {}

  } catch (err) {
    console.warn('[AetherGuard] Scan failed:', err.message || err);
    showResult(0, 'Connection failed. Is python app.py running on Port 5000?', true);
  }
}

// ── Neuter malicious email content ──────────────────────────────────────────
function neuterEmail() {
  const emailBody = document.querySelector('.a3s.aiL');
  if (!emailBody) return;

  const links = emailBody.querySelectorAll('a[href]');
  links.forEach(link => {
    link.dataset.originalHref = link.href;
    link.removeAttribute('href');
    link.style.pointerEvents = 'none';
    link.style.color = '#ef4444';
    link.style.textDecoration = 'line-through';
    link.title = '⚠ AetherGuard: Link disabled — phishing risk detected';
  });

  const images = emailBody.querySelectorAll('img[src]');
  images.forEach(img => {
    img.dataset.originalSrc = img.src;
    img.src = '';
    img.style.display = 'none';
  });

  console.log(`[AetherGuard] Neutered ${links.length} links, ${images.length} images.`);
}

// ── Debounce ─────────────────────────────────────────────────────────────────
const debouncedScan = (text) => {
  clearTimeout(scanTimeout);
  scanTimeout = setTimeout(() => scanEmailText(text), DEBOUNCE_MS);
};

// ── DOM Observer: watch Gmail for email body ─────────────────────────────────
const observer = new MutationObserver(() => {
  const emailBody = document.querySelector('.a3s.aiL');
  if (!emailBody) return;
  const text = emailBody.innerText || emailBody.textContent || '';
  if (text.length > 30) debouncedScan(text);
});

function init() {
  observer.observe(document.body, { childList: true, subtree: true });
  console.log('[AetherGuard] Gmail real-time scanner active.');
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
