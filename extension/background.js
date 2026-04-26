/**
 * AetherGuard Background Service Worker v3.0
 * ─────────────────────────────────────────────
 * Handles right-click context menu scans
 * and stores last scan result for popup display.
 */

const API_URL = 'http://127.0.0.1:5000/api/scan';

// ── Context Menu Setup ───────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'aetherguard-scan-selection',
    title: '🛡 Scan with AetherGuard',
    contexts: ['selection', 'link']
  });
});

// ── Context Menu Click Handler ───────────────────────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId !== 'aetherguard-scan-selection') return;

  let payload = info.linkUrl;

  if (!payload) {
    try {
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          const sel = window.getSelection();
          if (!sel.rangeCount) return '';
          const div = document.createElement('div');
          div.appendChild(sel.getRangeAt(0).cloneContents());
          return div.innerText;
        }
      });
      payload = results[0]?.result || info.selectionText;
    } catch (_) {
      payload = info.selectionText;
    }
  }

  if (!payload?.trim()) return;

  // Notify content script to show scanning indicator
  try {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const ev = new CustomEvent('aetherguard-scanning');
        document.dispatchEvent(ev);
      }
    });
  } catch (_) {}

  try {
    // Grab stored auth token
    const stored = await chrome.storage.local.get('aether_token');
    const token = stored.aether_token || '';

    const formData = new FormData();
    formData.append('text', payload.substring(0, 4000));

    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(API_URL, {
      method: 'POST',
      body: formData,
      headers,
    });

    const data = await response.json();
    const score = data.final_risk_score ?? 0;
    const topReason = data.risk_breakdown?.[0]?.detail || '';

    // Store for popup
    chrome.storage.local.set({
      last_scan: {
        score,
        label: score > 60 ? 'HIGH RISK' : score > 30 ? 'SUSPICIOUS' : 'SAFE',
        reason: topReason,
        time: new Date().toISOString(),
      }
    });

    // Show result via script injection into page
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (scoreVal, reason) => {
        const ev = new CustomEvent('aetherguard-result', {
          detail: { score: scoreVal, reason }
        });
        document.dispatchEvent(ev);
      },
      args: [score, topReason]
    });

  } catch (err) {
    console.error('[AetherGuard] Context menu scan failed:', err);
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => alert('AETHERGUARD OFFLINE: Ensure Python backend is running on port 5000.'),
    });
  }
});

// ── Message listener (for popup to trigger actions) ──────────────────────────
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_STATUS') {
    fetch('http://127.0.0.1:5000/api/status', {
      method: 'GET',
      headers: { 'Authorization': 'Bearer admin_mock_token_123' }
    })
      .then(r => r.json())
      .then(data => sendResponse({ online: true, data }))
      .catch(() => sendResponse({ online: false }));
    return true; // keep channel open for async response
  }

  if (msg.type === 'SAVE_TOKEN') {
    chrome.storage.local.set({ aether_token: msg.token });
    sendResponse({ ok: true });
  }
});
