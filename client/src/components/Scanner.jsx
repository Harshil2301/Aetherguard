import { useState, useRef, useEffect } from 'react'
import { jsPDF } from 'jspdf'

const API = '/api'
const SCREENSHOT_BASE = 'https://image.thum.io/get/width/600/crop/700/noanimate/'

function exportToJSON(result, payload) {
  const report = {
    generated_at: new Date().toISOString(),
    payload_preview: (payload || '').substring(0, 200),
    final_risk_score: result.final_risk_score,
    verdict: result.final_risk_score > 60 ? 'ELEVATED RISK' : result.final_risk_score > 30 ? 'SUSPICIOUS' : 'SAFE',
    ml_classification: {
      result: result.ml_classification_result,
      confidence: result.ml_classification_confidence,
    },
    headers_status: result.headers_status || {},
    risk_breakdown: result.risk_breakdown || [],
    vt_urls: result.vt_urls || [],
    yara_matches: result.yara_matches || [],
    xai_attribution: result.xai_attribution || [],
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `aetherguard-report-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportToSTIX(result, payload) {
  const timestamp = new Date().toISOString();
  const idBase = `indicator--${crypto.randomUUID ? crypto.randomUUID() : Date.now()}`;
  
  const stixBundle = {
    type: "bundle",
    id: `bundle--${crypto.randomUUID ? crypto.randomUUID() : Date.now()}`,
    objects: []
  };

  // Create an indicator for the overall email if it's high risk
  if (result.final_risk_score >= 40) {
    stixBundle.objects.push({
      type: "indicator",
      spec_version: "2.1",
      id: idBase,
      created: timestamp,
      modified: timestamp,
      name: "Suspicious Email Payload",
      description: `AetherGuard detected an email with a risk score of ${result.final_risk_score}/100.`,
      pattern: "[email-message:subject != '']", // generic pattern, ideally we'd extract actual IOCs
      pattern_type: "stix",
      valid_from: timestamp
    });
  }

  // Create indicators for URLs found
  if (result.vt_urls && result.vt_urls.length > 0) {
    result.vt_urls.forEach(urlObj => {
      stixBundle.objects.push({
        type: "indicator",
        spec_version: "2.1",
        id: `indicator--${crypto.randomUUID ? crypto.randomUUID() : Date.now()}`,
        created: timestamp,
        modified: timestamp,
        name: "Malicious URL",
        description: `URL flagged by VirusTotal with ${urlObj.malicious_hits} hits.`,
        pattern: `[url:value = '${urlObj.url}']`,
        pattern_type: "stix",
        valid_from: timestamp
      });
    });
  }

  const blob = new Blob([JSON.stringify(stixBundle, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `aetherguard-stix-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportToIRReport(result, payload) {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const W = doc.internal.pageSize.getWidth();
  const pad = 48;
  let y = 0;

  const score = result.final_risk_score;
  const severity = score >= 80 ? 'CRITICAL' : score >= 60 ? 'HIGH' : score >= 40 ? 'MEDIUM' : score >= 20 ? 'LOW' : 'INFO';
  const [r, g, b] = score >= 60 ? [239, 68, 68] : score >= 40 ? [245, 158, 11] : [16, 185, 129];
  const iocList = (result.vt_urls || []).map(u => u.url).filter(Boolean);
  const failedProtos = Object.entries(result.headers_status || {}).filter(([,v]) => v === 'fail').map(([k]) => k.toUpperCase());

  // — Cover Page —
  doc.setFillColor(4, 12, 26);
  doc.rect(0, 0, W, 200, 'F');
  doc.setFillColor(r, g, b);
  doc.rect(0, 0, 6, 200, 'F');
  doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(100, 116, 139);
  doc.text('AETHERGUARD INCIDENT RESPONSE REPORT', pad, 50);
  doc.setFontSize(28); doc.setTextColor(226, 232, 240);
  doc.text('Threat Analysis', pad, 90);
  doc.text('Incident Report', pad, 118);
  doc.setFontSize(11); doc.setTextColor(r, g, b);
  doc.text(`Severity: ${severity}  |  Risk Score: ${score}/100`, pad, 148);
  doc.setFontSize(9); doc.setTextColor(71, 85, 105);
  doc.text(`Generated: ${new Date().toLocaleString()}  |  Classification: CONFIDENTIAL`, pad, 172);
  y = 230;

  // — Section 1: Executive Summary —
  doc.setFont('helvetica', 'bold'); doc.setFontSize(13); doc.setTextColor(34, 211, 238);
  doc.text('1. EXECUTIVE SUMMARY', pad, y); y += 20;
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(148, 163, 184);
  const summary = score >= 70
    ? `This email has been classified as a HIGH-SEVERITY phishing attempt with a composite risk score of ${score}/100. The AetherGuard multi-phase analysis engine detected ${result.risk_breakdown?.length || 0} active threat indicators across ML classification, URL analysis, and header authentication layers. Immediate quarantine is recommended.`
    : score >= 40
    ? `This email displays SUSPICIOUS characteristics with a risk score of ${score}/100. While not conclusively malicious, multiple heuristic flags were triggered. The email should be treated with caution and the sender's identity should be independently verified before any action is taken.`
    : `This email was assessed as LOW RISK with a score of ${score}/100. No significant threat indicators were detected across any analysis layer. Standard email hygiene practices are recommended.`;
  const sumLines = doc.splitTextToSize(summary, W - pad * 2);
  doc.text(sumLines, pad, y); y += sumLines.length * 14 + 20;

  // — Section 2: Threat Classification —
  doc.setFillColor(r, g, b, 0.06);
  doc.roundedRect(pad, y, W - pad * 2, 56, 6, 6, 'F');
  doc.setFont('helvetica', 'bold'); doc.setFontSize(13); doc.setTextColor(34, 211, 238);
  doc.text('2. THREAT CLASSIFICATION', pad + 12, y + 20); 
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(r, g, b);
  doc.text(`Severity: ${severity}   |   Score: ${score}/100   |   ML: ${result.ml_classification_result || 'N/A'}   |   Confidence: ${((result.ml_classification_confidence || 0)*100).toFixed(1)}%`, pad + 12, y + 42);
  y += 76;

  // — Section 3: Indicators of Compromise (IOCs) —
  doc.setFont('helvetica', 'bold'); doc.setFontSize(13); doc.setTextColor(34, 211, 238);
  doc.text('3. INDICATORS OF COMPROMISE (IOCs)', pad, y); y += 18;
  if (iocList.length > 0) {
    iocList.forEach(url => {
      doc.setFont('courier', 'normal'); doc.setFontSize(8.5); doc.setTextColor(239, 68, 68);
      doc.text(`• ${url.substring(0, 90)}`, pad + 8, y); y += 14;
    });
  } else if (failedProtos.length > 0) {
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(245, 158, 11);
    doc.text(`Failed authentication protocols: ${failedProtos.join(', ')}`, pad + 8, y); y += 16;
  } else {
    doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(100, 116, 139);
    doc.text('No network-level IOCs extracted.', pad + 8, y); y += 16;
  }
  y += 12;

  // — Section 4: Risk Breakdown —
  doc.setFont('helvetica', 'bold'); doc.setFontSize(13); doc.setTextColor(34, 211, 238);
  doc.text('4. DETECTION ENGINE FINDINGS', pad, y); y += 18;
  (result.risk_breakdown || []).forEach(b => {
    doc.setFont('helvetica', 'bold'); doc.setFontSize(9); doc.setTextColor(226, 232, 240);
    doc.text(`[${b.source}] +${b.points} pts`, pad + 8, y);
    doc.setFont('helvetica', 'normal'); doc.setTextColor(100, 116, 139);
    const dLines = doc.splitTextToSize(b.detail, W - pad * 2 - 16);
    y += 13; doc.text(dLines, pad + 16, y); y += dLines.length * 12 + 6;
  });
  y += 8;

  // — Section 5: Recommended Actions —
  if (y > 650) { doc.addPage(); y = 60; }
  doc.setFont('helvetica', 'bold'); doc.setFontSize(13); doc.setTextColor(34, 211, 238);
  doc.text('5. RECOMMENDED ACTIONS', pad, y); y += 18;
  const actions = score >= 70 ? [
    'IMMEDIATE: Quarantine this email and do not click any links or open attachments.',
    'Notify your IT Security / SOC team with this report attached.',
    'Run a full antivirus scan on any device that interacted with this email.',
    'Report the sending domain to your email provider and relevant authorities.',
    'Reset credentials if any links were clicked or forms were filled out.',
  ] : score >= 40 ? [
    'Do not respond to this email or click any links without independent verification.',
    'Verify the sender identity through an alternate communication channel.',
    'Forward to IT Security team for secondary assessment.',
  ] : [
    'No immediate action required. Continue standard email hygiene practices.',
    'If this email contains unexpected attachments, verify the sender before opening.',
  ];
  doc.setFont('helvetica', 'normal'); doc.setFontSize(10); doc.setTextColor(148, 163, 184);
  actions.forEach((a, i) => {
    const lines = doc.splitTextToSize(`${i+1}. ${a}`, W - pad * 2);
    doc.text(lines, pad + 8, y); y += lines.length * 14 + 4;
  });

  // — Footer —
  const ph = doc.internal.pageSize.getHeight();
  doc.setFillColor(4, 12, 26);
  doc.rect(0, ph - 32, W, 32, 'F');
  doc.setFontSize(8); doc.setTextColor(51, 65, 85);
  doc.text('AetherGuard · AI-Powered Email Security Gateway · CONFIDENTIAL — For Internal Use Only', pad, ph - 12);

  doc.save(`aetherguard-IR-${severity}-${Date.now()}.pdf`);
}

function exportToPDF(result, payload) {
  const doc = new jsPDF({ unit: 'pt', format: 'a4' });
  const W = doc.internal.pageSize.getWidth();
  const pad = 48;
  let y = 60;

  // Header
  doc.setFillColor(4, 12, 26);
  doc.rect(0, 0, W, 90, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(20);
  doc.setTextColor(34, 211, 238);
  doc.text('AETHERGUARD', pad, 40);
  doc.setFontSize(10);
  doc.setTextColor(148, 163, 184);
  doc.text('Threat Scan Report', pad, 58);
  doc.text(`Generated: ${new Date().toLocaleString()}`, pad, 72);
  y = 116;

  // Score box
  const score = result.final_risk_score;
  const [r, g, b] = score > 60 ? [239, 68, 68] : score > 30 ? [245, 158, 11] : [16, 185, 129];
  doc.setFillColor(r, g, b, 0.12);
  doc.roundedRect(pad, y, W - pad * 2, 64, 8, 8, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(32);
  doc.setTextColor(r, g, b);
  doc.text(`${score}`, pad + 16, y + 42);
  doc.setFontSize(13);
  doc.setTextColor(226, 232, 240);
  const verdict = score > 60 ? 'ELEVATED RISK — Likely Phishing' : score > 30 ? 'SUSPICIOUS — Proceed with Caution' : 'SAFE — No Threats Detected';
  doc.text(verdict, pad + 72, y + 42);
  y += 90;

  // Payload preview
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(100, 116, 139);
  doc.text('PAYLOAD PREVIEW', pad, y);
  y += 16;
  doc.setFont('courier', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(148, 163, 184);
  const previewLines = doc.splitTextToSize((payload || '').substring(0, 300) + (payload?.length > 300 ? '…' : ''), W - pad * 2);
  doc.text(previewLines, pad, y);
  y += previewLines.length * 13 + 20;

  // ML Result
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(11);
  doc.setTextColor(100, 116, 139);
  doc.text('ML CLASSIFICATION', pad, y);
  y += 16;
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(10);
  doc.setTextColor(226, 232, 240);
  doc.text(`Verdict: ${result.ml_classification_result || 'N/A'}`, pad, y);
  doc.text(`Confidence: ${((result.ml_classification_confidence || 0) * 100).toFixed(1)}%`, pad + 200, y);
  y += 28;

  // Breakdown
  if (result.risk_breakdown?.length > 0) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(100, 116, 139);
    doc.text('RISK BREAKDOWN', pad, y);
    y += 16;
    result.risk_breakdown.forEach(b => {
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(148, 163, 184);
      doc.text(`[${b.source}] ${b.detail}`, pad + 8, y);
      doc.setTextColor(239, 68, 68);
      doc.text(`+${b.points} pts`, W - pad - 40, y);
      doc.setTextColor(51, 65, 85);
      doc.line(pad, y + 4, W - pad, y + 4);
      y += 18;
    });
    y += 8;
  }

  // Headers
  if (Object.keys(result.headers_status || {}).length > 0) {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(100, 116, 139);
    doc.text('EMAIL AUTHENTICATION (SPF / DKIM / DMARC)', pad, y);
    y += 16;
    Object.entries(result.headers_status).forEach(([proto, status]) => {
      const [cr, cg, cb] = status === 'pass' ? [16, 185, 129] : status === 'fail' ? [239, 68, 68] : [245, 158, 11];
      doc.setTextColor(cr, cg, cb);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(9);
      doc.text(`[${status.toUpperCase()}]`, pad + 8, y);
      doc.setTextColor(148, 163, 184);
      doc.setFont('helvetica', 'normal');
      doc.text(`${proto.toUpperCase()} Protocol`, pad + 56, y);
      y += 16;
    });
    y += 8;
  }

  // Footer
  doc.setFillColor(4, 12, 26);
  const pageH = doc.internal.pageSize.getHeight();
  doc.rect(0, pageH - 36, W, 36, 'F');
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8);
  doc.setTextColor(51, 65, 85);
  doc.text('AetherGuard · AI-Powered Email Security Gateway · Confidential Report', pad, pageH - 14);

  doc.save(`aetherguard-report-${Date.now()}.pdf`);
}

export default function Scanner({ lastScanResult, setLastScanResult, lastScanText, setLastScanText }) {
  const [text, setText] = useState(lastScanText || '')
  const [files, setFiles] = useState([])
  const [isScanning, setIsScanning] = useState(false)
  const [result, setResult] = useState(lastScanResult || null)
  const [bulkResults, setBulkResults] = useState(null)
  const [screenshotUrl, setScreenshotUrl] = useState(
    lastScanResult ? (lastScanResult.vt_urls?.[0]?.url || extractFirstUrlStatic(lastScanText)) : null
  )
  const [showScreenshot, setShowScreenshot] = useState(false)
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)
  const [feedbackStats, setFeedbackStats] = useState(null)
  const fileInputRef = useRef(null)

  // Helper used at init time (before hooks)
  function extractFirstUrlStatic(txt) {
    const match = txt?.match(/https?:\/\/[^\s"'<>]+/);
    return match ? match[0] : null;
  }

  const getToken = () => localStorage.getItem('aether_token') || ''

  const loadFeedbackStats = async () => {
    try {
      const res = await fetch(`${API}/feedback/stats`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (res.ok) setFeedbackStats(await res.json());
    } catch (e) { /* silent fail */ }
  }

  // Load feedback stats when component mounts
  useEffect(() => {
    loadFeedbackStats()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleScan = async () => {
    if (!text.trim() && files.length === 0) return;
    setIsScanning(true);
    setScreenshotUrl(null);
    setShowScreenshot(false);
    setFeedbackSubmitted(false);
    setBulkResults(null);
    // Sync text up to parent immediately so it persists on tab switch
    if (setLastScanText) setLastScanText(text);

    try {
      const formData = new FormData();
      if (text) formData.append('text', text);
      files.forEach(f => formData.append('files', f)); // For bulk
      if (files.length === 1) formData.append('file', files[0]); // For single

      const endpoint = files.length > 1 ? `${API}/scan/bulk` : `${API}/scan`;

      const [res] = await Promise.all([
        fetch(endpoint, {
          method: 'POST',
          body: formData,
          headers: { 'Authorization': `Bearer ${getToken()}` },
        }),
        new Promise(r => setTimeout(r, 800))
      ]);

      const data = await res.json();
      
      if (files.length > 1) {
        setBulkResults(data.results);
      } else {
        setResult(data);
        if (setLastScanResult) setLastScanResult(data);
        const firstUrl = data.vt_urls?.[0]?.url || extractFirstUrl(text);
        if (firstUrl) setScreenshotUrl(firstUrl);
      }

    } catch (e) {
      console.error(e);
      alert('Scan Failed — ensure the backend is running on port 5000.');
    }
    setIsScanning(false);
  }

  const extractFirstUrl = (txt) => {
    const match = txt?.match(/https?:\/\/[^\s"'<>]+/);
    return match ? match[0] : null;
  }

  const handleFlush = () => {
    setText('');
    setFiles([]);
    setResult(null);
    setBulkResults(null);
    setScreenshotUrl(null);
    setShowScreenshot(false);
    // Also clear from parent so a fresh session starts clean
    if (setLastScanResult) setLastScanResult(null);
    if (setLastScanText) setLastScanText('');
    setFeedbackSubmitted(false);
  }

  const handleFeedback = async (feedbackType) => {
    if (!result || !result.scan_id) return;
    try {
      const res = await fetch(`${API}/scan/${result.scan_id}/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ feedback: feedbackType })
      });
      if (res.ok) {
        setFeedbackSubmitted(true);
        loadFeedbackStats(); // Refresh counts so user sees their contribution immediately
      }
    } catch (e) {
      console.error("Failed to submit feedback", e);
    }
  }

  const handleFileDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    if (droppedFiles.length > 0) setFiles(droppedFiles);
  }

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    if (selectedFiles.length > 0) setFiles(selectedFiles);
  }

  return (
    <div className="view-panel active-view">
      <header className="topbar">
        <div className="hero-text">
          <h1>Decentralized Entity Scanner</h1>
          <p>Harness localized ML verification and signature analysis protocol.</p>
        </div>
      </header>

      <div className="terminal-grid">
        {/* Payload Input Box */}
        <div className="card glass-panel left-panel">
          <div className="panel-header align-between">
            <h3>Payload Injection</h3>
            <div className="hex-badge">AETHER-INTEL</div>
          </div>

          <div className="form-container">
            <textarea
              className="hacker-textarea"
              placeholder=">> INSERT SUSPICIOUS EMAIL / PAYLOAD HERE..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isScanning}
            />

            <div
              className="file-drop cyber-drop"
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
              <p><strong>DROP FILE TO SCAN</strong></p>
              <span>.eml &nbsp;·&nbsp; .txt &nbsp;·&nbsp; .pdf &nbsp;·&nbsp; .docx &nbsp;·&nbsp; .jpg &nbsp;·&nbsp; .png</span>
              <input
                type="file"
                ref={fileInputRef}
                style={{ display: 'none' }}
                onChange={handleFileSelect}
                accept=".eml,.txt,.pdf,.docx,.doc,.jpg,.jpeg,.png,.gif,.bmp,.webp"
                multiple
              />
            </div>

            {files.length > 0 && (
              <div className="readout-box" style={{ display: 'block' }}>
                [ATTACHED_BLOB] :: {files.length === 1 ? `${files[0].name} (${(files[0].size / 1024).toFixed(1)} KB)` : `${files.length} files selected`}
              </div>
            )}

            <div className="button-row">
              <button className="web3-btn primary-btn" onClick={handleScan} disabled={isScanning}>
                <span className="btn-text">{isScanning ? 'EXECUTING DYNAMIC ANALYSIS...' : files.length > 1 ? 'INITIATE BULK SCAN' : 'INITIATE DEEP SCAN'}</span>
                <div className="btn-glow"></div>
              </button>
              <button className="web3-btn secondary-btn" onClick={handleFlush}>FLUSH</button>
            </div>
          </div>
        </div>

        {/* Results output box — overflow:visible so feedback buttons are always clickable */}
        <div className="card glass-panel right-panel" style={{ display: (isScanning || result || bulkResults) ? 'flex' : 'none', flexDirection: 'column', overflow: 'hidden' }}>
          {isScanning && (
            <div className="scanning-overlay">
              <div className="spinner"></div>
              <p className="crypto-text">INTERROGATING BLOCK...</p>
            </div>
          )}

          {bulkResults && (
            <div id="scanContent">
              <div className="panel-header align-between">
                <h3>Bulk Diagnostics</h3>
                <div style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                  {bulkResults.length} files analyzed
                </div>
              </div>
              <div style={{ marginTop: '15px', overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', textAlign: 'left', color: '#94a3b8' }}>
                      <th style={{ padding: '10px 5px' }}>File</th>
                      <th style={{ padding: '10px 5px' }}>Score</th>
                      <th style={{ padding: '10px 5px' }}>Verdict</th>
                      <th style={{ padding: '10px 5px' }}>ML Confidence</th>
                      <th style={{ padding: '10px 5px' }}>Threats</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bulkResults.map((r, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '10px 5px', color: '#cbd5e1' }}>{r.filename}</td>
                        <td style={{ padding: '10px 5px' }}>
                          <span style={{ color: r.final_risk_score > 60 ? '#f87171' : r.final_risk_score > 30 ? '#fbbf24' : '#34d399', fontWeight: 'bold' }}>
                            {r.final_risk_score}
                          </span>
                        </td>
                        <td style={{ padding: '10px 5px' }}>
                          <span className={`gradient-badge ${r.final_risk_score > 60 ? 'danger' : r.final_risk_score > 30 ? 'warning' : 'safe'}`} style={{ transform: 'scale(0.8)', display: 'inline-block' }}>
                            {r.final_risk_score > 60 ? 'ELEVATED' : r.final_risk_score > 30 ? 'SUSPICIOUS' : 'SECURE'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 5px', color: '#94a3b8' }}>{(r.ml_classification_confidence * 100).toFixed(1)}%</td>
                        <td style={{ padding: '10px 5px', color: '#94a3b8' }}>{r.risk_breakdown?.length || 0} alerts</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {result && (
            <div id="scanContent">
              <div className="panel-header align-between">
                <h3>Aether Diagnostics</h3>
                <div style={{ display:'flex', gap:'8px', alignItems:'center', flexWrap:'wrap' }}>
                  <span className={`gradient-badge ${result.final_risk_score > 60 ? 'danger' : result.final_risk_score > 30 ? 'warning' : 'safe'}`}>
                    {result.final_risk_score > 60 ? 'ELEVATED RISK' : result.final_risk_score > 30 ? 'SUSPICIOUS' : 'SECURE'}
                  </span>
                  {/* JSON Export — always available */}
                  <button
                    onClick={() => exportToJSON(result, text)}
                    style={{
                      padding: '5px 12px', borderRadius: '6px', fontSize: '11px',
                      fontWeight: 700, letterSpacing: '0.08em', cursor: 'pointer',
                      background: 'rgba(124,58,237,0.1)', border: '1px solid rgba(124,58,237,0.35)',
                      color: '#a78bfa', transition: 'all 0.2s',
                    }}
                    title="Export raw scan data as JSON"
                  >
                    ⬇ JSON
                  </button>
                  {/* IR Report — always available for any scan result */}
                  <button
                    onClick={() => exportToIRReport(result, text)}
                    style={{
                      padding: '5px 12px', borderRadius: '6px', fontSize: '11px',
                      fontWeight: 700, letterSpacing: '0.08em', cursor: 'pointer',
                      background: result.final_risk_score >= 40
                        ? 'rgba(239,68,68,0.1)' : 'rgba(16,185,129,0.1)',
                      border: result.final_risk_score >= 40
                        ? '1px solid rgba(239,68,68,0.35)' : '1px solid rgba(16,185,129,0.35)',
                      color: result.final_risk_score >= 40 ? '#f87171' : '#34d399',
                      transition: 'all 0.2s',
                    }}
                    title="Generate full Incident Response Report PDF"
                  >
                    🛡 IR Report
                  </button>
                </div>
              </div>


              <div className="results-matrix">
                <div className="score-crystal">
                  <div className="crystal-outer">
                    <div className={`crystal-inner ${result.final_risk_score > 60 ? 'danger' : result.final_risk_score > 30 ? 'warning' : 'safe'}`}>
                      <div className="score-val">{result.final_risk_score}</div>
                    </div>
                  </div>
                  <h4 className="crypto-text">
                    {result.final_risk_score > 60 ? 'ELEVATED RISK' : result.final_risk_score > 30 ? 'SUSPICIOUS ACTIVITY' : 'SAFE PROTOCOL'}
                  </h4>
                </div>

                {/* Breakdown Block */}
                {result.risk_breakdown && result.risk_breakdown.length > 0 && (
                  <div className="metric-block" style={{ display: 'block' }}>
                    <h5><span className="icon">◉</span> Risk Score Breakdown</h5>
                    <div className="breakdown-list">
                      {result.risk_breakdown.map((b, i) => (
                        <div key={i} className="breakdown-row">
                          <div className="breakdown-source">{b.source}</div>
                          <div className="breakdown-detail">{b.detail}</div>
                          <div className="breakdown-pts">+{b.points} <span style={{fontSize:'0.65rem'}}>pts</span></div>
                        </div>
                      ))}
                      <div className="breakdown-total">
                        <span>Combined Score</span>
                        <span style={{ color: result.final_risk_score > 60 ? 'var(--danger)' : 'var(--success)' }}>{result.final_risk_score} / 100</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* ── XAI Phrase Risk Analysis — only shown when email has some risk signals ── */}
                {result.xai_attribution && result.xai_attribution.length > 0 && result.final_risk_score > 20 && (
                  <div className="metric-block" style={{ display: 'block' }}>
                    <h5><span className="icon">🔬</span> Phrase Risk Analysis (XAI)</h5>
                    <div style={{ fontSize: '10px', color: 'var(--text-dim)', marginBottom: '10px', lineHeight: 1.5 }}>
                      <strong style={{ color: '#ef4444' }}>Note: </strong> 
                      If this is a phishing email, it is <strong>expected and correct</strong> to see phrases with high phishing percentages. 
                      These highlight the exact text that triggers the ML model. Scores reflect risk relative to the overall email.
                      <span style={{ color: '#ef4444', marginLeft: '6px' }}>●</span> High risk
                      <span style={{ color: '#f59e0b', marginLeft: '8px' }}>●</span> Moderate
                      <span style={{ color: '#10b981', marginLeft: '8px' }}>●</span> Legitimate
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
                      {result.xai_attribution.slice(0, 8).map((attr, i) => {
                        const pct = Math.round(attr.score * 100);
                        const bg = attr.score > 0.6
                          ? `rgba(239,68,68,${0.08 + attr.intensity * 0.25})`
                          : attr.score > 0.4
                          ? `rgba(245,158,11,${0.06 + attr.intensity * 0.2})`
                          : `rgba(16,185,129,${0.05 + (1 - attr.score) * 0.1})`;
                        const txtColor = attr.score > 0.6 ? '#f87171' : attr.score > 0.4 ? '#fbbf24' : '#6ee7b7';
                        return (
                          <div key={i} style={{
                            padding: '7px 10px', borderRadius: '6px',
                            background: bg,
                            border: `1px solid ${txtColor}30`,
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px',
                          }}>
                            <div style={{ fontSize: '11px', color: '#cbd5e1', lineHeight: 1.4, flex: 1, wordBreak: 'break-word' }}>
                              {attr.text.substring(0, 120)}{attr.text.length > 120 ? '…' : ''}
                            </div>
                            <div style={{ flexShrink: 0, textAlign: 'right' }}>
                              <div style={{ fontSize: '12px', fontWeight: 800, color: txtColor }}>{pct}%</div>
                              <div style={{ fontSize: '9px', color: txtColor, letterSpacing: '0.05em' }}>{attr.label}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* URL Screenshot Preview */}
                {screenshotUrl && (
                  <div className="metric-block" style={{ display: 'block' }}>
                    <h5 style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span><span className="icon">🖼</span> Link Preview</span>
                      <button
                        onClick={() => setShowScreenshot(s => !s)}
                        style={{
                          padding: '3px 10px', borderRadius: '5px', fontSize: '10px', fontWeight: 700,
                          background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
                          color: '#f87171', cursor: 'pointer',
                        }}
                      >
                        {showScreenshot ? 'HIDE' : 'PREVIEW LINK'}
                      </button>
                    </h5>
                    {showScreenshot && (
                      <div style={{ marginTop: '10px' }}>
                        <div style={{
                          fontSize: '10px', color: 'var(--text-dim)', marginBottom: '6px',
                          wordBreak: 'break-all', fontFamily: 'monospace',
                        }}>
                          ⚠ Previewing (not opening): {screenshotUrl.substring(0, 60)}…
                        </div>
                        <div style={{
                          border: '1px solid rgba(239,68,68,0.2)', borderRadius: '8px', overflow: 'hidden',
                          position: 'relative',
                        }}>
                          <div style={{
                            position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none',
                            background: 'linear-gradient(to bottom, transparent 70%, rgba(4,12,26,0.8))',
                          }} />
                          <img
                            src={`${SCREENSHOT_BASE}${encodeURIComponent(screenshotUrl)}`}
                            alt="URL Preview"
                            style={{ width: '100%', display: 'block', maxHeight: '200px', objectFit: 'cover', objectPosition: 'top' }}
                            onError={(e) => {
                              e.target.parentElement.innerHTML = '<div style="padding:16px;color:#64748b;font-size:11px;line-height:1.8">🔒 Live screenshot blocked by the URL host.<br/>This is expected and is a <strong>security feature</strong> — AetherGuard never navigates to or opens suspicious URLs.<br/>URL analysis was performed using header inspection and heuristic pattern matching.</div>';
                            }}
                          />
                        </div>
                        <div style={{ fontSize: '10px', color: '#334155', marginTop: '6px', textAlign: 'right' }}>
                          Safe preview via thum.io — URL was NOT opened
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Telemetry output lists */}
                <div className="metrics-list">
                  <div className="metric-block">
                    <h5><span className="icon">⬢</span> Signature Authentication</h5>
                    {Object.keys(result.headers_status || {}).length > 0 ? (
                      <ul className="terminal-list">
                        {Object.entries(result.headers_status).map(([proto, res]) => (
                          <li key={proto}>
                            <span style={{ color: res === 'pass' ? 'var(--success)' : res === 'fail' ? 'var(--danger)' : 'var(--warning)', fontWeight: 600 }}>[{res.toUpperCase()}]</span>{' '}
                            {proto.toUpperCase()} Protocol Authentication
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="data-box" style={{ color: 'var(--text-dim)' }}>[NULL] No headers (text-only or non-EML scan).</div>
                    )}
                  </div>

                  <div className="metric-block">
                    <h5><span className="icon">▲</span> Neural Net Classification</h5>
                    <div className="data-box">
                      <div><span style={{color:'var(--text-dim)'}}>&gt;&gt; Phishing Confidence</span> <span style={{ float:'right', color: result.ml_classification_confidence > 0.6 ? 'var(--danger)' : 'var(--success)' }}>{(result.ml_classification_confidence * 100).toFixed(1)}%</span></div>
                      <div style={{ marginTop:'8px', width:'100%', height:'4px', background:'rgba(255,255,255,0.1)', borderRadius:'2px'}}>
                        <div style={{ width: `${result.ml_classification_confidence * 100}%`, height:'100%', background: result.ml_classification_confidence > 0.6 ? 'var(--danger)' : 'var(--success)', borderRadius:'2px'}}></div>
                      </div>
                      <div style={{ marginTop: '12px' }}><span style={{color:'var(--text-dim)'}}>&gt;&gt; Resolution:</span> {result.ml_classification_result}</div>
                    </div>
                  </div>
                </div>

                {/* ── Active Learning Feedback Loop ── */}
                <div className="metric-block" style={{
                  display: 'block', marginTop: '20px',
                  background: 'rgba(34,211,238,0.04)',
                  border: '1px solid rgba(34,211,238,0.15)',
                  position: 'relative',
                  zIndex: 10,
                  overflow: 'visible',
                }}>
                  <h5 style={{ color: '#22d3ee', marginBottom: '8px' }}><span className="icon">🧠</span> Active Learning Feedback</h5>
                  <p style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '14px', lineHeight: 1.6 }}>
                    Was this classification correct? Your feedback is used to retrain the AI model and reduce future errors for everyone.
                  </p>

                  {/* Live feedback stats bar — loads from /api/feedback/stats */}
                  {feedbackStats && feedbackStats.total_with_feedback > 0 && (
                    <div style={{
                      display: 'flex', gap: '16px', flexWrap: 'wrap',
                      padding: '8px 12px', borderRadius: '6px',
                      background: 'rgba(255,255,255,0.03)',
                      border: '1px solid rgba(255,255,255,0.07)',
                      marginBottom: '14px', fontSize: '11px',
                    }}>
                      <span style={{ color: '#10b981', fontWeight: 600 }}>✓ {feedbackStats.correct} Correct</span>
                      <span style={{ color: '#ef4444', fontWeight: 600 }}>✗ {feedbackStats.false_positive} False Positives</span>
                      <span style={{ color: '#f59e0b', fontWeight: 600 }}>⚠ {feedbackStats.false_negative} Missed Threats</span>
                      <span style={{ color: '#475569', marginLeft: 'auto' }}>
                        {feedbackStats.accuracy_pct}% model accuracy · {feedbackStats.total_scans} total scans analyzed
                      </span>
                    </div>
                  )}

                  {!feedbackSubmitted ? (
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', position: 'relative', zIndex: 20 }}>
                      <button
                        onClick={() => handleFeedback('correct')}
                        style={{ padding: '8px 16px', background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid #10b981', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>
                        ✓ Correct — Model got it right
                      </button>
                      <button
                        onClick={() => handleFeedback('false_positive')}
                        style={{ padding: '8px 16px', background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid #ef4444', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>
                        ✗ False Positive — It's safe
                      </button>
                      <button
                        onClick={() => handleFeedback('false_negative')}
                        style={{ padding: '8px 16px', background: 'rgba(245,158,11,0.15)', color: '#f59e0b', border: '1px solid #f59e0b', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', fontWeight: 'bold' }}>
                        ✗ False Negative — It's malicious
                      </button>
                    </div>
                  ) : (
                    <div style={{ fontSize: '13px', color: '#10b981', fontWeight: 'bold', padding: '6px 0' }}>
                      ✓ Feedback recorded. Thank you — this will be used in the next model retraining cycle.
                    </div>
                  )}
                </div>

              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
