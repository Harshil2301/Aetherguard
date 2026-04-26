import { lazy, Suspense } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const StarCanvas = lazy(() => import('../components/Scene3D').then(m => ({ default: m.StarCanvas })));
const HeroSphereCanvas = lazy(() => import('../components/Scene3D').then(m => ({ default: m.HeroSphereCanvas })));

function Envelope({ style }) {
  return (
    <div className="envelope-float absolute" style={style}>
      <svg width="40" height="32" viewBox="0 0 40 32" fill="none">
        <rect x="1" y="1" width="38" height="30" rx="3" stroke="#22d3ee" strokeWidth="1.5" fill="none" opacity="0.2"/>
        <path d="M1 5l19 13L39 5" stroke="#22d3ee" strokeWidth="1.5" opacity="0.2"/>
        <path d="M1 27l13-10M39 27L26 17" stroke="#22d3ee" strokeWidth="1" strokeDasharray="2 2" opacity="0.1"/>
      </svg>
    </div>
  );
}

function ShieldBadge({ style }) {
  return (
    <div className="envelope-float absolute" style={style}>
      <svg width="32" height="36" viewBox="0 0 32 36" fill="none">
        <path d="M16 2L3 8v10c0 9 6 16 13 18 7-2 13-9 13-18V8L16 2z" stroke="#ef4444" strokeWidth="1.5" fill="none" opacity="0.2"/>
        <text x="9" y="22" fontSize="14" fill="#ef4444" opacity="0.3">!</text>
      </svg>
    </div>
  );
}

const stats = [
  { value: '98.7%', label: 'Legitimate Recall', icon: '✅' },
  { value: '82.4K', label: 'Emails Trained', icon: '📧' },
  { value: '90.1%', label: 'Phishing Catch Rate', icon: '🎯' },
  { value: '0%',    label: 'Financial FPs', icon: '🏦' },
];

const features = [
  { icon:'🧠', title:'Semantic ML Engine',    tag:'PHASE 1', desc:'Local SentenceTransformer trained on 82,486 raw emails from the Enron & SpamAssassin honeypots. Engineered for zero false positives.', border:'rgba(59,130,246,0.2)', bg:'rgba(59,130,246,0.05)' },
  { icon:'🔌', title:'Zero-Click Extension',  tag:'SENSOR',  desc:'AetherGuard injects directly into the Gmail DOM. It reads the email in memory and renders a Threat HUD before you even click a link.', border:'rgba(34,197,94,0.2)', bg:'rgba(34,197,94,0.05)' },
  { icon:'🔬', title:'YARA Static Analysis',  tag:'PHASE 2', desc:'Industry-standard YARA rules scan every attachment for obfuscated shellcode, macros, and stealth payloads.', border:'rgba(139,92,246,0.2)', bg:'rgba(139,92,246,0.05)' },
  { icon:'🌐', title:'OTX Threat Intel',      tag:'PHASE 3', desc:'Real-time correlation against VirusTotal and AlienVault OTX for domain reputation and IOC matching.', border:'rgba(34,211,238,0.2)', bg:'rgba(34,211,238,0.05)' },
  { icon:'📧', title:'Email Header Forensics',tag:'CORE',    desc:'Deep SPF, DKIM, and DMARC analysis unmasks spoofed sender domains and rogue relay servers instantly.', border:'rgba(249,115,22,0.2)', bg:'rgba(249,115,22,0.05)' },
  { icon:'⚡', title:'Real-Time SOC Alerts',  tag:'PHASE 4', desc:'Discord webhook fires a live threat card to your security team the moment a high-risk payload is detected.', border:'rgba(239,68,68,0.2)', bg:'rgba(239,68,68,0.05)' },
];

const fadeUp = { hidden:{ opacity:0, y:24 }, show:{ opacity:1, y:0 } };

const NAV_LINK = { color:'#94a3b8', fontSize:14, fontWeight:500, textDecoration:'none', transition:'color 0.2s' };

export default function Landing() {
  return (
    <>
      <Suspense fallback={null}><StarCanvas /></Suspense>
      <main style={{ position:'relative', zIndex:1 }}>

        {/* ── NAVBAR ── */}
        <nav style={{ position:'fixed', top:0, left:0, right:0, zIndex:50, backdropFilter:'blur(24px)', backgroundColor:'rgba(4,12,26,0.85)', borderBottom:'1px solid rgba(255,255,255,0.06)' }}>
          <div style={{ maxWidth:1280, margin:'0 auto', padding:'0 32px', height:68, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
            <div style={{ display:'flex', alignItems:'center', gap:12 }}>
              <div style={{ width:38, height:38, borderRadius:10, background:'linear-gradient(135deg,#22d3ee,#7c3aed)', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 0 20px rgba(34,211,238,0.3)' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L3 7v5c0 5.25 3.75 10.15 9 11.35C17.25 22.15 21 17.25 21 12V7L12 2z"/>
                  <polyline points="9 12 11 14 15 10"/>
                </svg>
              </div>
              <span style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:15, letterSpacing:'0.2em', color:'white' }}>AETHERGUARD</span>
            </div>
            <div style={{ display:'flex', gap:36, alignItems:'center' }}>
              <a href="#features" style={NAV_LINK} onMouseEnter={e=>e.currentTarget.style.color='white'} onMouseLeave={e=>e.currentTarget.style.color='#94a3b8'}>Features</a>
              <Link to="/dashboard" style={NAV_LINK} onMouseEnter={e=>e.currentTarget.style.color='white'} onMouseLeave={e=>e.currentTarget.style.color='#94a3b8'}>Dashboard</Link>
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:12 }}>
              <Link to="/login" style={NAV_LINK}>Sign In</Link>
              <Link to="/login" style={{ padding:'10px 22px', borderRadius:10, fontSize:14, fontWeight:700, background:'linear-gradient(135deg,#22d3ee,#7c3aed)', color:'white', textDecoration:'none', boxShadow:'0 0 20px rgba(34,211,238,0.25)', letterSpacing:'0.05em' }}>Get Started</Link>
            </div>
          </div>
        </nav>

        {/* ── HERO ── */}
        <section style={{ position:'relative', minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', textAlign:'center', paddingTop:68, overflow:'hidden' }}>
          <div style={{ position:'absolute', inset:0, zIndex:0 }}>
            <Suspense fallback={null}><HeroSphereCanvas /></Suspense>
          </div>
          <div style={{ position:'absolute', inset:0, zIndex:1, pointerEvents:'none', background:'radial-gradient(ellipse 75% 65% at 50% 55%, transparent 25%, #040c1a 80%)' }}/>
          <div style={{ position:'absolute', bottom:0, left:0, right:0, height:200, zIndex:1, pointerEvents:'none', background:'linear-gradient(to bottom,transparent,#040c1a)' }}/>
          <Envelope style={{ left:'8%',  bottom:'20%', animationDuration:'9s',  animationDelay:'0s'   }}/>
          <Envelope style={{ left:'18%', bottom:'15%', animationDuration:'13s', animationDelay:'3s'   }}/>
          <Envelope style={{ right:'10%',bottom:'25%', animationDuration:'11s', animationDelay:'1.5s' }}/>
          <Envelope style={{ right:'22%',bottom:'10%', animationDuration:'8s',  animationDelay:'5s'   }}/>
          <ShieldBadge style={{ left:'5%',  top:'30%', animationDuration:'14s', animationDelay:'2s' }}/>
          <ShieldBadge style={{ right:'6%', top:'40%', animationDuration:'10s', animationDelay:'4s' }}/>
          <div style={{ position:'relative', zIndex:2, maxWidth:800, margin:'0 auto', padding:'0 24px', width:'100%' }}>
            <motion.div initial={{ opacity:0, y:16 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.6 }}
              style={{ display:'inline-flex', alignItems:'center', gap:8, padding:'8px 20px', borderRadius:999, background:'rgba(34,211,238,0.08)', border:'1px solid rgba(34,211,238,0.3)', color:'#22d3ee', fontSize:11, fontWeight:700, letterSpacing:'0.15em', textTransform:'uppercase', marginBottom:28 }}>
              <span style={{ width:6, height:6, borderRadius:'50%', background:'#22d3ee', boxShadow:'0 0 8px #22d3ee', animation:'pulse-ring 2s ease-out infinite' }}/>
              Browser-Based AI Phishing Scanner
            </motion.div>
            <motion.h1 initial={{ opacity:0, y:32 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.9, delay:0.1 }}
              style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(42px,5vw,72px)', lineHeight:1.1, margin:'0 0 24px', color:'white' }}>
              Real-Time<br/><span className="gradient-text" style={{ whiteSpace: 'nowrap' }}>Phishing Detection.</span>
            </motion.h1>
            <motion.p initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.8, delay:0.22 }}
              style={{ fontSize:18, lineHeight:1.7, color:'#94a3b8', maxWidth:600, margin:'0 auto 40px' }}>
              AetherGuard integrates with the Gmail DOM to analyze email payloads in real-time. It utilizes a SentenceTransformer model trained on 82,000+ samples, specifically tuned to minimize false positives on legitimate communications.
            </motion.p>
            <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.8, delay:0.34 }}
              style={{ display:'flex', gap:16, justifyContent:'center', flexWrap:'wrap' }}>
              <Link to="/login"
                style={{ padding:'18px 44px', borderRadius:14, fontSize:16, fontWeight:800, background:'linear-gradient(135deg,#22d3ee,#3b82f6,#7c3aed)', color:'white', textDecoration:'none', boxShadow:'0 0 40px rgba(34,211,238,0.3),0 0 80px rgba(124,58,237,0.15)', letterSpacing:'0.06em', transition:'transform 0.2s,box-shadow 0.2s' }}
                onMouseEnter={e=>{ e.currentTarget.style.transform='translateY(-2px)'; e.currentTarget.style.boxShadow='0 0 60px rgba(34,211,238,0.45)'; }}
                onMouseLeave={e=>{ e.currentTarget.style.transform='translateY(0)'; e.currentTarget.style.boxShadow='0 0 40px rgba(34,211,238,0.3),0 0 80px rgba(124,58,237,0.15)'; }}>
                🛡️ ENTERPRISE SSO LOGIN
              </Link>
              <Link to="/dashboard"
                style={{ padding:'18px 36px', borderRadius:14, fontSize:16, fontWeight:600, background:'rgba(255,255,255,0.05)', border:'1px solid rgba(255,255,255,0.12)', color:'white', textDecoration:'none', transition:'background 0.2s' }}
                onMouseEnter={e=>e.currentTarget.style.background='rgba(255,255,255,0.1)'}
                onMouseLeave={e=>e.currentTarget.style.background='rgba(255,255,255,0.05)'}>
                Open Dashboard →
              </Link>
            </motion.div>
            <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.6 }}
              style={{ display:'flex', gap:16, justifyContent:'center', marginTop:36, flexWrap:'wrap' }}>
              {['SPF','DKIM','DMARC','YARA','OTX Intel'].map(b=>(
                <span key={b} style={{ padding:'5px 14px', borderRadius:999, background:'rgba(34,211,238,0.06)', border:'1px solid rgba(34,211,238,0.2)', color:'#67e8f9', fontSize:12, fontWeight:700, letterSpacing:'0.1em' }}>✓ {b}</span>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ── STATS ── */}
        <section style={{ borderTop:'1px solid rgba(255,255,255,0.05)', borderBottom:'1px solid rgba(255,255,255,0.05)', background:'rgba(4,12,26,0.7)', backdropFilter:'blur(12px)', padding:'48px 32px' }}>
          <div style={{ maxWidth:900, margin:'0 auto', display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:32 }}>
            {stats.map((s,i)=>(
              <motion.div key={i} initial="hidden" whileInView="show" variants={fadeUp} transition={{ delay:i*0.08 }} viewport={{ once:true }} style={{ textAlign:'center' }}>
                <div style={{ fontSize:28, marginBottom:6 }}>{s.icon}</div>
                <div style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(28px,4vw,44px)', marginBottom:6, background:'linear-gradient(120deg,#22d3ee,#7c3aed)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent' }}>{s.value}</div>
                <div style={{ fontSize:11, color:'#64748b', letterSpacing:'0.15em', textTransform:'uppercase', fontWeight:600 }}>{s.label}</div>
              </motion.div>
            ))}
          </div>
        </section>

        {/* ── HOW IT WORKS ── */}
        <section style={{ padding:'96px 32px', borderTop:'1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ maxWidth:900, margin:'0 auto' }}>
            <motion.div initial="hidden" whileInView="show" variants={fadeUp} viewport={{ once:true }} style={{ textAlign:'center', marginBottom:64 }}>
              <h2 style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(28px,4vw,48px)', color:'white', margin:'0 0 14px' }}>
                How does it <span className="gradient-text">actually work?</span>
              </h2>
              <p style={{ color:'#64748b', fontSize:16, maxWidth:560, margin:'0 auto' }}>No jargon. Here is exactly what happens the moment you paste a suspicious email or click scan.</p>
            </motion.div>
            <div style={{ display:'flex', flexDirection:'column', gap:0 }}>
              {[
                { step:'01', icon:'🔌', title:'Silently integrates into Gmail', desc:'The AetherGuard extension uses MutationObservers to watch your Gmail inbox. The millisecond you click an email, it intercepts the raw payload before you even read it.' },
                { step:'02', icon:'🧠', title:'An AI reads it like a human would', desc:'Our machine learning model — trained on the Enron & SpamAssassin honeypots — processes the semantics of the email. It intentionally trades a fraction of phishing catch-rate to guarantee zero false positives on legitimate financial emails.' },
                { step:'03', icon:'🔬', title:'Attachments are X-rayed for hidden malware', desc:'If you uploaded a file, our YARA engine scans every byte of it looking for hidden malicious code, dangerous macros (used to silently install viruses), and obfuscated payloads that normal antivirus can miss.' },
                { step:'04', icon:'🌐', title:'Every link is checked against global threat databases', desc:'Any URLs found in the email are checked in real time against VirusTotal (scanned by 70+ antivirus engines) and AlienVault OTX (a global database of known malicious domains). If a link is known-bad anywhere in the world, we catch it.' },
                { step:'05', icon:'📊', title:'You get a clear risk score — 0 to 100', desc:'All four checks are combined into a single risk score. Green (0–40) means it looks safe. Yellow (40–70) means proceed with caution. Red (70–100) means this is very likely a phishing or malware attack — do not click anything.' },
              ].map((item,i)=>(
                <motion.div key={i} initial="hidden" whileInView="show" variants={fadeUp} transition={{ delay:i*0.08 }} viewport={{ once:true }}
                  style={{ display:'flex', gap:28, alignItems:'flex-start', padding:'32px 0', borderBottom: i<4?'1px solid rgba(255,255,255,0.05)':'none' }}>
                  <div style={{ flexShrink:0, width:56, textAlign:'center' }}>
                    <div style={{ fontSize:10, fontWeight:800, color:'#334155', letterSpacing:'0.12em', marginBottom:6 }}>STEP {item.step}</div>
                    <div style={{ fontSize:32 }}>{item.icon}</div>
                  </div>
                  <div>
                    <h3 style={{ fontWeight:700, fontSize:17, color:'white', margin:'0 0 10px' }}>{item.title}</h3>
                    <p style={{ color:'#64748b', fontSize:14, lineHeight:1.8, margin:0 }}>{item.desc}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── BROWSER EXTENSION ── */}
        <section style={{ padding:'80px 32px', borderTop:'1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ maxWidth:1100, margin:'0 auto', display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(340px,1fr))', gap:48, alignItems:'center' }}>
            <motion.div initial="hidden" whileInView="show" variants={fadeUp} viewport={{ once:true }}>
              <div style={{ display:'inline-flex', alignItems:'center', gap:8, padding:'6px 14px', borderRadius:999, background:'rgba(74,222,128,0.08)', border:'1px solid rgba(74,222,128,0.25)', color:'#4ade80', fontSize:11, fontWeight:700, letterSpacing:'0.15em', marginBottom:20 }}>
                🔌 GMAIL DOM INTEGRATION
              </div>
              <h2 style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(26px,3.5vw,40px)', color:'white', margin:'0 0 16px', lineHeight:1.2 }}>
                Real-time threat detection<br/><span className="gradient-text">in the browser</span>
              </h2>
              <p style={{ color:'#64748b', fontSize:15, lineHeight:1.8, marginBottom:24 }}>
                The AetherGuard browser extension embeds into the Gmail DOM. It extracts the raw email payload in memory, evaluates it locally, and renders a Threat HUD directly in the UI.
              </p>
              <div style={{ display:'flex', flexDirection:'column', gap:12, marginBottom:24 }}>
                {['Instant Gmail DOM Interception','Dynamic HUD Badge Injection (SAFE / CRITICAL BREACH)','Context-menu fallback for any other website','Connects to your local AetherGuard ML backend securely'].map((f,i)=>(
                  <div key={i} style={{ display:'flex', gap:10, alignItems:'flex-start', fontSize:14, color:'#94a3b8' }}>
                    <span style={{ color:'#4ade80', flexShrink:0 }}>✓</span>{f}
                  </div>
                ))}
              </div>
              <div style={{ display:'flex', gap:12, flexWrap:'wrap', marginBottom:14 }}>
                <a href="/api/extension/download" style={{ display:'inline-flex', alignItems:'center', gap:8, padding:'12px 22px', borderRadius:10, fontSize:13, fontWeight:700, background:'linear-gradient(135deg,#22d3ee,#7c3aed)', color:'white', textDecoration:'none', boxShadow:'0 0 24px rgba(34,211,238,0.2)', letterSpacing:'0.05em' }}>
                  ⬇ Download for Chrome / Edge
                </a>
              </div>
              <div style={{ padding:'12px 16px', borderRadius:10, background:'rgba(255,193,7,0.06)', border:'1px solid rgba(255,193,7,0.2)', color:'#fbbf24', fontSize:12, lineHeight:1.7 }}>
                <strong>Install steps:</strong> Download the ZIP → Extract it → Open Chrome/Edge → Go to <code style={{ background:'rgba(255,255,255,0.08)', padding:'1px 5px', borderRadius:3 }}>chrome://extensions</code> → Enable "Developer Mode" → Click "Load unpacked" → Select the extracted folder.
              </div>
            </motion.div>
            <motion.div initial="hidden" whileInView="show" variants={fadeUp} transition={{ delay:0.15 }} viewport={{ once:true }}
              style={{ background:'rgba(255,255,255,0.025)', border:'1px solid rgba(255,255,255,0.08)', borderRadius:20, padding:32 }}>
              <div style={{ fontFamily:'monospace', fontSize:13, color:'#64748b', lineHeight:2 }}>
                <div style={{ color:'#334155', marginBottom:12, fontSize:11, letterSpacing:'0.1em' }}>GMAIL DOM INJECTION</div>
                <div style={{ padding:'10px 16px', background:'rgba(255,255,255,0.04)', borderRadius:8, border:'1px solid rgba(255,255,255,0.06)', marginBottom:20 }}>
                  <div style={{ color:'#94a3b8' }}>From: support@paypal-secure-update.com</div>
                  <div style={{ color:'#cbd5e1', fontWeight:700, marginTop:4 }}>Subject: Urgent Account Verification</div>
                </div>
                <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:20, color:'#475569', fontSize:12 }}>
                  <div style={{ flex:1, height:1, background:'rgba(255,255,255,0.06)' }}/>
                  aetherguard injecting HUD badge...
                  <div style={{ flex:1, height:1, background:'rgba(255,255,255,0.06)' }}/>
                </div>
                <div style={{ padding:16, borderRadius:10, background:'linear-gradient(135deg,rgba(239,68,68,0.08),rgba(239,68,68,0.03))', border:'1px solid rgba(239,68,68,0.3)', display:'flex', alignItems:'center', gap:12 }}>
                  <div style={{ width:40, height:40, borderRadius:8, background:'rgba(239,68,68,0.1)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20 }}>🛡️</div>
                  <div>
                    <div style={{ color:'#ef4444', fontWeight:800, fontSize:14 }}>CRITICAL BREACH</div>
                    <div style={{ fontSize:11 }}>ML Confidence: 94%</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── FEATURES GRID ── */}
        <section id="features" style={{ padding:'96px 32px', borderTop:'1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ maxWidth:1200, margin:'0 auto' }}>
            <motion.div initial="hidden" whileInView="show" variants={fadeUp} viewport={{ once:true }} style={{ textAlign:'center', marginBottom:64 }}>
              <h2 style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(32px,4vw,52px)', color:'white', margin:'0 0 16px' }}>
                Defense in <span className="gradient-text">Depth</span>
              </h2>
              <p style={{ color:'#64748b', fontSize:17, maxWidth:520, margin:'0 auto' }}>Every phishing vector covered — from fake headers to malicious attachments.</p>
            </motion.div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(340px,1fr))', gap:24 }}>
              {features.map((f,i)=>(
                <motion.div key={i} initial="hidden" whileInView="show" variants={fadeUp} transition={{ delay:i*0.07 }} viewport={{ once:true }}
                  whileHover={{ y:-6, scale:1.01 }}
                  style={{ padding:28, borderRadius:20, background:f.bg, border:`1px solid ${f.border}`, transition:'transform 0.2s', cursor:'default' }}>
                  <div style={{ display:'flex', alignItems:'center', gap:12, marginBottom:16 }}>
                    <span style={{ fontSize:32 }}>{f.icon}</span>
                    <div>
                      <div style={{ fontSize:10, fontWeight:800, letterSpacing:'0.15em', color:'#22d3ee', marginBottom:4 }}>{f.tag}</div>
                      <h3 style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:700, fontSize:17, color:'white', margin:0 }}>{f.title}</h3>
                    </div>
                  </div>
                  <p style={{ color:'#64748b', fontSize:14, lineHeight:1.7, margin:0 }}>{f.desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ── */}
        <section style={{ padding:'96px 32px' }}>
          <div style={{ maxWidth:720, margin:'0 auto', textAlign:'center' }}>
            <motion.div initial="hidden" whileInView="show" variants={fadeUp} viewport={{ once:true }}
              style={{ padding:'64px 48px', borderRadius:28, background:'linear-gradient(135deg,rgba(34,211,238,0.06),rgba(124,58,237,0.06))', border:'1px solid rgba(34,211,238,0.15)', boxShadow:'0 0 80px rgba(34,211,238,0.06)' }}>
              <div style={{ fontSize:48, marginBottom:16 }}>📧</div>
              <h2 style={{ fontFamily:'Space Grotesk,sans-serif', fontWeight:900, fontSize:'clamp(28px,4vw,44px)', color:'white', margin:'0 0 16px' }}>
                Ready to activate your <span className="gradient-text">node?</span>
              </h2>
              <p style={{ color:'#64748b', fontSize:16, margin:'0 0 36px' }}>Free forever for individuals. Pro plans from ₹2,499/month.</p>
              <div style={{ display:'flex', gap:16, justifyContent:'center', flexWrap:'wrap' }}>
                <Link to="/login" style={{ padding:'18px 44px', borderRadius:14, fontSize:16, fontWeight:800, background:'linear-gradient(135deg,#22d3ee,#3b82f6,#7c3aed)', color:'white', textDecoration:'none', boxShadow:'0 0 40px rgba(34,211,238,0.25)', letterSpacing:'0.06em' }}>
                  🛡️ ENTERPRISE SSO LOGIN
                </Link>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ── FOOTER ── */}
        <footer style={{ borderTop:'1px solid rgba(255,255,255,0.05)', padding:'28px 32px', textAlign:'center', fontSize:13, color:'#334155' }}>
          © 2026 AetherGuard — AI-Powered Email Security · Built with React · Vite · Three.js · Flask
        </footer>

      </main>
    </>
  );
}
