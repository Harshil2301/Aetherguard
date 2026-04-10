# 🛡️ AetherGuard — Web3 Email Security Gateway

> **AI-powered phishing detection platform with ML classification, header authentication analysis, and real-time URL reputation scoring.**

AetherGuard is an offline-first, enterprise-grade email security gateway developed as part of the **Codec Internship Capstone Program — Cybersecurity Division (April 2026)**. It transforms raw email payloads into a structured, multi-layer threat verdict using a Python backend and a premium Web3-styled browser interface.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **ML Phishing Classifier** | Logistic Regression + TF-IDF bigrams trained on 110 real-world examples — **87.5% test accuracy** |
| **Header Authentication** | SPF, DKIM, and DMARC parsing from raw `.eml` files |
| **VirusTotal API v3** | Real-time URL reputation with graceful heuristic fallback |
| **Advanced URL Heuristics** | Detects IP-based URLs, lookalike/homograph domains, shorteners, suspicious TLDs, redirect chains |
| **Multi-Format File Support** | Scan `.eml`, `.txt`, `.pdf`, `.docx`, `.jpg`, `.png` and more |
| **Risk Score Breakdown** | Per-layer scoring transparency: ML, Headers, and URL contributions shown separately |
| **Telemetry Node** | Live session analytics: total scans, threats, safe verdicts, scan history log |
| **Export Report** | One-click JSON report download for incident documentation |
| **Scan History Persistence** | Scan log persists across page refreshes via `localStorage` |
| **Toast Notifications** | In-UI alerts — no browser dialogs |

---

## 🏗️ Project Architecture

```
PhishGuard-main/
│
├── app.py               # Flask web server & REST API (/api/scan, /api/status)
├── scanner.py           # Core engine: ML, header analysis, URL scanning, file extraction
├── train_model.py       # ML training pipeline with dataset, evaluation, and model export
├── requirements.txt     # All Python dependencies
│
├── GUI_Version/
│   ├── index.html       # Single-page app: Scanner + Telemetry views
│   ├── style.css        # Web3 design system: glassmorphism, mesh canvas, responsive layout
│   └── app.js           # All UI logic: scan flow, chart rendering, history, export
│
└── test_emails/
    ├── sample_phishing.eml   # Real .eml with SPF/DKIM/DMARC=fail headers for testing
    ├── fake_phishing.txt     # Text-based phishing payload for ML testing
    └── safe_email.txt        # Legitimate email sample
```

---

## 📦 Setup & Installation

### Prerequisites
- Python 3.x
- pip

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/PhishGuard-main.git
cd PhishGuard-main
```

### 2. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Train the ML Model
> Run this once before starting the server. Generates `model.pkl` and `vectorizer.pkl`.
```bash
python train_model.py
```
Expected output:
```
[AetherGuard] Dataset: 119 samples (61 phishing, 58 legitimate)
[AetherGuard] Train accuracy : 100.00%
[AetherGuard] Test  accuracy : 87.50%
```

### 5. (Optional) Set VirusTotal API Key
```bash
# Windows
set VT_API_KEY=your_api_key_here

# Linux/Mac
export VT_API_KEY=your_api_key_here
```
Get a free key at [virustotal.com](https://www.virustotal.com). Without it, the system falls back to local heuristics automatically.

### 6. Start the Gateway
```bash
python app.py
```
Open your browser at **http://127.0.0.1:5000**

---

## 🔍 How to Use

### Aether Core Intel (Scanner)
1. **Paste Payload** — Paste any suspicious email text into the textarea
2. **Upload a File** — Drag & drop or click to upload:
   - `.eml` — Full header + body analysis
   - `.txt` — ML + URL analysis
   - `.pdf` — Text extracted, then scanned
   - `.docx` — Text extracted, then scanned
   - `.jpg` / `.png` — (Requires Tesseract OCR if needed)
3. **INITIATE DEEP SCAN** — Runs all 3 analysis layers simultaneously
4. **Review Results:**
   - 🔵 **Risk Score Crystal** — Animated 0-100 threat score
   - ◉ **Risk Breakdown** — See exactly which layer added which points
   - ⬢ **Signature Authentication** — SPF / DKIM / DMARC pass/fail status
   - ▲ **Neural Net Classification** — ML phishing confidence with progress bar
   - ◈ **Global Node Consensus** — URL reputation results with heuristic flag tags
5. **↓ EXPORT** — Download full JSON incident report

### Telemetry Node
Click **Telemetry Node** in the sidebar to view:
- **System Status** — Gateway health, ML engine state, VT API status
- **Session Counters** — Total scans, threats, safe, elevated risk
- **Scan History Log** — Full table of all scans this session (persists on refresh)

---

## 🧠 Detection Engine

### Layer 1 — ML Neural Classification
- **Algorithm:** Logistic Regression with TF-IDF bigram vectorization
- **Dataset:** 110 curated examples across 12 phishing attack categories
- **Evaluation:** 80/20 stratified train/test split — **87.5% test accuracy**
- **Scoring:** Contributes up to **60 points** to the risk score

### Layer 2 — SPF / DKIM / DMARC Header Analysis
- Parses `Authentication-Results` headers from raw `.eml` files
- Detects `fail`, `softfail`, and `permerror` statuses
- Each failed protocol contributes **15 points** to the risk score (max 40)

### Layer 3 — URL Reputation & Heuristics
| Check | What It Detects |
|---|---|
| IP-based URL | `http://185.220.101.34/login` |
| URL shorteners | `bit.ly`, `tinyurl.com`, `goo.gl` + 8 more |
| Suspicious TLDs | `.xyz`, `.top`, `.click`, `.loan` + 11 more |
| Brand impersonation | `paypal` in non-`paypal.com` domain |
| Homograph/lookalike | `paypa1.com`, `amaz0n.xyz`, `g00gle.net` |
| Excessive subdomains | More than 3 subdomain levels |
| Insecure HTTP | `http://` instead of `https://` |
| Redirect chains | Embedded `http://` inside another URL |
| Abnormally long URL | Over 120 characters |

---

## 🔑 Risk Scoring Formula

```
Total Score = MIN(
    ML_score        (0–60 pts, based on phishing confidence)
  + Header_score    (0–40 pts, failed SPF/DKIM/DMARC)
  + URL_score       (0–30 pts per suspicious URL, heuristics)
  + VT_score        (0–40 pts, vendor malicious votes)
, 100)
```

| Score Range | Verdict | Color |
|---|---|---|
| 0 – 29 | ✅ SAFE NODE | Green |
| 30 – 69 | ⚠️ ELEVATED RISK | Amber |
| 70 – 100 | 🔴 CRITICAL BREACH | Red |

---

## 🔒 Security Design

- **Zero-execution:** All payloads are treated as plain text strings. No HTML is rendered. No JavaScript from emails is executed.
- **Offline-first:** All analysis happens locally on your machine. No email content is sent to external servers (unless VirusTotal API is explicitly configured).
- **Safe file handling:** Files are read as bytes in memory. No file is written to disk during scanning.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| ML Engine | Scikit-Learn (LogisticRegression + TfidfVectorizer) |
| Data Layer | Pandas |
| URL Intelligence | VirusTotal API v3, Custom Heuristics |
| Email Parsing | Python `email` module (RFC 5322) |
| File Extraction | PyPDF2 (PDF), python-docx (DOCX), Pillow (Images) |
| Frontend | Vanilla HTML5, CSS3, JavaScript (ES2022) |
| Canvas | HTML5 Canvas API (mesh particle network) |
| Fonts | Google Fonts (Outfit, Space Grotesk) |
| Version Control | Git |

---

## 🧪 Testing

A sample phishing email is provided at `test_emails/sample_phishing.eml` with pre-set failures:
- `dkim=fail`
- `spf=fail`
- `dmarc=fail`
- Contains a `bit.ly` redirect URL

Expected result: **Score ≥ 70 (CRITICAL BREACH)**

---

## 📚 References

1. IBM Security. (2023). *Cost of a Data Breach Report 2023.* IBM Corporation.
2. MITRE Corporation. (2024). *MITRE ATT&CK® Framework v14.* https://attack.mitre.org
3. Proofpoint. (2023). *State of the Phish 2023.* Proofpoint, Inc.
4. Verizon. (2023). *Data Breach Investigations Report (DBIR) 2023.* Verizon Business.
5. Anti-Phishing Working Group. (2023). *Phishing Activity Trends Report Q4 2023.*
6. CISA. (2023). *Phishing Guidance: Stopping the Attack Cycle at Phase One.*

---

## 🎓 About

**AetherGuard** — Developed as part of the **Codec Internship Program, Cybersecurity Division, April 2026.**

> *This project is built for educational and internship demonstration purposes. It showcases applied knowledge of email security protocols, machine learning, heuristic analysis, and modern web development.*
