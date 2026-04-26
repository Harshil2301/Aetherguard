import { useState, useEffect } from 'react';

const API = '/api';

export default function YaraEditor() {
  const [content, setContent] = useState('');
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [isLoading, setIsLoading] = useState(true);

  const getToken = () => localStorage.getItem('aether_token') || '';

  useEffect(() => {
    fetchYaraRules();
  }, []);

  const fetchYaraRules = async () => {
    try {
      const res = await fetch(`${API}/yara`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await res.json();
      if (res.ok) {
        setContent(data.content || '');
      } else {
        setStatus({ type: 'error', msg: data.error || 'Failed to load rules.' });
      }
    } catch (e) {
      setStatus({ type: 'error', msg: 'Network error loading YARA rules.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setStatus({ type: 'info', msg: 'Compiling rules...' });
    try {
      const res = await fetch(`${API}/yara`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ content })
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: 'success', msg: data.message });
      } else {
        setStatus({ type: 'error', msg: data.error || 'Failed to compile rules.' });
      }
    } catch (e) {
      setStatus({ type: 'error', msg: 'Network error saving YARA rules.' });
    }
  };

  return (
    <div className="view-panel active-view">
      <header className="topbar">
        <div className="hero-text">
          <h1>YARA Signature Editor</h1>
          <p>Define custom static analysis rules for immediate deployment.</p>
        </div>
      </header>

      <div className="card glass-panel" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 160px)' }}>
        <div className="panel-header align-between">
          <h3>custom_rules.yar</h3>
          {status.msg && (
            <span style={{
              fontSize: '11px',
              padding: '4px 8px',
              borderRadius: '4px',
              fontWeight: 'bold',
              background: status.type === 'error' ? 'rgba(239,68,68,0.1)' : status.type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(34,211,238,0.1)',
              color: status.type === 'error' ? '#ef4444' : status.type === 'success' ? '#10b981' : '#22d3ee',
              border: `1px solid ${status.type === 'error' ? '#ef4444' : status.type === 'success' ? '#10b981' : '#22d3ee'}30`
            }}>
              {status.msg}
            </span>
          )}
        </div>

        {isLoading ? (
          <div className="scanning-overlay" style={{ position: 'relative', flex: 1, minHeight: '300px' }}>
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            <textarea
              className="hacker-textarea"
              style={{ flex: 1, margin: '0', fontFamily: 'monospace', fontSize: '13px', lineHeight: '1.4', whiteSpace: 'pre' }}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              spellCheck="false"
              placeholder="// Write your custom YARA rules here..."
            />
            <div style={{ padding: '15px 0 0', display: 'flex', justifyContent: 'flex-end' }}>
              <button className="web3-btn primary-btn" onClick={handleSave} style={{ width: 'auto', padding: '0 30px' }}>
                <span className="btn-text">COMPILE & DEPLOY</span>
                <div className="btn-glow"></div>
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
