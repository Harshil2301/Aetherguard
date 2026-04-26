import { useState, useEffect } from 'react'
import Scanner from '../components/Scanner'
import History from '../components/History'
import YaraEditor from '../components/YaraEditor'
import Settings from '../components/Settings'
import { Navigate } from 'react-router-dom'

function Dashboard() {
  const [activeTab, setActiveTab] = useState('scanner')
  const [token, setToken] = useState(() => {
    // Check URL params first (handoff from Next.js dashboard gateway)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlUser = params.get('user');
    if (urlToken) {
      localStorage.setItem('aether_token', urlToken);
      if (urlUser) localStorage.setItem('aether_user', decodeURIComponent(urlUser));
      // Clean URL without reloading
      window.history.replaceState({}, '', window.location.pathname);
      return urlToken;
    }
    return localStorage.getItem('aether_token');
  })
  const [user, setUser] = useState(localStorage.getItem('aether_user') || 'ADMIN')
  // Lifted scan result — persists when navigating between tabs
  const [lastScanResult, setLastScanResult] = useState(null)
  const [lastScanText, setLastScanText]     = useState('')

  useEffect(() => {
    setUser(localStorage.getItem('aether_user') || 'ADMIN')
  }, [token])

  if (!token) {
      return <Navigate to="/login" />
  }

  const handleLogout = () => {
      localStorage.removeItem('aether_token')
      localStorage.removeItem('aether_user')
      setToken(null)
  }

  return (
    <div className="dashboard-layout-root">
      <div className="glow-orb orb-1"></div>
      <div className="glow-orb orb-2"></div>

      <div className="app-layout">
        <aside className="sidebar glass-panel">
            <div className="logo">
                <div className="logo-box" style={{ borderRadius: '10px', background: 'linear-gradient(135deg, #22d3ee, #7c3aed)', boxShadow: '0 0 18px rgba(34,211,238,0.3)' }}>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/>
                        <polyline points="9 12 11 14 15 10"/>
                    </svg>
                </div>
                <h2>AETHERGUARD</h2>
            </div>
            
            <nav className="nav">
                <p className="nav-title">NEXUS MODULES</p>
                <a href="#" className={`nav-item ${activeTab === 'scanner' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('scanner'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
                    Aether Core Intel
                </a>
                <a href="#" className={`nav-item ${activeTab === 'history' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('history'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                    Telemetry Node
                </a>
                <a href="#" className={`nav-item ${activeTab === 'yara' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('yara'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                    Signature Rules
                </a>
                <a href="#" className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`} onClick={(e) => { e.preventDefault(); setActiveTab('settings'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    Platform Settings
                </a>
            </nav>

            <div className="sidebar-footer">
                <div className="node-status" style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className="dot active"></span>
                    <span style={{ fontSize: '11px', color: '#9ca3af', letterSpacing: '1px' }}>{user.toUpperCase()}</span>
                </div>
                <button onClick={handleLogout} style={{
                    width: '100%', padding: '10px', background: 'transparent',
                    border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444',
                    borderRadius: '4px', cursor: 'pointer', fontSize: '11px',
                    letterSpacing: '1px', transition: 'all 0.2s', fontWeight: 'bold'
                }}
                onMouseOver={e => e.target.style.background = 'rgba(239, 68, 68, 0.1)'}
                onMouseOut={e => e.target.style.background = 'transparent'}
                >
                    SECURE LOGOUT
                </button>
            </div>
        </aside>

        <main className="main-content">
            <div style={{ display: activeTab === 'scanner' ? 'contents' : 'none' }}>
              <Scanner
                lastScanResult={lastScanResult}
                setLastScanResult={setLastScanResult}
                lastScanText={lastScanText}
                setLastScanText={setLastScanText}
              />
            </div>
            <div style={{ display: activeTab === 'history' ? 'contents' : 'none' }}>
              <History />
            </div>
            <div style={{ display: activeTab === 'yara' ? 'contents' : 'none' }}>
              <YaraEditor />
            </div>
            <div style={{ display: activeTab === 'settings' ? 'contents' : 'none' }}>
              <Settings />
            </div>
        </main>
      </div>
    </div>
  )
}

export default Dashboard
