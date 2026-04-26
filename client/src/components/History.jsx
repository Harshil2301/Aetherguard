import { useState, useEffect, useCallback } from 'react'

const API = '/api'

export default function History() {
  const [history, setHistory]   = useState([])
  const [stats, setStats]       = useState({ total: 0, threats: 0, safe: 0, warnings: 0 })
  const [loading, setLoading]   = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [gatewayOnline, setGatewayOnline] = useState(false)
  const [mlActive, setMlActive] = useState(false)

  const token = () => localStorage.getItem('aether_token')

  const fetchHistory = useCallback(async () => {
    try {
      // Fetch stats and history in parallel
      const [statsRes, histRes] = await Promise.all([
        fetch(`${API}/telemetry/stats`, {
          headers: { 'Authorization': `Bearer ${token()}` }
        }),
        fetch(`${API}/history`, {
          headers: { 'Authorization': `Bearer ${token()}` }
        })
      ])

      // Handle stats response (tells us gateway/ml status)
      if (statsRes.ok) {
        const statsData = await statsRes.json()
        if (!statsData.error) {
          setGatewayOnline(statsData.gateway_status === 'ONLINE')
          setMlActive(statsData.ml_loaded === true)
          setStats({
            total: statsData.total_scans,
            threats: statsData.threats,
            warnings: statsData.warnings,
            safe: statsData.safe,
          })
        }
      } else {
        setGatewayOnline(false)
      }

      // Handle history response (scan log table)
      if (histRes.ok) {
        const data = await histRes.json()
        if (!data.error) {
          setHistory(data)
        }
      }

      setLastUpdated(new Date())
    } catch (e) {
      setGatewayOnline(false)
    } finally {
      setLoading(false)
    }
  }, [])


  // Fetch on mount and every 10 seconds (live updates)
  useEffect(() => {
    fetchHistory()
    const interval = setInterval(fetchHistory, 10000)
    return () => clearInterval(interval)
  }, [fetchHistory])

  const getThreatLevel = () => {
    if (stats.threats === 0) return { label: 'CLEAR', color: 'var(--success)' }
    if (stats.threats < 3)  return { label: 'ELEVATED', color: 'var(--warning)' }
    return { label: 'CRITICAL', color: 'var(--danger)' }
  }
  const threat = getThreatLevel()

  return (
    <div className="view-panel active-view">
      <header className="topbar">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div className="hero-text">
            <h1>Telemetry Node</h1>
            <p>Live diagnostics and scan activity — auto-refreshes every 10s.</p>
          </div>
          <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-dim)', fontFamily: '"Space Grotesk", monospace' }}>
            {lastUpdated ? (
              <>⟳ Last sync: {lastUpdated.toLocaleTimeString()}</>
            ) : 'Syncing...'}
          </div>
        </div>
      </header>

      <div className="telemetry-body">

        {/* ── System Status Row (DYNAMIC) ── */}
        <div className="telemetry-row">
          <div className="tele-card glass-panel">
            <div className="tele-card-icon">⬡</div>
            <div className="tele-card-label">Gateway Status</div>
            <div className={`tele-card-value ${gatewayOnline ? 'online' : 'offline'}`}>
              {loading ? '…' : gatewayOnline ? 'ONLINE' : 'OFFLINE'}
            </div>
          </div>
          <div className="tele-card glass-panel">
            <div className="tele-card-icon">▲</div>
            <div className="tele-card-label">ML Neural Engine</div>
            <div className={`tele-card-value ${mlActive ? 'online' : 'offline'}`}>
              {loading ? '…' : mlActive ? 'ACTIVE' : 'LOADING'}
            </div>
          </div>
          <div className="tele-card glass-panel">
            <div className="tele-card-icon">◈</div>
            <div className="tele-card-label">Threat Level</div>
            <div className="tele-card-value" style={{ color: threat.color }}>
              {loading ? '…' : threat.label}
            </div>
          </div>
        </div>

        {/* ── Session Stats (DYNAMIC — from real scan data) ── */}
        <div className="telemetry-row">
          <div className="tele-stat glass-panel">
            <div className="tele-stat-num" style={{ transition: 'all 0.5s ease' }}>
              {loading ? '—' : stats.total}
            </div>
            <div className="tele-stat-label">Total Scans</div>
          </div>
          <div className="tele-stat glass-panel">
            <div className="tele-stat-num danger-text" style={{ transition: 'all 0.5s ease' }}>
              {loading ? '—' : stats.threats}
            </div>
            <div className="tele-stat-label">Threats Detected</div>
          </div>
          <div className="tele-stat glass-panel">
            <div className="tele-stat-num success-text" style={{ transition: 'all 0.5s ease' }}>
              {loading ? '—' : stats.safe}
            </div>
            <div className="tele-stat-label">Safe Payloads</div>
          </div>
          <div className="tele-stat glass-panel">
            <div className="tele-stat-num warning-text" style={{ transition: 'all 0.5s ease' }}>
              {loading ? '—' : stats.warnings}
            </div>
            <div className="tele-stat-label">Elevated Risk</div>
          </div>
        </div>

        {/* ── Detection Rate Bar (DYNAMIC) ── */}
        {stats.total > 0 && (
          <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', fontSize: '0.8rem', color: 'var(--text-dim)', letterSpacing: '0.05em' }}>
              <span>⚡ SESSION DETECTION BREAKDOWN</span>
              <span>{stats.total} total scans</span>
            </div>
            <div style={{ display: 'flex', height: '8px', borderRadius: '99px', overflow: 'hidden', gap: '2px' }}>
              <div style={{ flex: stats.threats,  background: 'var(--danger)',  transition: 'flex 0.6s ease', minWidth: stats.threats > 0 ? '4px' : 0 }} title={`Threats: ${stats.threats}`} />
              <div style={{ flex: stats.warnings, background: 'var(--warning)', transition: 'flex 0.6s ease', minWidth: stats.warnings > 0 ? '4px' : 0 }} title={`Warnings: ${stats.warnings}`} />
              <div style={{ flex: stats.safe,     background: 'var(--success)', transition: 'flex 0.6s ease', minWidth: stats.safe > 0 ? '4px' : 0 }} title={`Safe: ${stats.safe}`} />
            </div>
            <div style={{ display: 'flex', gap: '20px', marginTop: '8px', fontSize: '0.72rem' }}>
              <span style={{ color: 'var(--danger)' }}>● Threat ({stats.threats})</span>
              <span style={{ color: 'var(--warning)' }}>● Elevated ({stats.warnings})</span>
              <span style={{ color: 'var(--success)' }}>● Safe ({stats.safe})</span>
            </div>
          </div>
        )}

        {/* ── Scan History Table ── */}
        <div className="tele-history glass-panel">
          <div className="panel-header align-between">
            <h3>Session Scan Log</h3>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <button className="export-btn" onClick={fetchHistory}>⟳ REFRESH</button>
              <div className="hex-badge" style={{ background: gatewayOnline ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', color: gatewayOnline ? 'var(--success)' : 'var(--danger)', borderColor: gatewayOnline ? 'var(--success)' : 'var(--danger)' }}>
                {gatewayOnline ? 'LIVE' : 'OFFLINE'}
              </div>
            </div>
          </div>
          <div className="history-table">
            {loading ? (
              <div className="history-empty">
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                  <div style={{ width: '28px', height: '28px', border: '2px solid rgba(0,240,255,0.2)', borderTopColor: 'var(--accent-neon)', borderRadius: '50%', animation: 'spin 0.9s linear infinite' }} />
                  Loading telemetry data...
                </div>
              </div>
            ) : history.length === 0 ? (
              <div className="history-empty">
                No scans recorded yet. Run a scan from Aether Core Intel to see live data here.
              </div>
            ) : (
              <>
                <div className="history-row history-header">
                  <div>TIMESTAMP</div>
                  <div>SCORE</div>
                  <div>PAYLOAD PREVIEW</div>
                  <div>VT HITS</div>
                </div>
                {history.map(row => (
                  <div key={row.id} className="history-row">
                    <div style={{ color: 'var(--text-dim)', fontFamily: '"Space Grotesk", monospace', fontSize: '0.8rem' }}>
                      {new Date(row.timestamp).toLocaleTimeString()}
                      <div style={{ fontSize: '0.7rem', marginTop: '2px' }}>{new Date(row.timestamp).toLocaleDateString()}</div>
                    </div>
                    <div>
                      <span className={`score-chip ${row.final_risk_score > 60 ? 'danger' : row.final_risk_score > 30 ? 'warning' : 'safe'}`}>
                        {row.final_risk_score}
                      </span>
                    </div>
                    <div style={{ fontFamily: '"Space Grotesk", monospace', color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      "{row.payload_preview}"
                    </div>
                    <div style={{ color: row.vt_malicious_hits > 0 ? 'var(--danger)' : 'var(--text-dim)' }}>
                      {row.vt_malicious_hits > 0 ? `🚨 ${row.vt_malicious_hits} Flags` : '✓ Clean'}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>

      </div>
    </div>
  )
}
