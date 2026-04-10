# 🛡️ AetherGuard - Web3 Security Gateway

AetherGuard is a high-performance web-based security gateway designed to rapidly analyze suspicious emails and identify indicators of phishing attacks. Developed as a pure Python security tool, it operates locally with zero external dependencies, making it 100% safe, perfectly secure for offline analysis, and extremely fast.

## 🚀 Features

- **Blazing Fast Heuristic Analysis:** Uses a rule-based engine to scan for psychological manipulation tactics (urgency, forced actions).
- **Intelligent URL Extraction:** Locates all links hidden within text or email files (`.txt`, `.eml`).
- **Signature Threat Scoring:** Scores extracted URLs against known malicious patterns (IP-based URLs, suspicious TLDs like `.xyz`, and URL shorteners used for masking).
- **Detailed Threat Report:** Automatically calculates a threat score from 0-100 and outputs a highly readable, color-coded terminal report.
- **100% Secure Architecture:** Completely passive analysis. The tool does not execute files, contact external tracking servers, or pose any risk to the host OS.

## 📦 Setup & Requirements

AetherGuard requires the Python dependencies listed in `requirements.txt`.

1. Ensure Python 3.x is installed on your system.
2. Clone this repository to your local machine.
3. Install dependencies: `pip install -r requirements.txt`

## 💻 Usage

To launch the AetherGuard Web3 gateway, simply run the flask application:

```bash
python app.py
```

Then open your browser and navigate to `http://127.0.0.1:5000`.

## 🔍 How to Use

1. **Paste Payload** — Paste suspicious email text directly into the "Payload Injection" textarea.
2. **Upload .EML File** — Drag and drop a raw `.eml` file (or click to browse) to enable full header analysis.
3. **Initiate Deep Scan** — Click the "INITIATE DEEP SCAN" button to run all analysis engines.
4. **Review Results** — The Aether Diagnostics panel will display:
   - **Signature Authentication** — SPF, DKIM, DMARC pass/fail status from email headers.
   - **Neural Net Classification** — ML phishing confidence score with a visual progress bar.
   - **Global Node Consensus** — VirusTotal URL reputation results (requires `VT_API_KEY`).

> **Tip:** A sample phishing `.eml` file is provided at `test_emails/sample_phishing.eml` to test the header analysis feature end-to-end.

## 🔑 VirusTotal API (Optional)

Set your VirusTotal API key as an environment variable to enable real-time URL scanning:

```bash
set VT_API_KEY=your_api_key_here   # Windows
export VT_API_KEY=your_api_key_here # Linux/Mac
```

If no key is provided, AetherGuard falls back to local heuristic URL analysis.

## 🏗️ Project Architecture

*   `app.py`: The main Flask web server and REST API endpoint.
*   `scanner.py`: The core engine containing ML classification, header parsing, URL extraction, and VirusTotal integration.
*   `train_model.py`: Script to generate and train the local phishing detection ML model.
*   `GUI_Version/`: Complete Web3 frontend — HTML, CSS, and JavaScript.
*   `test_emails/`: Sample emails (`.txt` and `.eml`) for testing the scanner.

## 🎓 Educational Purpose

This project is built and maintained as part of a formal Cybersecurity Internship program to demonstrate applied knowledge of social engineering defense, Python tool development, and heuristic malware analysis. It is completely safe for deployment.
