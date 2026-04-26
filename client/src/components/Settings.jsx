import { useState, useEffect } from 'react';

const API = '/api';

export default function Settings() {
  const [profile, setProfile] = useState(null);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [status, setStatus] = useState({ type: '', msg: '' });
  const [isLoading, setIsLoading] = useState(true);

  const getToken = () => localStorage.getItem('aether_token') || '';

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await fetch(`${API}/profile`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await res.json();
      if (res.ok) {
        setProfile(data);
        setWebhookUrl(data.webhook_url || '');
      }
    } catch (e) {
      console.error("Failed to load profile", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveWebhook = async () => {
    setStatus({ type: 'info', msg: 'Saving...' });
    try {
      const res = await fetch(`${API}/settings/webhook`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({ webhook_url: webhookUrl })
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: 'success', msg: 'Webhook updated successfully.' });
        setProfile({ ...profile, webhook_url: data.webhook_url });
      } else {
        setStatus({ type: 'error', msg: data.error || 'Failed to update.' });
      }
    } catch (e) {
      setStatus({ type: 'error', msg: 'Network error.' });
    }
  };

  const handleGenerateKey = async () => {
    if (!window.confirm("Generating a new API key will invalidate your old one. Continue?")) return;
    
    setStatus({ type: 'info', msg: 'Generating...' });
    try {
      const res = await fetch(`${API}/settings/apikey`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: 'success', msg: 'API Key generated successfully.' });
        setProfile({ ...profile, api_key: data.api_key });
      } else {
        setStatus({ type: 'error', msg: data.error || 'Failed to generate key.' });
      }
    } catch (e) {
      setStatus({ type: 'error', msg: 'Network error.' });
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setStatus({ type: 'success', msg: 'Copied to clipboard!' });
    setTimeout(() => setStatus({ type: '', msg: '' }), 3000);
  };

  if (isLoading) {
    return (
      <div className="view-panel active-view">
        <div className="scanning-overlay"><div className="spinner"></div></div>
      </div>
    );
  }

  return (
    <div className="view-panel active-view">
      <header className="topbar">
        <div className="hero-text">
          <h1>Platform Settings</h1>
          <p>Configure integrations and programmatic access credentials.</p>
        </div>
      </header>

      <div className="card glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="panel-header align-between">
          <h3>Integrations & API</h3>
          {status.msg && (
            <span style={{
              fontSize: '11px', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold',
              background: status.type === 'error' ? 'rgba(239,68,68,0.1)' : status.type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(34,211,238,0.1)',
              color: status.type === 'error' ? '#ef4444' : status.type === 'success' ? '#10b981' : '#22d3ee',
              border: `1px solid ${status.type === 'error' ? '#ef4444' : status.type === 'success' ? '#10b981' : '#22d3ee'}30`
            }}>
              {status.msg}
            </span>
          )}
        </div>

        <div style={{ marginTop: '20px' }}>
          <div className="metric-block" style={{ display: 'block', marginBottom: '20px' }}>
            <h5><span className="icon">🔑</span> API Key Management</h5>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '15px' }}>
              Use this key to authenticate external scripts or CI/CD pipelines with the AetherGuard API. Pass it via the <code>X-API-Key</code> header.
            </p>
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                value={profile?.api_key || 'No API key generated yet.'} 
                readOnly 
                className="hacker-textarea"
                style={{ flex: 1, padding: '10px', margin: 0, height: 'auto', minHeight: 'auto', color: profile?.api_key ? '#22d3ee' : '#64748b' }}
              />
              <button 
                className="web3-btn primary-btn" 
                onClick={handleGenerateKey}
                style={{ width: 'auto', padding: '10px 20px', minHeight: 'auto' }}>
                GENERATE NEW KEY
              </button>
              {profile?.api_key && (
                <button 
                  className="web3-btn secondary-btn" 
                  onClick={() => copyToClipboard(profile.api_key)}
                  style={{ width: 'auto', padding: '10px 20px', minHeight: 'auto' }}>
                  COPY
                </button>
              )}
            </div>
          </div>

          <div className="metric-block" style={{ display: 'block' }}>
            <h5><span className="icon">🔔</span> Webhook Alerts</h5>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '15px' }}>
              Receive real-time notifications in Discord or Slack when a high-risk payload is detected (Score &ge; 70).
            </p>
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input 
                type="text" 
                placeholder="https://discord.com/api/webhooks/..."
                value={webhookUrl} 
                onChange={(e) => setWebhookUrl(e.target.value)}
                className="hacker-textarea"
                style={{ flex: 1, padding: '10px', margin: 0, height: 'auto', minHeight: 'auto' }}
              />
              <button 
                className="web3-btn primary-btn" 
                onClick={handleSaveWebhook}
                style={{ width: 'auto', padding: '10px 20px', minHeight: 'auto' }}>
                SAVE WEBHOOK
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
