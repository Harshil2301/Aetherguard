<div align="center">
  <img src="https://raw.githubusercontent.com/harshil2301/AetherGuard/main/extension/icons/icon128.png" width="128" alt="AetherGuard Logo">
  
  # AetherGuard: Open-Source Email Security
  
  **Real-Time Phishing Detection via Browser Integration**
  
  AetherGuard is an open-source email security tool that integrates a Machine Learning pipeline into the browser to detect phishing threats in real-time.
</div>

---

## 🚀 Overview

Traditional phishing scanners rely on static databases and require users to manually forward suspicious emails. AetherGuard approaches this by intercepting the email payload directly in the browser memory using a local `SentenceTransformer`, evaluating the underlying semantics of the email with high precision.

- **Browser Integration:** The Chrome Extension intercepts and scans emails within the Gmail interface.
- **Deep Semantic ML Engine:** Trained on an 82,400+ email dataset across 6 corpora (Enron, Nazario, SpamAssassin, etc.).
- **Explainable AI (XAI):** AetherGuard extracts the exact sentence that triggered the neural network, mapped to MITRE ATT&CK concepts.
- **Tuned for Legitimate Communications:** The model is specifically tuned to minimize false positives, prioritizing the delivery of legitimate financial and transactional emails.
- **Automated SOC Alerts:** Integration with Discord webhooks allows for optional alert forwarding when high-risk payloads are detected.

---

## 🛠 Tech Stack Architecture

| Component | Technology | Role |
|---|---|---|
| **Frontend** | React 18 + Vite | Telemetry Node & Dashboard |
| **Backend** | Flask (Python 3.10+) | API Gateway, ML Engine orchestration, YARA parsing |
| **Machine Learning** | `SentenceTransformer` + `SGDClassifier` | Converts text to semantic vectors, classifies threats |
| **Browser Extension** | Chrome Manifest V3 | Injects Threat HUD directly into Gmail DOM |
| **Database** | SQLite + Firebase | Local persistent storage and remote telemetry sync |

---

## 📊 Performance Benchmark

AetherGuard was evaluated against a custom enterprise suite:

- **Dataset:** Kaggle 6-Corpus (82,486 real emails)
- **Legitimate Recall:** `98.79%` (Optimized for low false positive rate)
- **Phishing Catch Rate:** `90.15%` 
- **Inference Speed:** ~300ms round-trip latency on CPU

---

## ⚙️ Quick Start Installation

### 1. The Backend (Python ML Engine)
Clone the repository and set up the Python environment:
```bash
git clone https://github.com/harshil2301/AetherGuard.git
cd AetherGuard

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the backend (Starts on localhost:5000)
python app.py
```

### 2. The Frontend (Telemetry Dashboard)
Open a new terminal to start the React application:
```bash
cd AetherGuard/client

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. The Chrome Extension
1. Open Google Chrome and navigate to `chrome://extensions/`
2. Toggle **Developer mode** in the top right.
3. Click **Load unpacked** and select the `AetherGuard/extension` folder.
4. Click the AetherGuard icon in your extension tray, input your Telemetry API key from the Dashboard, and open Gmail.

---

## 🧠 Retraining the Model

You can fine-tune the model directly using your own datasets:

1. Place your CSV inside `data/phishing_emails.csv/`
2. Run the precision-biased training pipeline:
```bash
python scripts/train_model.py
```
3. Evaluate the model:
```bash
python scripts/evaluate_model.py
```

---

## 🧪 Testing

AetherGuard includes a Gmail API injector to push test payloads into your inbox for evaluation.

```bash
python scripts/inject_test_emails.py
```

---

<div align="center">
  <i>Developed by Harshil Parmar.</i>
</div>
