import os
import re
import io
import email
import base64
import pickle
import requests
from email.policy import default

# ======================================
# LOAD ML COMPONENTS
# ======================================
try:
    with open('model.pkl', 'rb') as f:
        model = pickle.load(f)
    with open('vectorizer.pkl', 'rb') as f:
        vectorizer = pickle.load(f)
    print("[AetherGuard] ML engine loaded successfully.")
except Exception as e:
    print(f"[AetherGuard] Warning: ML models not loaded. Run train_model.py first. Error: {e}")
    model = None
    vectorizer = None

VT_API_KEY = os.environ.get("VT_API_KEY", "")

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

def extract_text_from_file(file_bytes, filename):
    """Dispatch to the correct extractor based on file extension."""
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext == 'pdf':
        return extract_text_from_pdf(file_bytes)
    elif ext == 'docx':
        return extract_text_from_docx(file_bytes)
    elif ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'):
        return extract_text_from_image(file_bytes)
    return ""

# ======================================
# URL ANALYSIS
# ======================================
SHORTENERS = {
    'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'ow.ly',
    'is.gd', 'buff.ly', 'rebrand.ly', 'short.io', 'rb.gy', 'cutt.ly'
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
        parts = domain.split('.')
        apex = '.'.join(parts[-2:]) if len(parts) >= 2 else domain
        for brand in BRAND_KEYWORDS:
            if brand in domain and brand not in apex:
                flags.append(f"Brand '{brand}' in suspicious domain")
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
def analyze_headers(raw_bytes=None, eml_file_path=None):
    headers_status = {}
    if not raw_bytes and not eml_file_path:
        return headers_status
    try:
        if raw_bytes:
            msg = email.message_from_bytes(raw_bytes, policy=default)
        else:
            with open(eml_file_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=default)

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

    # 1. Header Analysis (EML files only)
    is_eml = fname.endswith('.eml')
    headers_status = analyze_headers(raw_bytes=file_bytes if is_eml else None)

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
        # ML Classification
        if model and vectorizer:
            X = vectorizer.transform([text_payload])
            prob = model.predict_proba(X)[0]
            ml_confidence = prob[1]
            if ml_confidence > 0.6:
                ml_result = "Phishing Characteristics Detected"
                pts = int(ml_confidence * 60)
                final_risk_score += pts
                breakdown.append({
                    "source": "Neural Net (ML)",
                    "points": pts,
                    "detail": f"{(ml_confidence * 100):.1f}% phishing probability"
                })
            else:
                ml_result = "Normal / Legitimate Text"

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

    return {
        "final_risk_score": final_risk_score,
        "ml_classification_confidence": float(ml_confidence),
        "ml_classification_result": ml_result,
        "headers_status": headers_status,
        "vt_urls": vt_urls,
        "risk_breakdown": breakdown,
        "extraction_note": extraction_note
    }
