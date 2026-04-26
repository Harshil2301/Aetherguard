import AuthForm from '../components/AuthForm';

export default function Login() {
  return (
    <div style={{
      minHeight: '100vh',
      width: '100%',
      background: '#040c1a',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Ambient glow orbs */}
      <div style={{
        position: 'absolute', top: '15%', left: '15%',
        width: 480, height: 480,
        background: 'radial-gradient(circle, rgba(34,211,238,0.12) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none',
      }}/>
      <div style={{
        position: 'absolute', bottom: '10%', right: '10%',
        width: 560, height: 560,
        background: 'radial-gradient(circle, rgba(124,58,237,0.12) 0%, transparent 70%)',
        borderRadius: '50%', pointerEvents: 'none',
      }}/>
      <div style={{
        position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
        width: 800, height: 800,
        background: 'radial-gradient(circle, rgba(59,130,246,0.05) 0%, transparent 60%)',
        borderRadius: '50%', pointerEvents: 'none',
      }}/>

      {/* Floating particles */}
      {[...Array(6)].map((_, i) => (
        <div key={i} style={{
          position: 'absolute',
          width: i % 2 === 0 ? 3 : 2,
          height: i % 2 === 0 ? 3 : 2,
          borderRadius: '50%',
          background: i % 3 === 0 ? '#22d3ee' : i % 3 === 1 ? '#7c3aed' : '#3b82f6',
          opacity: 0.4,
          top: `${15 + i * 14}%`,
          left: `${8 + i * 15}%`,
          animation: `float-up ${8 + i * 2}s linear infinite`,
          animationDelay: `${i * 1.2}s`,
          pointerEvents: 'none',
        }}/>
      ))}

      {/* Auth card — full width on mobile, fixed on desktop */}
      <div style={{ position: 'relative', zIndex: 10, width: '100%', maxWidth: 480, padding: '24px 20px' }}>
        <AuthForm />
      </div>
    </div>
  );
}
