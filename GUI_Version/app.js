// ============================
// CONSTANTS
// ============================
const HISTORY_KEY = 'aetherguard_scan_history';

// ============================
// SCAN HISTORY (persisted in localStorage)
// ============================
const sessionScans = [];

function saveHistory() {
    try {
        // Keep last 100 scans
        localStorage.setItem(HISTORY_KEY, JSON.stringify(sessionScans.slice(-100)));
    } catch (e) { /* Storage full or unavailable */ }
}

function loadHistory() {
    try {
        const saved = localStorage.getItem(HISTORY_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            if (Array.isArray(parsed)) sessionScans.push(...parsed);
        }
    } catch (e) { /* Parse error */ }
}

// Load history immediately on script parse
loadHistory();

// ============================
// VIEW SWITCHING
// ============================
window.switchView = function (view) {
    const scannerView   = document.getElementById('view-scanner');
    const telemetryView = document.getElementById('view-telemetry');
    const navScanner    = document.getElementById('navScanner');
    const navTelemetry  = document.getElementById('navTelemetry');

    if (view === 'scanner') {
        scannerView.style.display   = 'flex';
        telemetryView.style.display = 'none';
        navScanner.classList.add('active');
        navTelemetry.classList.remove('active');
    } else {
        scannerView.style.display   = 'none';
        telemetryView.style.display = 'flex';
        navScanner.classList.remove('active');
        navTelemetry.classList.add('active');
        loadTelemetry();
    }
};

// ============================
// TELEMETRY LOADER
// ============================
async function loadTelemetry() {
    // System status from backend
    try {
        const res  = await fetch('/api/status');
        const data = await res.json();

        const teleGateway = document.getElementById('teleGateway');
        const teleMl      = document.getElementById('teleMl');
        const teleVt      = document.getElementById('teleVt');

        teleGateway.textContent = data.gateway_status || 'ONLINE';
        teleGateway.className   = 'tele-card-value online';

        teleMl.textContent = data.ml_loaded ? 'LOADED ✓' : 'NOT FOUND ✗';
        teleMl.className   = `tele-card-value ${data.ml_loaded ? 'online' : 'offline'}`;

        teleVt.textContent = data.vt_api_active ? 'API KEY SET ✓' : 'HEURISTIC MODE';
        teleVt.className   = `tele-card-value ${data.vt_api_active ? 'online' : 'offline'}`;
    } catch (e) {
        console.warn('Status endpoint error:', e);
    }

    // Session counters
    const total    = sessionScans.length;
    const threats  = sessionScans.filter(s => s.score >= 70).length;
    const safe     = sessionScans.filter(s => s.score < 30).length;
    const warnings = sessionScans.filter(s => s.score >= 30 && s.score < 70).length;

    document.getElementById('statTotal').textContent    = total;
    document.getElementById('statThreats').textContent  = threats;
    document.getElementById('statSafe').textContent     = safe;
    document.getElementById('statWarnings').textContent = warnings;

    // History table
    const table = document.getElementById('scanHistoryTable');
    if (sessionScans.length === 0) {
        table.innerHTML = '<div class="history-empty">No scans recorded. Run a scan from Aether Core Intel.</div>';
        return;
    }

    let html = `
        <div class="history-row history-header">
            <span>Timestamp</span><span>Score</span>
            <span>Risk Level</span><span>ML Classification</span>
        </div>`;

    [...sessionScans].reverse().forEach(scan => {
        const cls   = scan.score >= 70 ? 'danger' : scan.score >= 30 ? 'warning' : 'safe';
        const label = scan.score >= 70 ? 'CRITICAL' : scan.score >= 30 ? 'ELEVATED' : 'SAFE';
        const color = cls === 'danger' ? 'var(--danger)' : cls === 'warning' ? 'var(--warning)' : 'var(--success)';
        html += `
            <div class="history-row">
                <span style="color:var(--text-dim);font-size:0.78rem;">${scan.time}</span>
                <span><span class="score-chip ${cls}">${scan.score}</span></span>
                <span style="color:${color};font-size:0.82rem;">${label}</span>
                <span style="color:var(--text-dim);font-size:0.78rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${scan.mlResult}</span>
            </div>`;
    });

    table.innerHTML = html;
}

// ============================
// EXPORT REPORT
// ============================
let lastScanData = null;

function exportReport() {
    if (!lastScanData) return;
    const report = {
        generated:       new Date().toISOString(),
        gateway:         'AetherGuard v1.0',
        risk_score:      lastScanData.final_risk_score,
        risk_level:      lastScanData.final_risk_score >= 70 ? 'CRITICAL' : lastScanData.final_risk_score >= 30 ? 'ELEVATED' : 'SAFE',
        ml_confidence_pct: parseFloat((lastScanData.ml_classification_confidence * 100).toFixed(1)),
        ml_result:       lastScanData.ml_classification_result,
        headers:         lastScanData.headers_status,
        urls_analyzed:   lastScanData.vt_urls,
        risk_breakdown:  lastScanData.risk_breakdown || [],
        extraction_note: lastScanData.extraction_note || null
    };

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const a    = document.createElement('a');
    a.href     = URL.createObjectURL(blob);
    a.download = `aetherguard_report_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    showToast('Report downloaded successfully.', 'success', 2500);
}

// ============================
// MESH PARTICLE CANVAS
// ============================
document.addEventListener("DOMContentLoaded", () => {
    const canvas = document.getElementById('web3Canvas');
    const ctx    = canvas.getContext('2d');
    let width, height;

    function resize() {
        width  = canvas.width  = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);
    resize();

    const PARTICLE_COUNT  = 80;
    const CONNECTION_DIST = 160;
    const particles       = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push({
            x: Math.random() * width,
            y: Math.random() * height,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            size: Math.random() * 2 + 0.5,
            opacity: Math.random() * 0.5 + 0.2
        });
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > width)  p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 240, 255, ${p.opacity})`;
            ctx.fill();
        });

        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx   = particles[i].x - particles[j].x;
                const dy   = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < CONNECTION_DIST) {
                    const alpha = (1 - dist / CONNECTION_DIST) * 0.22;
                    const grad  = ctx.createLinearGradient(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    grad.addColorStop(0, `rgba(139, 92, 246, ${alpha})`);
                    grad.addColorStop(1, `rgba(0, 240, 255, ${alpha})`);
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = grad;
                    ctx.lineWidth   = 0.8;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();

    // ============================
    // TOAST SYSTEM
    // ============================
    const toastContainer = document.getElementById('toast-container');

    function showToast(message, type = 'error', duration = 4000) {
        const icons = { error: '⬡', warning: '⚠', success: '✓' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span class="toast-icon">${icons[type] || '⬡'}</span><span class="toast-msg">${message}</span>`;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('dismissing');
            toast.addEventListener('animationend', () => toast.remove(), { once: true });
        }, duration);
    }

    // Expose globally for exportReport (called outside DOMContentLoaded)
    window.showToast = showToast;

    // ============================
    // DOM REFERENCES
    // ============================
    const emailInput      = document.getElementById("emailInput");
    const fileInput       = document.getElementById("fileInput");
    const dropZone        = document.getElementById("dropZone");
    const fileReadout     = document.getElementById("fileReadout");
    const analyzeBtn      = document.getElementById("analyzeBtn");
    const clearBtn        = document.getElementById("clearBtn");
    const exportBtn       = document.getElementById("exportBtn");
    const resultsPanel    = document.getElementById("resultsPanel");
    const scanningOverlay = document.getElementById("scanningOverlay");
    const scanContent     = document.getElementById("scanContent");
    const crystalInner    = document.getElementById("crystalInner");
    const scoreText       = document.getElementById("scoreText");
    const threatBadge     = document.getElementById("threatBadge");
    const riskLabel       = document.getElementById("riskLabel");
    const headerResults   = document.getElementById("headerResults");
    const mlResults       = document.getElementById("mlResults");
    const vtResults       = document.getElementById("vtResults");
    const breakdownBlock  = document.getElementById("breakdownBlock");
    const breakdownList   = document.getElementById("breakdownList");

    let currentAttachment = null;

    // Export button wiring
    exportBtn.addEventListener("click", exportReport);

    // ============================
    // FILE HANDLERS
    // ============================
    const ALLOWED_EXTS = ['.eml', '.txt', '.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'];
    const FILE_TYPE_ICONS = {
        '.eml': '📧', '.txt': '📄', '.pdf': '📕',
        '.doc': '📝', '.docx': '📝',
        '.jpg': '🖼', '.jpeg': '🖼', '.png': '🖼', '.gif': '🖼', '.bmp': '🖼', '.webp': '🖼'
    };

    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "var(--accent-neon)";
        dropZone.style.background  = "rgba(0, 240, 255, 0.05)";
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "";
        dropZone.style.background  = "";
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "";
        dropZone.style.background  = "";
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
        if (!ALLOWED_EXTS.includes(ext)) {
            showToast(`Unsupported: ${ext}. Supported: ${ALLOWED_EXTS.join(', ')}`, 'error');
            return;
        }
        currentAttachment = file;
        const icon = FILE_TYPE_ICONS[ext] || '📄';
        fileReadout.style.display = "block";
        fileReadout.innerHTML = `${icon} INGESTED: <span style="color:var(--accent-neon)">${file.name}</span> &nbsp;[${(file.size / 1024).toFixed(1)} KB]`;
        showToast(`${icon} File loaded: ${file.name}`, 'success', 2500);
    }

    // ============================
    // FLUSH
    // ============================
    clearBtn.addEventListener("click", () => {
        emailInput.value           = "";
        currentAttachment          = null;
        fileInput.value            = "";
        fileReadout.style.display  = "none";
        resultsPanel.style.display = "none";
        crystalInner.className     = "crystal-inner";
        scoreText.textContent      = "0";
        exportBtn.style.display    = "none";
        lastScanData               = null;
    });

    // ============================
    // SCAN EXECUTION
    // ============================
    analyzeBtn.addEventListener("click", async () => {
        if (!emailInput.value.trim() && !currentAttachment) {
            showToast("SYS_ERR: Zero payload. Inject text or upload a file.", 'warning');
            return;
        }

        analyzeBtn.disabled = true;
        document.querySelector(".btn-text").innerText = "EXECUTING...";

        resultsPanel.style.display    = "flex";
        scanningOverlay.style.display = "flex";
        scanContent.style.opacity     = "0";
        scanContent.style.transition  = "";
        exportBtn.style.display       = "none";
        breakdownBlock.style.display  = "none";

        const formData = new FormData();
        if (emailInput.value.trim()) formData.append("text", emailInput.value);
        if (currentAttachment)       formData.append("file", currentAttachment);

        try {
            const response = await fetch('/api/scan', { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Server error ${response.status}`);

            const data = await response.json();
            if (data.error) throw new Error(data.error);

            lastScanData = data;

            // Record in session history
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-GB', { hour12: false }) +
                            ' ' + now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
            sessionScans.push({ time: timeStr, score: data.final_risk_score, mlResult: data.ml_classification_result || 'N/A' });
            saveHistory();

            setTimeout(() => {
                scanningOverlay.style.display = "none";
                scanContent.style.transition  = "opacity 0.6s ease";
                scanContent.style.opacity     = "1";
                renderResults(data);
                analyzeBtn.disabled = false;
                document.querySelector(".btn-text").innerText = "INITIATE DEEP SCAN";
            }, 1400);

        } catch (error) {
            console.error("Scan failed:", error);
            showToast(`SYS_ERR: ${error.message || 'Backend connection failed.'}`, 'error');
            analyzeBtn.disabled           = false;
            document.querySelector(".btn-text").innerText = "INITIATE DEEP SCAN";
            resultsPanel.style.display    = "none";
            scanningOverlay.style.display = "none";
        }
    });

    // ============================
    // RENDER RESULTS
    // ============================
    function renderResults(data) {
        let scoreClass = "safe", level = "SAFE NODE", color = "var(--success)";
        if      (data.final_risk_score >= 70) { scoreClass = "danger";  level = "CRITICAL BREACH"; color = "var(--danger)"; }
        else if (data.final_risk_score >= 30) { scoreClass = "warning"; level = "ELEVATED RISK";   color = "var(--warning)"; }

        crystalInner.className  = `crystal-inner ${scoreClass}`;
        riskLabel.textContent   = level;
        riskLabel.style.color   = color;
        threatBadge.className   = `gradient-badge ${scoreClass}`;
        threatBadge.textContent = level;

        // Show export button
        exportBtn.style.display = "inline-block";

        // Ease-out score counter
        let startTs = null;
        const end   = data.final_risk_score;
        function step(ts) {
            if (!startTs) startTs = ts;
            const prog  = Math.min((ts - startTs) / 1200, 1);
            const eased = 1 - Math.pow(1 - prog, 3);
            scoreText.textContent = Math.floor(eased * end);
            if (prog < 1) requestAnimationFrame(step);
            else scoreText.textContent = end;
        }
        requestAnimationFrame(step);

        // Severity toast
        if (scoreClass === 'danger')       showToast('⚠ Critical threat detected!', 'error', 5000);
        else if (scoreClass === 'warning') showToast('Elevated risk signals found.', 'warning', 4000);
        else                               showToast('Scan complete — payload appears safe.', 'success', 3000);

        // Extraction note (PDF/OCR warnings)
        const existingNote = document.getElementById('extractionNote');
        if (existingNote) existingNote.remove();
        if (data.extraction_note) {
            const noteEl = document.createElement('div');
            noteEl.id    = 'extractionNote';
            noteEl.className = 'extraction-note';
            noteEl.textContent = data.extraction_note;
            scanContent.insertBefore(noteEl, scanContent.querySelector('.results-matrix'));
        }

        // ── Risk Breakdown ──
        if (data.risk_breakdown && data.risk_breakdown.length > 0) {
            breakdownBlock.style.display = "block";
            let bHtml = '';
            data.risk_breakdown.forEach(item => {
                bHtml += `
                    <div class="breakdown-row">
                        <span class="breakdown-source">${item.source}</span>
                        <span class="breakdown-detail">${item.detail}</span>
                        <span class="breakdown-pts">+${item.points} pts</span>
                    </div>`;
            });
            const total = data.risk_breakdown.reduce((acc, i) => acc + i.points, 0);
            bHtml += `
                <div class="breakdown-total">
                    <span>Combined Score</span>
                    <span style="color:${color}; font-size:1rem;">${Math.min(total, 100)} / 100</span>
                </div>`;
            breakdownList.innerHTML = bHtml;
        } else {
            breakdownBlock.style.display = "none";
        }

        // ── Header Authentication ──
        headerResults.innerHTML = "";
        if (data.headers_status && Object.keys(data.headers_status).length > 0) {
            for (let [key, status] of Object.entries(data.headers_status)) {
                const sym = status === 'pass' ? '[OK]' : status === 'fail' ? '[FAIL]' : '[NONE]';
                const c   = status === 'pass' ? 'var(--success)' : status === 'fail' ? 'var(--danger)' : 'var(--warning)';
                headerResults.innerHTML += `<li><span style="color:${c};font-weight:700;min-width:52px;">${sym}</span>${key.toUpperCase()} — ${status.toUpperCase()}</li>`;
            }
        } else {
            headerResults.innerHTML = `<li><span style="color:var(--text-dim)">[NULL]</span> No headers (text-only or non-EML scan).</li>`;
        }

        // ── ML Neural Net ──
        const mlConf  = (data.ml_classification_confidence * 100).toFixed(1);
        const mlColor = data.ml_classification_confidence > 0.6 ? 'var(--danger)' : 'var(--success)';
        mlResults.innerHTML = `
            <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                <span style="color:var(--text-dim);">>> Phishing Confidence</span>
                <span style="color:${mlColor};font-weight:700;">${mlConf}%</span>
            </div>
            <div style="background:rgba(0,0,0,0.3);border-radius:4px;height:6px;overflow:hidden;margin-bottom:10px;">
                <div style="width:${mlConf}%;height:100%;background:linear-gradient(90deg,var(--accent-purple),${mlColor});border-radius:4px;transition:width 1s ease;"></div>
            </div>
            <div style="color:var(--text-dim);">>> Resolution: <span style="color:white;">${data.ml_classification_result}</span></div>`;

        // ── VirusTotal / URL Results ──
        if (data.vt_urls && data.vt_urls.length > 0) {
            vtResults.innerHTML = "";
            data.vt_urls.forEach(u => {
                const hc    = u.malicious_hits > 0 ? "var(--danger)" : "var(--success)";
                const sc    = u.total_scans > 0 ? u.total_scans : 'OFFLINE';
                const flags = u.heuristic_flags && u.heuristic_flags.length > 0
                    ? `<div style="margin-top:4px;">${u.heuristic_flags.map(f => `<span style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);color:#FCA5A5;border-radius:4px;padding:2px 7px;font-size:0.72rem;margin-right:4px;">${f}</span>`).join('')}</div>`
                    : '';
                vtResults.innerHTML += `
                    <div style="margin-bottom:12px;border-bottom:1px dashed rgba(255,255,255,0.08);padding-bottom:10px;">
                        <div style="color:var(--text-dim);word-break:break-all;font-size:0.8rem;margin-bottom:4px;">◈ ${u.url}</div>
                        <div style="color:${hc};font-weight:600;margin-bottom:4px;">>> ${u.malicious_hits} / ${sc} Nodes Flagged</div>
                        ${flags}
                    </div>`;
            });
        } else {
            vtResults.innerHTML = `<span style="color:var(--text-dim);">>> Zero URLs detected in payload.</span>`;
        }
    }
});
