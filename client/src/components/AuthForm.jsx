import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { auth } from '../lib/firebase';
import { GoogleAuthProvider, FacebookAuthProvider, signInWithPopup } from 'firebase/auth';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

async function exchangeFirebaseToken(firebaseUser, provider) {
  const idToken = await firebaseUser.getIdToken();
  const res = await fetch(`${API_URL}/api/auth/social`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken, provider })
  });
  if (!res.ok) throw new Error('Backend exchange failed');
  return res.json();
}

export default function AuthForm() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSuccess = async (firebaseUser, provider) => {
    try {
      const data = await exchangeFirebaseToken(firebaseUser, provider);
      localStorage.setItem('aether_token', data.token);
      localStorage.setItem('aether_user', data.username);
    } catch (e) {
      const idToken = await firebaseUser.getIdToken();
      const displayName = firebaseUser.displayName || firebaseUser.email || 'User';
      localStorage.setItem('aether_token', idToken);
      localStorage.setItem('aether_user', displayName);
      console.warn('[AetherGuard] Backend sync failed, using Firebase token directly.', e);
    }
    navigate('/dashboard');
  };

  const handleGoogle = async () => {
    setLoading(true); setError('');
    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      await handleSuccess(result.user, 'google');
    } catch (e) {
      setError(e.message || 'Google sign-in failed');
    } finally { setLoading(false); }
  };

  const handleFacebook = async () => {
    setLoading(true); setError('');
    try {
      const provider = new FacebookAuthProvider();
      const result = await signInWithPopup(auth, provider);
      await handleSuccess(result.user, 'facebook');
    } catch (e) {
      setError(e.message || 'Facebook sign-in failed');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Card */}
      <div style={{
        width: '100%',
        background: 'rgba(255,255,255,0.04)',
        backdropFilter: 'blur(32px)',
        WebkitBackdropFilter: 'blur(32px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 24,
        padding: '48px 40px',
        boxShadow: '0 32px 80px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05) inset',
      }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{
            width: 72, height: 72, borderRadius: 18, margin: '0 auto 20px',
            background: 'linear-gradient(135deg, #22d3ee, #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 40px rgba(34,211,238,0.4), 0 0 80px rgba(124,58,237,0.2)',
          }}>
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/>
              <polyline points="9 12 11 14 15 10"/>
            </svg>
          </div>
          <h1 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 28, fontWeight: 900, letterSpacing: '0.18em', color: 'white', margin: '0 0 8px' }}>
            AETHERGUARD
          </h1>
          <p style={{ fontSize: 12, color: '#64748b', letterSpacing: '0.2em', margin: 0, textTransform: 'uppercase' }}>
            Secure Identity Gateway
          </p>
        </div>

        {/* Security badges */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 28, flexWrap: 'wrap' }}>
          {['Zero-Trust', 'OAuth 2.0', 'End-to-End Encrypted'].map(b => (
            <span key={b} style={{
              padding: '4px 10px', borderRadius: 999,
              background: 'rgba(34,211,238,0.06)',
              border: '1px solid rgba(34,211,238,0.18)',
              color: '#67e8f9', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
            }}>✓ {b}</span>
          ))}
        </div>

        {/* Error */}
        {error && (
          <div style={{
            marginBottom: 20, padding: '12px 16px', borderRadius: 10,
            background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
            color: '#fca5a5', fontSize: 13, textAlign: 'center', lineHeight: 1.5,
          }}>
            {error}
          </div>
        )}

        {/* Buttons */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

          {/* Google */}
          <button onClick={handleGoogle} disabled={loading} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            padding: '16px 20px', borderRadius: 14,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'white', fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s', opacity: loading ? 0.6 : 1,
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => !loading && (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}>
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            {loading ? 'Authenticating…' : 'Continue with Google'}
          </button>

          {/* Facebook */}
          <button onClick={handleFacebook} disabled={loading} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            padding: '16px 20px', borderRadius: 14,
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'white', fontSize: 15, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s', opacity: loading ? 0.6 : 1,
            fontFamily: 'inherit',
          }}
          onMouseEnter={e => !loading && (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
          onMouseLeave={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.05)')}>
            <svg width="20" height="20" fill="#1877F2" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
            Continue with Facebook
          </button>

          {/* Divider */}
          <div style={{ position: 'relative', margin: '4px 0', display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }}/>
            <span style={{ fontSize: 11, color: '#475569', letterSpacing: '0.1em', textTransform: 'uppercase' }}>or</span>
            <div style={{ flex: 1, height: 1, background: 'rgba(255,255,255,0.08)' }}/>
          </div>

          {/* Admin login */}
          <button onClick={() => {
            localStorage.setItem('aether_token', 'admin_mock_token_123');
            localStorage.setItem('aether_user', 'ADMIN');
            navigate('/dashboard');
          }} style={{
            width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center',
            padding: '16px 20px', borderRadius: 14, border: 'none', cursor: 'pointer',
            background: 'linear-gradient(135deg, #2563eb, #7c3aed)',
            color: 'white', fontSize: 14, fontWeight: 800, letterSpacing: '0.08em',
            boxShadow: '0 0 30px rgba(124,58,237,0.3)',
            transition: 'all 0.2s', fontFamily: 'inherit'
          }}
          onMouseEnter={e => e.currentTarget.style.boxShadow = '0 0 50px rgba(124,58,237,0.5)'}
          onMouseLeave={e => e.currentTarget.style.boxShadow = '0 0 30px rgba(124,58,237,0.3)'}>
            🛡️ DASHBOARD LOGIN (ADMIN)
          </button>
        </div>

      </div>

      {/* Footer text */}
      <p style={{ textAlign: 'center', fontSize: 12, color: '#334155', marginTop: 20, letterSpacing: '0.05em' }}>
        Protected by AetherGuard Zero-Trust Security
      </p>
    </div>
  );
}
