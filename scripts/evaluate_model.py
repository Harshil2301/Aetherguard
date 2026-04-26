"""
AetherGuard — Phase 5 Enterprise Model Evaluation Suite
=========================================================
Produces a full quantitative analysis of the active model including:
  - Overall accuracy, precision, recall, F1-score
  - Confusion matrix with FP rate
  - Financial email false-positive specific benchmark
  - JSON audit report saved to models/model_evaluation_report.json
"""

import os
import json
import time
import pickle
import numpy as np
from datetime import datetime
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, precision_score, recall_score, f1_score
)

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR  = os.path.join(BASE_DIR, 'models')
REPORT_PATH = os.path.join(MODELS_DIR, 'model_evaluation_report.json')

# Hard-coded financial email FP benchmark — these MUST score as SAFE
FINANCIAL_FP_BENCHMARK = [
    ("Your SBI Mutual Fund account statement for Q1 2024 is attached.", 0),
    ("Groww: Your SIP of INR 5,000 was successfully processed.", 0),
    ("HDFC Bank: Monthly statement for March 2024 is available on NetBanking.", 0),
    ("Zerodha: Your capital gains statement for FY 2023-24 is now ready.", 0),
    ("Naukri.com: 5 new job recommendations for Harshil Parmar — Junior Pen Tester.", 0),
    ("Amazon.in: Your order has been shipped. Tracking ID: IN123456789.", 0),
    ("GitHub: [AetherGuard] Pull request #42 by harshil2301 — review requested.", 0),
    ("Microsoft 365: Your subscription has been renewed for 1 year. Amount: INR 4,999.", 0),
    ("Upstox: Contract note for today's trades. Net P&L: +2,340 INR.", 0),
    ("AngelOne: Units allotted to your mutual fund SIP for April 2024.", 0),
    ("Your electricity bill of INR 1,840 is due on April 20, 2024.", 0),
    ("IRCTC: Booking confirmed for PNR 4521839076. Train: 12955 Mumbai Rajdhani.", 0),
    ("PayTM: Money received! INR 500 from Rahul Sharma. Balance: INR 1,430.", 0),
    ("Google Pay: Payment of INR 200 made to Zomato. UPI ID: harshil@oksbi.", 0),
    ("Your GST return for March 2024 has been filed. ARN: AA123456789.", 0),
    ("Dear customer, your FD of INR 50,000 has matured. Credit to savings account.", 0),
    ("Your loan EMI of INR 12,500 has been debited for April 2024.", 0),
    ("Zerodha Varsity: New module on Options Trading is now live.", 0),
    ("Statement of holdings: Total portfolio value INR 2,45,000 across 8 funds.", 0),
    ("ICICI Prudential: Dividend payout of INR 500 has been credited.", 0),
]

# Clear phishing samples — these MUST score as PHISHING
PHISHING_BENCHMARK = [
    ("URGENT: Your PayPal account has been limited. Click here to verify now!", 1),
    ("Your Netflix subscription payment failed. Update billing: http://netflix-billing.xyz", 1),
    ("Congratulations! You have won a $1,000 Amazon gift card. Claim at: http://amazon-prize.top", 1),
    ("Your Apple ID has been locked. Verify identity: http://appleid-unlock.ml/login", 1),
    ("FINAL WARNING: IRS demands $3,492. Pay now to avoid arrest: http://irs-collect.xyz", 1),
    ("Dear Sir, I am Nigerian prince with $18.5 million. Please send your bank details.", 1),
    ("Your Google account was accessed from Nigeria. Secure it: http://google-security.net", 1),
    ("DHL: Package undeliverable. Pay $2.99 fee to reschedule: http://dhl-redelivery.xyz", 1),
    ("Your bank account has been compromised. Verify at: http://hdfc-secure.ml/unlock", 1),
    ("Microsoft: Your account will be deleted in 24 hours. Verify: http://msft-verify.xyz", 1),
    ("Free iPhone 15 giveaway! Enter your details to win: http://free-iphone-promo.top", 1),
    ("Your password has been reset. If not you, click: http://reset-verify.phish.xyz", 1),
    ("ALERT: Unauthorized transaction of $499 on your card. Dispute: http://bank-dispute.ml", 1),
    ("Verify your email now or lose access to your account permanently: http://verify-now.xyz", 1),
    ("Claim your Bitcoin reward of 0.5 BTC. Limited time: http://crypto-reward.top/claim", 1),
]


def load_models():
    print("[AetherGuard Eval] Loading model artifacts...")
    with open(os.path.join(MODELS_DIR, 'model.pkl'), 'rb') as f:
        clf = pickle.load(f)
    with open(os.path.join(MODELS_DIR, 'vectorizer.pkl'), 'rb') as f:
        encoder = pickle.load(f)
    with open(os.path.join(MODELS_DIR, 'model_meta.json'), 'r') as f:
        meta = json.load(f)
    print(f"[AetherGuard Eval] Model: Phase {meta.get('phase', '?')} | Dataset: {meta.get('dataset', 'Unknown')[:60]}")
    print(f"[AetherGuard Eval] Threshold: {meta.get('threshold', 0.65)}")
    return clf, encoder, meta


def encode_batch(texts, encoder):
    all_emb = []
    batch_size = 64
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = encoder.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_emb.append(emb)
        pct = min(i+batch_size, len(texts)) / len(texts) * 100
        print(f"\r  Encoding... {pct:.0f}%", end='', flush=True)
    print()
    return np.vstack(all_emb)


def load_hf_eval_sample(encoder, sample_size=5000):
    """Load a random sample from HuggingFace for main benchmark."""
    try:
        from huggingface_hub import hf_hub_download
        import pandas as pd
        print(f"\n[AetherGuard Eval] Loading {sample_size:,} random emails from HuggingFace...")
        file_path = hf_hub_download(
            repo_id="ealvaradob/phishing-dataset",
            repo_type="dataset",
            filename="combined_reduced.json"
        )
        df = pd.read_json(file_path)
        df = df.rename(columns={df.columns[0]: 'text', df.columns[-1]: 'label'})
        df = df.dropna(subset=['text', 'label'])
        df['label'] = pd.to_numeric(df['label'], errors='coerce').dropna().astype(int)
        df = df[df['label'].isin([0, 1])]
        if len(df) > sample_size:
            df = df.sample(sample_size, random_state=77)
        texts = df['text'].tolist()
        labels = df['label'].tolist()
        X = encode_batch(texts, encoder)
        return X, labels
    except Exception as e:
        print(f"[AetherGuard Eval] Could not load HF dataset: {e}")
        return None, None


def run_benchmark(clf, encoder, meta):
    threshold = meta.get('threshold', 0.65)

    # ── 1. Main HuggingFace benchmark ────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  AETHERGUARD — ENTERPRISE MODEL EVALUATION REPORT")
    print("=" * 60)

    X_hf, y_hf = load_hf_eval_sample(encoder, sample_size=5000)

    main_results = {}
    if X_hf is not None:
        proba_hf = clf.predict_proba(X_hf)[:, 1]
        y_pred_hf = (proba_hf >= threshold).astype(int)
        cm = confusion_matrix(y_hf, y_pred_hf)
        tn, fp, fn, tp = cm.ravel()
        fp_rate = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0

        print(f"\n  [MAIN BENCHMARK] — {len(y_hf):,} random emails from HuggingFace")
        print(f"  {'-'*55}")
        print(f"  Accuracy          : {accuracy_score(y_hf, y_pred_hf):.2%}")
        print(f"  Phishing Precision : {precision_score(y_hf, y_pred_hf):.2%}")
        print(f"  Phishing Recall    : {recall_score(y_hf, y_pred_hf):.2%}")
        print(f"  F1 Score          : {f1_score(y_hf, y_pred_hf):.2%}")
        print(f"  False Positive Rate: {fp_rate:.2f}%  ({fp} legit emails wrongly flagged)")
        print(f"  Legitimate Recall : {tn / (tn + fp) * 100:.2f}%  (legit emails correctly cleared)")
        print(f"\n  Confusion Matrix:")
        print(f"                       [Pred Legit]  [Pred Phish]")
        print(f"  [Actual Legitimate]     {tn:<12} {fp}")
        print(f"  [Actual Phishing]       {fn:<12} {tp}")
        print(f"\n  Classification Report:")
        print(classification_report(y_hf, y_pred_hf, target_names=['Legitimate', 'Phishing']))

        main_results = {
            "sample_size": len(y_hf),
            "accuracy": round(accuracy_score(y_hf, y_pred_hf), 4),
            "phishing_precision": round(precision_score(y_hf, y_pred_hf), 4),
            "phishing_recall": round(recall_score(y_hf, y_pred_hf), 4),
            "f1_score": round(f1_score(y_hf, y_pred_hf), 4),
            "false_positive_rate_pct": round(fp_rate, 2),
            "legitimate_recall_pct": round(tn / (tn + fp) * 100, 2),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)}
        }

    # ── 2. Financial Email FP Benchmark ──────────────────────────────────────
    print(f"\n  [FINANCIAL EMAIL BENCHMARK] — {len(FINANCIAL_FP_BENCHMARK)} financial/tech emails (must ALL be SAFE)")
    print(f"  {'-'*55}")
    fin_texts = [t for t, l in FINANCIAL_FP_BENCHMARK]
    fin_labels = [l for t, l in FINANCIAL_FP_BENCHMARK]
    X_fin = encode_batch(fin_texts, encoder)
    proba_fin = clf.predict_proba(X_fin)[:, 1]
    y_pred_fin = (proba_fin >= threshold).astype(int)

    fin_fp = sum(1 for pred, true in zip(y_pred_fin, fin_labels) if pred == 1 and true == 0)
    fin_ok = len(FINANCIAL_FP_BENCHMARK) - fin_fp

    for i, (text, true_label) in enumerate(FINANCIAL_FP_BENCHMARK):
        pred = y_pred_fin[i]
        prob = proba_fin[i]
        status = "PASS" if pred == 0 else "FAIL (FALSE POSITIVE!)"
        print(f"  [{status}] ({prob:.2f}) {text[:55]}...")

    print(f"\n  Result: {fin_ok}/{len(FINANCIAL_FP_BENCHMARK)} correctly cleared as SAFE")
    print(f"  False Positives: {fin_fp}  {'(PERFECT!)' if fin_fp == 0 else '(Needs tuning)'}")

    # ── 3. Phishing Detection Benchmark ──────────────────────────────────────
    print(f"\n  [PHISHING DETECTION BENCHMARK] — {len(PHISHING_BENCHMARK)} clear phishing emails (must ALL be flagged)")
    print(f"  {'-'*55}")
    ph_texts = [t for t, l in PHISHING_BENCHMARK]
    ph_labels = [l for t, l in PHISHING_BENCHMARK]
    X_ph = encode_batch(ph_texts, encoder)
    proba_ph = clf.predict_proba(X_ph)[:, 1]
    y_pred_ph = (proba_ph >= threshold).astype(int)

    ph_fn = sum(1 for pred, true in zip(y_pred_ph, ph_labels) if pred == 0 and true == 1)
    ph_ok = len(PHISHING_BENCHMARK) - ph_fn

    for i, (text, true_label) in enumerate(PHISHING_BENCHMARK):
        pred = y_pred_ph[i]
        prob = proba_ph[i]
        status = "PASS" if pred == 1 else "MISS (FALSE NEGATIVE!)"
        print(f"  [{status}] ({prob:.2f}) {text[:55]}...")

    print(f"\n  Result: {ph_ok}/{len(PHISHING_BENCHMARK)} phishing emails correctly detected")
    print(f"  False Negatives: {ph_fn}  {'(PERFECT!)' if ph_fn == 0 else '(Model needs more phishing data)'}")

    # ── Save JSON report ──────────────────────────────────────────────────────
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "model_phase": meta.get('phase', 'Unknown'),
        "dataset": meta.get('dataset', 'Unknown'),
        "threshold": threshold,
        "main_benchmark": main_results,
        "financial_fp_benchmark": {
            "total_emails": len(FINANCIAL_FP_BENCHMARK),
            "correctly_cleared": fin_ok,
            "false_positives": fin_fp,
            "pass_rate_pct": round(fin_ok / len(FINANCIAL_FP_BENCHMARK) * 100, 1)
        },
        "phishing_detection_benchmark": {
            "total_emails": len(PHISHING_BENCHMARK),
            "correctly_flagged": ph_ok,
            "false_negatives": ph_fn,
            "detection_rate_pct": round(ph_ok / len(PHISHING_BENCHMARK) * 100, 1)
        }
    }

    with open(REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n  {'='*55}")
    print(f"  EVALUATION COMPLETE")
    print(f"  Report saved to: models/model_evaluation_report.json")
    print(f"  {'='*55}\n")
    return report


if __name__ == '__main__':
    clf, encoder, meta = load_models()
    run_benchmark(clf, encoder, meta)
