import React, { useState } from 'react';

export default function Login({ setToken }) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();
            
            if (res.ok && data.token) {
                localStorage.setItem('aether_token', data.token);
                localStorage.setItem('aether_user', data.username);
                setToken(data.token);
            } else {
                setError(data.error || 'Authentication Failed');
            }
        } catch (err) {
            setError('Network Error: API Offline');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', 
            background: '#0b0e14', color: '#d1d5db', fontFamily: 'Inter, sans-serif'
        }}>
            <div className="glow-orb orb-1"></div>
            <div className="glow-orb orb-2"></div>
            
            <div className="glass-panel" style={{
                width: '400px', padding: '40px', borderRadius: '16px', zIndex: 10,
                border: '1px solid rgba(255, 255, 255, 0.05)',
                boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
            }}>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                    <div className="logo-box" style={{ width: '52px', height: '52px', margin: '0 auto 12px auto', borderRadius: '14px', background: 'linear-gradient(135deg, #22d3ee, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 24px rgba(34,211,238,0.35)' }}>
                        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/>
                            <polyline points="9 12 11 14 15 10"/>
                        </svg>
                    </div>
                    <h2 style={{ fontSize: '24px', letterSpacing: '4px', margin: 0, 
                        background: 'linear-gradient(to right, #3b82f6, #a855f7)', WebkitBackgroundClip: 'text', color: 'transparent'
                    }}>
                        AETHERGUARD
                    </h2>
                    <p style={{ fontSize: '11px', color: '#6b7280', marginTop: '5px', letterSpacing: '2px' }}>
                        SECURE IDENTITY NODE
                    </p>
                </div>

                {error && (
                    <div style={{
                        background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', 
                        color: '#fca5a5', padding: '10px', borderRadius: '4px', fontSize: '13px', 
                        marginBottom: '20px', textAlign: 'center'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                    <div>
                        <label style={{ display: 'block', fontSize: '11px', color: '#9ca3af', marginBottom: '5px', letterSpacing: '1px' }}>ADMIN ID</label>
                        <input type="text" value={username} onChange={e => setUsername(e.target.value)} 
                            style={{
                                width: '100%', padding: '12px', background: 'rgba(0,0,0,0.3)', 
                                border: '1px solid rgba(255,255,255,0.1)', color: '#fff', 
                                borderRadius: '6px', boxSizing: 'border-box', outline: 'none'
                            }} 
                            required 
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '11px', color: '#9ca3af', marginBottom: '5px', letterSpacing: '1px' }}>BIOMETRIC KEY (PASSWORD)</label>
                        <input type="password" value={password} onChange={e => setPassword(e.target.value)} 
                            style={{
                                width: '100%', padding: '12px', background: 'rgba(0,0,0,0.3)', 
                                border: '1px solid rgba(255,255,255,0.1)', color: '#fff', 
                                borderRadius: '6px', boxSizing: 'border-box', outline: 'none'
                            }} 
                            required 
                        />
                    </div>
                    
                    <button type="submit" disabled={loading} style={{
                        marginTop: '10px', padding: '14px', background: 'linear-gradient(135deg, #3b82f6, #6366f1)',
                        color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', letterSpacing: '1px',
                        cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.7 : 1
                    }}>
                        {loading ? 'AUTHENTICATING...' : 'ESTABLISH SECURE LINK'}
                    </button>
                    <p style={{ textAlign: 'center', fontSize: '11px', color: '#4b5563', marginTop: '10px' }}>
                        Default Admin is securely provisioned in SQLite.
                    </p>
                </form>
            </div>
        </div>
    );
}
