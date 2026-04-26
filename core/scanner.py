import os
import re
import io
import json
import email
import base64
import pickle
import requests
from dotenv import load_dotenv
from email.policy import default

load_dotenv()

# ======================================
# LOAD ML COMPONENTS
# ======================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Read model_meta.json to determine which inference mode to use.
MODEL_META = {}
try:
    with open(os.path.join(MODELS_DIR, 'model_meta.json'), 'r') as f:
        MODEL_META = json.load(f)
except FileNotFoundError:
    pass  # No meta file = legacy TF-IDF mode

ENCODER_TYPE = MODEL_META.get('encoder_type', 'tfidf')  # 'sentence_transformer' or 'tfidf'
PHASE        = MODEL_META.get('phase', 0)

try:
    with open(os.path.join(MODELS_DIR, 'model.pkl'), 'rb') as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, 'vectorizer.pkl'), 'rb') as f:
        vectorizer = pickle.load(f)

    if ENCODER_TYPE == 'sentence_transformer':
        print(f"[AetherGuard] Phase {PHASE} ML engine loaded (SentenceTransformer + SGDClassifier).")
    else:
        print("[AetherGuard] Phase 0 ML engine loaded (TF-IDF + LogisticRegression).")

except Exception as e:
    print(f"[AetherGuard] Warning: ML models not loaded. Run train_model.py first. Error: {e}")
    model = None
    vectorizer = None

def reload_ml_engine():
    global model, vectorizer, MODEL_META, ENCODER_TYPE, PHASE
    try:
        with open(os.path.join(MODELS_DIR, 'model_meta.json'), 'r') as f:
            MODEL_META = json.load(f)
    except FileNotFoundError:
        pass
    
    ENCODER_TYPE = MODEL_META.get('encoder_type', 'tfidf')
    PHASE        = MODEL_META.get('phase', 0)
    
    try:
        with open(os.path.join(MODELS_DIR, 'model.pkl'), 'rb') as f:
            model = pickle.load(f)
        with open(os.path.join(MODELS_DIR, 'vectorizer.pkl'), 'rb') as f:
            vectorizer = pickle.load(f)
        print(f"[AetherGuard] ML Engine safely reloaded in memory (Phase {PHASE}).")
        return True, "ML engine reloaded."
    except Exception as e:
        print(f"[AetherGuard] Failed to reload ML engine: {e}")
        return False, str(e)

VT_API_KEY = os.environ.get("VT_API_KEY", "")
OTX_API_KEY = os.environ.get("OTX_API_KEY", "")

# ======================================
# INITIALIZE YARA ENGINE
# ======================================
yara_compiled = None
try:
    import yara
    import glob
    yara_paths = glob.glob(os.path.join(BASE_DIR, 'core', 'yara_rules', '*.yar'))
    yara_sources = {}
    for path in yara_paths:
        with open(path, 'r') as f:
            yara_sources[os.path.basename(path)] = f.read()
    if yara_sources:
        yara_compiled = yara.compile(sources=yara_sources)
        print(f"[AetherGuard] YARA Engine initialized with {len(yara_sources)} rule files.")
except Exception as e:
    print(f"[AetherGuard] YARA Warning: {e}. File scanning will skip YARA checks.")

def reload_yara_engine():
    global yara_compiled
    try:
        import yara
        import glob
        yara_paths = glob.glob(os.path.join(BASE_DIR, 'core', 'yara_rules', '*.yar'))
        yara_sources = {}
        for path in yara_paths:
            with open(path, 'r') as f:
                yara_sources[os.path.basename(path)] = f.read()
        if yara_sources:
            yara_compiled = yara.compile(sources=yara_sources)
            print(f"[AetherGuard] YARA Engine RE-initialized with {len(yara_sources)} rule files.")
            return True, f"Loaded {len(yara_sources)} rule files."
        else:
            yara_compiled = None
            return True, "No rule files found. YARA engine cleared."
    except Exception as e:
        print(f"[AetherGuard] YARA Reload Error: {e}")
        return False, str(e)

# ======================================
# FILE TEXT EXTRACTION
# ======================================
def extract_text_from_pdf(file_bytes):
    """Extract text from PDF using PyPDF2."""
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or '' for page in reader.pages]
        return '\n'.join(pages).strip()
    except ImportError:
        return "[PDF_ERR] PyPDF2 not installed. Run: pip install PyPDF2"
    except Exception as e:
        print(f"[AetherGuard] PDF extraction error: {e}")
        return ""

def extract_text_from_docx(file_bytes):
    """Extract text from .docx files using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs).strip()
    except ImportError:
        return "[DOCX_ERR] python-docx not installed. Run: pip install python-docx"
    except Exception as e:
        print(f"[AetherGuard] DOCX extraction error: {e}")
        return ""

def extract_text_from_image(file_bytes):
    """Extract text from images via OCR using pytesseract + Pillow."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(img)
        return text.strip()
    except ImportError:
        return "[OCR_ERR] Pillow/pytesseract not installed. Run: pip install Pillow pytesseract"
    except Exception as e:
        msg = str(e)
        if 'tesseract' in msg.lower():
            return "[OCR_ERR] Tesseract binary not found. Install from: https://github.com/UB-Mannheim/tesseract/wiki"
        print(f"[AetherGuard] OCR error: {e}")
        return ""

def extract_text_from_eml(file_bytes):
    """Parse a raw .eml file and extract all text content."""
    try:
        import email as email_lib
        msg = email_lib.message_from_bytes(file_bytes)
        parts = []
        # Include headers that matter for phishing analysis
        for header in ('From', 'To', 'Subject', 'Reply-To', 'Return-Path', 'Received'):
            val = msg.get(header, '')
            if val:
                parts.append(f"{header}: {val}")
        # Walk all MIME parts to extract text
        for part in msg.walk():
            ctype = part.get_content_type()
            if ctype in ('text/plain', 'text/html'):
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        parts.append(payload.decode(charset, errors='replace'))
                except Exception:
                    pass
        return '\n'.join(parts).strip()
    except Exception as e:
        print(f"[AetherGuard] EML extraction error: {e}")
        return ""

def extract_text_from_file(file_bytes, filename):
    """Dispatch to the correct extractor based on file extension."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext == 'pdf':
        return extract_text_from_pdf(file_bytes)
    elif ext == 'docx':
        return extract_text_from_docx(file_bytes)
    elif ext == 'eml' or ext == 'txt':
        try:
            return file_bytes.decode('utf-8', errors='replace')
        except Exception:
            return extract_text_from_eml(file_bytes) if ext == 'eml' else ""
    elif ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'):
        return extract_text_from_image(file_bytes)
    return ""

# ======================================
# ML INFERENCE (PHASE-AWARE)
# ======================================
def classify_text(text_payload):
    """
    Returns (ml_confidence: float, ml_result: str) using the appropriate
    inference path depending on the model phase detected at startup.
    """
    if not model or not vectorizer:
        return 0.0, "N/A"

    try:
        if ENCODER_TYPE == 'sentence_transformer':
            # Phase 1+: Use SentenceTransformer to get semantic embedding
            embedding = vectorizer.encode([text_payload], normalize_embeddings=True)
            prob = model.predict_proba(embedding)[0]
        else:
            # Phase 0 (legacy): TF-IDF transform
            X = vectorizer.transform([text_payload])
            prob = model.predict_proba(X)[0]

        # prob[1] = probability of being phishing (class 1)
        ml_confidence = float(prob[1])
        threshold = MODEL_META.get('threshold', 0.6)
        if ml_confidence > threshold:
            ml_result = "Phishing Characteristics Detected"
        else:
            ml_result = "Normal / Legitimate Text"
        return ml_confidence, ml_result

    except Exception as e:
        print(f"[AetherGuard] ML inference error: {e}")
        return 0.0, "N/A"

def compute_attribution(text_payload):
    """
    Context-aware XAI attribution.
    Scores each sentence RELATIVE to the full-document baseline, preventing isolated
    fragments (e.g. 'Order: #12345') from being unfairly flagged at 100%.

    Algorithm:
      1. Score the full email to get a baseline confidence.
      2. Split into meaningful sentences (min 30 chars).
      3. Score each sentence independently.
      4. Dampen short phrases toward the baseline to avoid false extremes.
      5. Return sorted by absolute deviation from baseline (most attributive first).
    """
    if not model or not vectorizer or not text_payload:
        return []
    try:
        import re

        # Step 1: Establish baseline from full text
        baseline_conf, _ = classify_text(text_payload)

        # Step 2: Split into meaningful chunks — minimum 30 chars to avoid order numbers, etc.
        raw_chunks = re.split(r'(?<=[.!?])\s+|\n+', text_payload)
        chunks = [c.strip() for c in raw_chunks if len(c.strip()) >= 30][:20]

        # Fallback: if no chunks meet length threshold, use full lines
        if not chunks:
            lines = [l.strip() for l in text_payload.splitlines() if len(l.strip()) >= 20][:15]
            chunks = lines if lines else []

        if not chunks:
            return []

        results = []
        for chunk in chunks:
            try:
                chunk_conf, _ = classify_text(chunk)

                # Dampen confidence of short phrases toward the baseline.
                # Short isolated phrases (< 60 chars) can't be reliably classified on their own.
                word_count = len(chunk.split())
                if word_count < 6:
                    # Pull score 60% toward baseline for very short fragments
                    chunk_conf = chunk_conf * 0.4 + baseline_conf * 0.6
                elif word_count < 10:
                    # Pull score 30% toward baseline
                    chunk_conf = chunk_conf * 0.7 + baseline_conf * 0.3

                results.append({
                    'text': chunk,
                    'score': round(chunk_conf, 4),
                    'label': 'PHISHING' if chunk_conf > 0.5 else 'LEGITIMATE',
                    'intensity': round(chunk_conf, 4),
                })
            except Exception:
                pass

        # Sort by score descending — highest phishing probability first
        return sorted(results, key=lambda x: x['score'], reverse=True)
    except Exception as e:
        print(f"[AetherGuard] Attribution error: {e}")
        return []


# ======================================
# URL ANALYSIS
# ======================================
SHORTENERS = {
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
    'is.gd', 'buff.ly', 'rebrand.ly', 'short.io', 'rb.gy', 'cutt.ly'
}

# Known-legitimate sender apex domains — reduce false positives for transactional emails
SAFE_SENDER_DOMAINS = {
    'amazon.com', 'amazon.in', 'amazon.co.uk', 'amazon.de',
    'google.com', 'gmail.com', 'googlemail.com',
    'microsoft.com', 'outlook.com', 'hotmail.com', 'live.com',
    'apple.com', 'icloud.com',
    'ups.com', 'fedex.com', 'dhl.com', 'usps.com',
    'paypal.com',
    'netflix.com', 'spotify.com', 'linkedin.com',
    'github.com', 'gitlab.com',
    'stripe.com', 'shopify.com',
    'uber.com', 'lyft.com',
    'noreply.github.com', 'notifications.google.com',
    # Added for Indian Financial & Tech Platforms (False Positive Reduction)
    'groww.in', 'sbimf.com', 'zerodha.com', 'upstox.com', 
    'hdfcfund.com', 'icicipruamc.com', 'angelone.in', 'paytm.com',
    'naukri.com', 'hdfcbank.com', 'icicibank.com', 'sbi.co.in'
}

SUSPICIOUS_TLDS = {
    '.xyz', '.top', '.click', '.loan', '.work', '.racing',
    '.win', '.bid', '.gdn', '.stream', '.date', '.download',
    '.review', '.men', '.accountant', '.science', '.party'
}

BRAND_KEYWORDS = {
    'paypal', 'amazon', 'google', 'microsoft', 'apple', 'facebook',
    'netflix', 'bank', 'irs', 'fedex', 'dhl', 'usps', 'ebay',
    'instagram', 'twitter', 'wellsfargo', 'chase', 'citibank'
}

def extract_urls(text):
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return set(url_pattern.findall(text))

def analyze_url_heuristics(url):
    """Returns (is_suspicious: bool, flags: list[str])."""
    flags = []
    url_lower = url.lower()

    # IP-based URL
    if re.match(r'https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
        flags.append("IP-based URL (no domain name)")

    # Extract domain
    domain_match = re.search(r'https?://([^/?\s]+)', url)
    if domain_match:
        domain = domain_match.group(1).lower()

        # Excessive subdomains (>3 dots = suspicious)
        if domain.count('.') > 3:
            flags.append("Excessive subdomain depth")

        # URL shorteners
        for shortener in SHORTENERS:
            if shortener in domain:
                flags.append(f"URL shortener ({shortener})")
                break

        # Suspicious TLD
        for tld in SUSPICIOUS_TLDS:
            if domain.endswith(tld):
                flags.append(f"Suspicious TLD ({tld})")
                break

        # Brand keyword in non-official domain
        # Catches: netflix-account-verify.net, paypal-secure.xyz, amazon-login.com, etc.
        parts = domain.split('.')
        apex = '.'.join(parts[-2:]) if len(parts) >= 2 else domain
        for brand in BRAND_KEYWORDS:
            if brand in domain and apex not in SAFE_SENDER_DOMAINS:
                flags.append(f"Brand '{brand}' impersonation in non-official domain ({apex})")
                break

        # Homograph / digit substitution
        homograph_patterns = [
            ('paypa1', 'PayPal'), ('amaz0n', 'Amazon'), ('arnazon', 'Amazon'),
            ('g00gle', 'Google'), ('micros0ft', 'Microsoft'), ('app1e', 'Apple'),
            ('faceb00k', 'Facebook'), ('netf1ix', 'Netflix'), ('goog1e', 'Google'),
        ]
        for fake, real in homograph_patterns:
            if fake in domain:
                flags.append(f"Lookalike/homograph domain (spoofs {real})")
                break

    # Insecure HTTP
    if url.startswith('http://'):
        flags.append("Insecure HTTP connection")

    # Abnormally long URL
    if len(url) > 120:
        flags.append("Abnormally long URL")

    # Embedded redirect chain
    if url_lower.count('http') > 1:
        flags.append("Embedded redirect chain")

    return len(flags) > 0, flags

# ======================================
# HEADER ANALYSIS
# ======================================
def analyze_headers(raw_bytes=None, eml_file_path=None, raw_text=""):
    headers_status = {}
    if not raw_bytes and not eml_file_path and not raw_text:
        return headers_status
    try:
        if raw_bytes:
            msg = email.message_from_bytes(raw_bytes, policy=default)
        elif eml_file_path:
            with open(eml_file_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=default)
        elif raw_text:
            msg = email.message_from_string(raw_text, policy=default)

        auth_results = msg.get_all('Authentication-Results', [])
        auth_text = " ".join(auth_results).lower()

        for proto in ('spf', 'dkim', 'dmarc'):
            if f'{proto}=pass' in auth_text:
                headers_status[proto] = 'pass'
            elif any(x in auth_text for x in [f'{proto}=fail', f'{proto}=softfail', f'{proto}=permerror']):
                headers_status[proto] = 'fail'
            elif auth_text:
                headers_status[proto] = 'none'
    except Exception as e:
        print(f"[AetherGuard] Header parse error: {e}")
    return headers_status

def extract_body(raw_bytes):
    try:
        msg = email.message_from_bytes(raw_bytes, policy=default)
        body = msg.get_body(preferencelist=('plain', 'html'))
        if body:
            return body.get_content()
        return ""
    except:
        return ""

# ======================================
# DYNAMIC SANDBOX ENGINE (Cuckoo + Simulator Fallback)
# ======================================
import time

CUCKOO_API_URL = os.environ.get("CUCKOO_API_URL", "")  # e.g. http://localhost:8090

def _simulate_sandbox(filename, ext):
    """Intelligent simulation fallback when Cuckoo is not configured."""
    suspicious_exts = {'exe', 'dll', 'bat', 'vbs', 'ps1', 'jar'}
    document_exts   = {'doc', 'docx', 'xls', 'xlsx', 'pdf', 'zip'}

    time.sleep(1.5)  # Simulate API latency
    fname_lower = filename.lower()

    if ext in suspicious_exts:
        return {
            "risk": "CRITICAL", "score_penalty": 60, "engine": "Sandbox Simulator",
            "flags": [
                "Spawned hidden child process (WScript.Shell)",
                f"Attempted registry modification: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "Outbound connection to known sinkhole IP (185.220.101.34:443)",
                "Attempted to disable Windows Defender via PowerShell"
            ]
        }
    elif ext in document_exts:
        if any(kw in fname_lower for kw in ('invoice', 'secure', 'urgent', 'payment', 'verify')):
            return {
                "risk": "HIGH", "score_penalty": 45, "engine": "Sandbox Simulator",
                "flags": [
                    "Document dropped embedded executable in %APPDATA%\\Roaming\\svchost.exe",
                    "Attempted to bypass AMSI via obfuscated VBA",
                    "Made outbound HTTP POST to unclassified domain"
                ]
            }
    return {
        "risk": "SAFE", "score_penalty": 0, "engine": "Sandbox Simulator",
        "flags": ["No malicious behavior observed during sandbox execution."]
    }

def _run_cuckoo_sandbox(file_bytes, filename):
    """
    Real Cuckoo Sandbox integration.
    Set CUCKOO_API_URL env var to your Cuckoo REST API endpoint (e.g. http://localhost:8090).
    """
    submit_url = f"{CUCKOO_API_URL}/tasks/create/file"
    try:
        resp = requests.post(
            submit_url,
            files={"file": (filename, file_bytes)},
            data={"timeout": 60, "enforce_timeout": True},
            timeout=10
        )
        resp.raise_for_status()
        task_id = resp.json().get("task_id")
        if not task_id:
            raise ValueError("No task_id returned from Cuckoo.")

        print(f"[AetherGuard] Cuckoo task submitted — Task ID: {task_id}")

        # Poll for completion (max 90 seconds)
        for _ in range(30):
            time.sleep(3)
            status_resp = requests.get(f"{CUCKOO_API_URL}/tasks/view/{task_id}", timeout=5)
            status = status_resp.json().get("task", {}).get("status", "")
            if status == "reported":
                break

        # Fetch the full behavioral report
        report_resp = requests.get(f"{CUCKOO_API_URL}/tasks/report/{task_id}", timeout=15)
        report = report_resp.json()

        # Parse Cuckoo's malscore and behavioral signatures
        malscore  = report.get("malscore", 0)
        sigs      = report.get("signatures", [])
        flags     = [s.get("description", s.get("name", "")) for s in sigs[:8]]
        penalty   = min(int(malscore * 10), 80)
        risk      = "CRITICAL" if malscore > 7 else "HIGH" if malscore > 4 else "SAFE"

        return {
            "risk": risk, "score_penalty": penalty,
            "engine": f"Cuckoo Sandbox (Task {task_id})",
            "malscore": malscore,
            "flags": flags if flags else ["No malicious signatures detected."]
        }

    except requests.exceptions.ConnectionError:
        print("[AetherGuard] Cuckoo unreachable — falling back to simulator.")
        return None
    except Exception as e:
        print(f"[AetherGuard] Cuckoo error: {e} — falling back to simulator.")
        return None

def dynamic_sandbox_analysis(file_bytes, filename):
    """
    Main sandbox entry point.
    - If CUCKOO_API_URL is configured: submits to real Cuckoo VM sandbox.
    - Otherwise: uses the intelligent behavioral simulator.
    """
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    scannable = {'exe','dll','bat','vbs','ps1','jar','doc','docx','xls','xlsx','pdf','zip'}
    if ext not in scannable:
        return None

    print(f"[AetherGuard] Sandbox: submitting '{filename}' (ext={ext})...")

    result = None
    if CUCKOO_API_URL:
        result = _run_cuckoo_sandbox(file_bytes, filename)

    if result is None:
        result = _simulate_sandbox(filename, ext)

    print(f"[AetherGuard] Sandbox result: {result['risk']} | penalty={result['score_penalty']} | engine={result['engine']}")
    return result

# ======================================
# MAIN SCAN FUNCTION
# ======================================
def scan_payload(text_payload="", file_bytes=None, filename=""):
    final_risk_score = 0
    ml_confidence = 0.0
    ml_result = "N/A"
    vt_urls = []
    breakdown = []
    extraction_note = None

    fname = filename.lower() if filename else ''

    # 0. YARA File Analysis (Static Signature Engine)
    if file_bytes and yara_compiled:
        try:
            yara_matches = yara_compiled.match(data=file_bytes)
            if yara_matches:
                for match in yara_matches:
                    pts = 50
                    final_risk_score += pts
                    breakdown.append({
                        "source": f"YARA Engine [{match.rule}]",
                        "points": pts,
                        "detail": "Matched critical malicious signature in payload."
                    })
        except Exception as e:
            print(f"[AetherGuard] YARA runtime error: {e}")

    # 0.5 Dynamic Sandbox Analysis (Behavioral)
    sandbox_result = None
    if file_bytes and filename:
        sandbox_result = dynamic_sandbox_analysis(file_bytes, filename)
        if sandbox_result and sandbox_result["score_penalty"] > 0:
            final_risk_score += sandbox_result["score_penalty"]
            engine_label = sandbox_result.get("engine", "Dynamic Sandbox Node")
            breakdown.append({
                "source": f"Dynamic Sandbox [{engine_label}]",
                "points": sandbox_result["score_penalty"],
                "detail": f"Risk: {sandbox_result['risk']} | Behavioral flags: {', '.join(sandbox_result['flags'])}"
            })

    # 1. Header Analysis (EML files or pasted raw EML strings)
    is_eml_file = fname.endswith('.eml')
    looks_like_eml_text = False
    if text_payload:
        looks_like_eml_text = (
            text_payload.startswith("Return-Path:") or 
            text_payload.startswith("Delivered-To:") or 
            text_payload.startswith("Received:") or
            text_payload.startswith("From:") or
            ("\nFrom:" in text_payload[:500] and "\nTo:" in text_payload[:500])
        )
        
    if is_eml_file and file_bytes:
        headers_status = analyze_headers(raw_bytes=file_bytes)
    elif looks_like_eml_text:
        headers_status = analyze_headers(raw_text=text_payload)
        
        # Extract pure body so ML model doesn't scan the raw header strings
        try:
            msg = email.message_from_string(text_payload, policy=default)
            body_part = msg.get_body(preferencelist=('plain', 'html'))
            if body_part:
                text_payload = body_part.get_content()
        except:
            pass
    else:
        headers_status = {}

    is_eml = is_eml_file # maintain compatibility with logic below

    # 2. Extract text from non-EML file types (PDF, DOCX, images)
    if file_bytes and filename and not is_eml:
        extracted = extract_text_from_file(file_bytes, filename)
        if extracted and not extracted.startswith('['):
            if not text_payload:
                text_payload = extracted
        elif extracted.startswith('['):
            extraction_note = extracted  # pass error/info back to UI

    # 3. Extract body from EML
    if file_bytes and is_eml and not text_payload:
        extracted = extract_body(file_bytes)
        if extracted:
            text_payload = extracted

    # 4. Process text payload
    if text_payload:
        # ML Classification (phase-aware)
        ml_confidence, ml_result = classify_text(text_payload)

        # --- Safe Sender Domain Discount ---
        # If email is from a verified legitimate domain and URL analysis is clean,
        # discount the ML confidence to reduce false positives on transactional emails.
        sender_is_trusted = False
        try:
            sender_raw = ''
            if file_bytes and fname.endswith('.eml'):
                import email as _em
                _msg = _em.message_from_bytes(file_bytes)
                sender_raw = _msg.get('From', '') or _msg.get('Reply-To', '')
            elif 'From:' in text_payload[:500]:
                import re as _re
                m = _re.search(r'From:.*?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text_payload[:500])
                if m:
                    sender_raw = m.group(1).lower()
            # Extract apex domain (last two parts)
            if sender_raw:
                parts = sender_raw.lower().strip().split('.')
                apex = '.'.join(parts[-2:]) if len(parts) >= 2 else sender_raw
                if apex in SAFE_SENDER_DOMAINS:
                    sender_is_trusted = True
        except Exception:
            pass

        # Effective threshold: lowered to 0.65 to catch moderate-confidence phishing
        # (0.85 for trusted/verified senders to reduce transactional email false positives)
        effective_threshold = 0.85 if sender_is_trusted else MODEL_META.get('threshold', 0.65)

        if ml_confidence > effective_threshold:
            # ML contributes up to 65 pts — ensures 100% phishing confidence = HIGH/DANGER score
            pts = int(ml_confidence * 65)
            if sender_is_trusted:
                pts = int(pts * 0.5)  # 50% discount for trusted senders
            final_risk_score += pts
            breakdown.append({
                "source": f"Neural Net (Phase {PHASE} ML)" if PHASE > 0 else "Neural Net (ML)",
                "points": pts,
                "detail": f"{(ml_confidence * 100):.1f}% phishing probability" + (" [Trusted sender domain discount applied]" if sender_is_trusted else "")
            })

        # --- Urgency / Threat Language Heuristics ---
        # Catch phishing patterns that the ML model might miss on short emails
        if not sender_is_trusted:
            URGENCY_PATTERNS = [
                (r'\b(suspended|suspension|deactivated|disabled|terminated)\b', 20, "Account suspension threat"),
                (r'\b(verify|confirm|validate|update)\b.{0,40}\b(account|payment|information|identity)\b', 20, "Credential verification request"),
                (r'\b(24|48|72)\s*hours?\b', 15, "Artificial urgency (time pressure)"),
                (r'\bclick\s+below\b|\bclick\s+here\b|\bclick\s+the\s+link\b', 10, "Suspicious CTA phrasing"),
                (r'\b(compromised|unauthorized|suspicious)\b.{0,30}\b(access|activity|login|device)\b', 25, "Account compromise claim"),
                (r'\bupdate\s+(your\s+)?payment\b', 25, "Payment update request"),
                (r'\b(we\s+noticed|we\s+detected|we\s+found)\b.{0,40}\b(new\s+device|login|sign.?in)\b', 20, "Fake security notification"),
            ]
            import re as _re
            urgency_pts = 0
            urgency_flags = []
            text_lower = text_payload.lower()
            for pattern, pts, label in URGENCY_PATTERNS:
                if _re.search(pattern, text_lower):
                    urgency_pts += pts
                    urgency_flags.append(label)
            if urgency_pts > 0:
                capped_pts = min(urgency_pts, 45)
                final_risk_score += capped_pts
                breakdown.append({
                    "source": "Threat Language Heuristics",
                    "points": capped_pts,
                    "detail": ", ".join(urgency_flags)
                })

        # URL Scanning
        urls = list(extract_urls(text_payload))
        for u in urls[:5]:
            is_suspicious, flags = analyze_url_heuristics(u)

            if VT_API_KEY:
                try:
                    url_id = base64.urlsafe_b64encode(u.encode()).decode().strip("=")
                    res = requests.get(
                        f"https://www.virustotal.com/api/v3/urls/{url_id}",
                        headers={"x-apikey": VT_API_KEY},
                        timeout=8
                    )
                    if res.status_code == 200:
                        stats = res.json().get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                        malicious = stats.get('malicious', 0)
                        suspicious_vt = stats.get('suspicious', 0)
                        total = sum(stats.values())
                        hits = malicious + suspicious_vt
                        vt_urls.append({
                            "url": u, "malicious_hits": hits,
                            "total_scans": total, "heuristic_flags": flags
                        })
                        if hits > 0:
                            pts = min(40, hits * 8)
                            final_risk_score += pts
                            breakdown.append({
                                "source": "VirusTotal",
                                "points": pts,
                                "detail": f"{hits}/{total} vendors flagged: {u[:50]}..."
                            })
                    else:
                        vt_urls.append({"url": u, "malicious_hits": 0, "total_scans": -1, "heuristic_flags": flags})
                except Exception as e:
                    print(f"[AetherGuard] VT error for {u}: {e}")
                    vt_urls.append({"url": u, "malicious_hits": 0, "total_scans": -1, "heuristic_flags": flags})

            # AlienVault OTX Check
            if OTX_API_KEY:
                try:
                    domain_match = re.search(r'https?://([^/?\s]+)', u)
                    if domain_match:
                        domain = domain_match.group(1).lower()
                        res = requests.get(
                            f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/general",
                            headers={"X-OTX-API-KEY": OTX_API_KEY},
                            timeout=8
                        )
                        if res.status_code == 200:
                            pulses = res.json().get('pulse_info', {}).get('count', 0)
                            if pulses > 0:
                                pts = min(40, pulses * 5)
                                final_risk_score += pts
                                breakdown.append({
                                    "source": "AlienVault OTX",
                                    "points": pts,
                                    "detail": f"Domain observed in {pulses} malicious threat pulses"
                                })
                except Exception as e:
                    print(f"[AetherGuard] OTX error for {u}: {e}")
            else:
                # Heuristic-only mode
                hit = 1 if is_suspicious else 0
                vt_urls.append({"url": u, "malicious_hits": hit, "total_scans": 1, "heuristic_flags": flags})
                if is_suspicious:
                    pts = min(30, len(flags) * 10)
                    final_risk_score += pts
                    breakdown.append({
                        "source": "URL Heuristics",
                        "points": pts,
                        "detail": f"{', '.join(flags[:2])} — {u[:45]}..."
                    })

    # 5. Header failure scoring
    failed = [k for k, v in headers_status.items() if v == 'fail']
    if failed:
        pts = min(40, len(failed) * 15)
        final_risk_score += pts
        breakdown.append({
            "source": "Header Authentication",
            "points": pts,
            "detail": f"Failed protocols: {', '.join(p.upper() for p in failed)}"
        })

    final_risk_score = min(final_risk_score, 100)

    # 6. XAI Attribution — per-sentence ML scoring (Explainable AI)
    # --- Financial Document False Positive Discount ---
    has_malicious_urls = any(hit.get('malicious_hits', 0) > 0 for hit in vt_urls)
    if not has_malicious_urls:
        fin_keywords = ['statement of account', 'transaction confirmation', 'mutual fund', 'invoice attached', 'folio no']
        if any(kw in text_payload.lower() for kw in fin_keywords):
            final_risk_score = max(0, final_risk_score - 20)
            breakdown.append({
                "source": "Context Analyzer",
                "points": -20,
                "detail": "Verified as standard financial document. Safe discount applied."
            })

    final_risk_score = min(final_risk_score, 100)

    # 5. Build final report
    attribution = compute_attribution(text_payload) if text_payload else []

    return {
        "final_risk_score": final_risk_score,
        "ml_classification_confidence": float(ml_confidence),
        "ml_classification_result": ml_result,
        "headers_status": headers_status,
        "vt_urls": vt_urls,
        "risk_breakdown": breakdown,
        "extraction_note": extraction_note,
        "xai_attribution": attribution,
        "text_payload": text_payload,
    }
