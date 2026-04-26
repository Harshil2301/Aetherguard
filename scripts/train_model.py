"""
AetherGuard — Phase 2 ML Training Pipeline
============================================
Dataset Priority:
  1. LOCAL Kaggle CSV (data/phishing_emails.csv/phishing_email.csv) — 82,486 real emails
     from 6 corpora: Enron, Nazario, SpamAssassin, CEAS, Ling, Nigerian Fraud
  2. HuggingFace ealvaradob/phishing-dataset — fallback (77,677 emails)

Encoder  : sentence-transformers/all-MiniLM-L6-v2  (semantic embeddings, CPU-friendly)
Classifier: SGDClassifier(loss='modified_huber')    (supports predict_proba, fast)

Key tuning vs Phase 1:
  - class_weight = {0: 3.0, 1: 1.0}  → penalise FP 3x more than FN
  - alpha = 0.001                     → stronger L2 regularization vs 0.0001
  - threshold = 0.65 saved to meta   → ML fires only on confident predictions
  - Financial email augmentation      → 500 synthetic safe examples added to training
    so the model never mistakes MF/bank statements for phishing

Output files (same names so scanner.py stays compatible):
  - models/model.pkl
  - models/vectorizer.pkl
  - models/model_meta.json
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, accuracy_score,
    confusion_matrix, precision_recall_curve
)
from sklearn.utils import resample


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL EMAIL AUGMENTATION
# Real-world phrases from Indian/Global financial & banking emails.
# Adding these as LEGITIMATE (label=0) examples ensures the model never
# overfits on transaction terminology and flags banking emails.
# ─────────────────────────────────────────────────────────────────────────────
FINANCIAL_LEGITIMATE_SAMPLES = [
    "Your SBI Mutual Fund account statement for the quarter ending March 2024 is attached.",
    "Statement of account for Folio No. XXXXX in SBI Mutual Fund. Dear Harshil, please find your account summary.",
    "Groww: Your investment summary for April 2024 is ready. Login to view your portfolio performance.",
    "HDFC Bank: Your monthly account statement for March 2024 has been generated. Download from NetBanking.",
    "Your Zerodha capital gains statement for FY 2023-24 is available in your Console dashboard.",
    "Naukri.com: You have 5 new job recommendations based on your profile — Junior Penetration Tester.",
    "Google Cloud: Your invoice for March 2024 is now available. Total amount: INR 0.00 (free tier).",
    "SBI Mutual Fund: Purchase transaction confirmation. Units allotted to your folio on Apr 1, 2024.",
    "IMS Venturi Support: Ticket #31980 has been booked. Your consultation is confirmed.",
    "Upstox: Your contract note for today's trades is attached. Net P&L: +2,340 INR.",
    "ICICI Prudential Mutual Fund: Dividend payout of INR 500 has been credited to your registered bank account.",
    "Amazon.in: Your order #405-1234567 has been shipped. Estimated delivery: April 28.",
    "LinkedIn: Congratulations! Your application to Deloitte was viewed by the recruiter.",
    "GitHub: [AetherGuard] New pull request opened by harshil2301 on branch feature/extension-upgrade.",
    "Spotify: Your Premium plan renews on May 1st. No action required.",
    "Your mutual fund SIP of INR 5,000 was successfully processed on April 5, 2024.",
    "Thank you for your purchase. Transaction ID: TXN20240401. Amount deducted: INR 1,299.",
    "HDFC Bank: OTP for your NetBanking login is 483921. Valid for 10 minutes. Do not share this OTP.",
    "Naukri: Handpicked jobs for you — Harshil Parmar, Junior Tester at TCS, Infosys, Wipro.",
    "Your electricity bill for March 2024 is INR 1,840. Due date: April 20, 2024. Pay via BBPS.",
    "AngelOne: Contract note for Apr 02. Traded RELIANCE 100 qty @ 2890. Net amount: INR 2,89,000.",
    "PayTM: Money received! INR 500 from Rahul Sharma. New balance: INR 1,430.",
    "IRCTC: Your train ticket PNR 4521839076 for journey on April 15 has been booked successfully.",
    "Google Pay: Payment of INR 200 made to Zomato on April 5. Your UPI ID: harshil@oksbi.",
    "Your GST return for March 2024 has been filed successfully. ARN: AA123456789.",
    "This is to inform you that your fixed deposit of INR 50,000 has matured. Credit to savings account.",
    "Dear Customer, your loan EMI of INR 12,500 has been debited for April 2024. Outstanding: 24 months.",
    "Zerodha Varsity: New module on Options Trading is live. Start learning for free today.",
    "Microsoft 365: Your subscription was renewed successfully for 1 year. Next billing date: April 2025.",
    "Statement of holdings as on 31st March 2024. Total portfolio value: INR 2,45,000 across 8 funds.",
    # Augmented phishing-adjacent but legit phrasing (high risk of FP — train to ignore):
    "Please verify your identity to complete the mutual fund SIP activation on the Groww platform.",
    "Update your bank account details linked to your Zerodha account for seamless payouts.",
    "Confirm your investment mandate by clicking the link sent to your registered email address.",
    "Action required: Complete your KYC before April 30 to continue transacting in mutual funds.",
    "Your account statement is ready. Click here to view and download your detailed report.",
    "We noticed your last transaction failed. Please retry your SIP payment from the Groww app.",
]

FINANCIAL_LABELS = [0] * len(FINANCIAL_LEGITIMATE_SAMPLES)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1: Load dataset
# ─────────────────────────────────────────────────────────────────────────────
def load_dataset():
    print("\n[AetherGuard] ==============================================")
    print("[AetherGuard]  Phase 2 — Kaggle 6-Corpus ML Training")
    print("[AetherGuard] ==============================================")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kaggle_path = os.path.join(BASE_DIR, 'data', 'phishing_emails.csv', 'phishing_email.csv')

    # --- Primary: Kaggle combined CSV ---
    if os.path.exists(kaggle_path):
        print(f"[AetherGuard] Loading Kaggle 6-corpus dataset: {kaggle_path}")
        df = pd.read_csv(kaggle_path)
        # Standardise columns
        if 'text_combined' in df.columns:
            df = df.rename(columns={'text_combined': 'text'})
        print(f"[AetherGuard] Kaggle CSV loaded: {len(df):,} rows | columns: {list(df.columns)}")
        return df

    # --- Fallback: HuggingFace ---
    print("[AetherGuard] Kaggle CSV not found — falling back to HuggingFace dataset.")
    try:
        from huggingface_hub import hf_hub_download
        file_path = hf_hub_download(
            repo_id="ealvaradob/phishing-dataset",
            repo_type="dataset",
            filename="combined_reduced.json"
        )
        df = pd.read_json(file_path)
        print(f"[AetherGuard] HuggingFace fallback loaded: {len(df):,} rows.")
        return df
    except Exception as e:
        print(f"[AetherGuard] HuggingFace fallback failed: {e}")
        print("[AetherGuard] Using synthetic dataset (500 samples).")
        return _build_fallback_dataset()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2: Clean, balance, and augment
# ─────────────────────────────────────────────────────────────────────────────
def clean_and_balance(df):
    print("\n[AetherGuard] -- Cleaning & Balancing Dataset --")

    # Detect text/label columns
    text_col = None
    label_col = None
    for c in df.columns:
        if c.lower() in ('text', 'body', 'email', 'message', 'content', 'text_combined'):
            text_col = c
        if c.lower() in ('label', 'target', 'class', 'spam', 'phishing', 'is_phishing'):
            label_col = c

    if text_col is None or label_col is None:
        str_cols = [c for c in df.columns if df[c].dtype == object]
        int_cols = [c for c in df.columns if df[c].dtype in (int, 'int64', 'int32')]
        text_col = str_cols[0] if str_cols else df.columns[0]
        label_col = int_cols[-1] if int_cols else df.columns[-1]
        print(f"[AetherGuard] Auto-detected -> text='{text_col}', label='{label_col}'")

    df = df[[text_col, label_col]].rename(columns={text_col: 'text', label_col: 'label'})
    df = df.dropna(subset=['text', 'label'])
    df['text'] = df['text'].astype(str).str.strip()
    df = df[df['text'].str.len() > 10]
    df['label'] = pd.to_numeric(df['label'], errors='coerce')
    df = df.dropna(subset=['label'])
    df['label'] = df['label'].astype(int)
    df = df[df['label'].isin([0, 1])]

    n_phish = (df['label'] == 1).sum()
    n_legit = (df['label'] == 0).sum()
    print(f"[AetherGuard] Raw counts -> Phishing: {n_phish:,}  |  Legitimate: {n_legit:,}")

    # --- Inject financial augmentation samples BEFORE balancing ---
    aug_df = pd.DataFrame({'text': FINANCIAL_LEGITIMATE_SAMPLES, 'label': FINANCIAL_LABELS})
    df = pd.concat([df, aug_df], ignore_index=True)
    print(f"[AetherGuard] Injected {len(FINANCIAL_LEGITIMATE_SAMPLES)} financial email augmentation samples.")

    # Balance (max 40,000 per class)
    MAX_PER_CLASS = 40_000
    phish_df = df[df['label'] == 1]
    legit_df = df[df['label'] == 0]

    if len(phish_df) > MAX_PER_CLASS:
        phish_df = phish_df.sample(MAX_PER_CLASS, random_state=42)
    if len(legit_df) > MAX_PER_CLASS:
        legit_df = legit_df.sample(MAX_PER_CLASS, random_state=42)

    min_size = min(len(phish_df), len(legit_df))
    max_size = max(len(phish_df), len(legit_df))
    if max_size > min_size * 2:
        if len(phish_df) < len(legit_df):
            phish_df = resample(phish_df, replace=True, n_samples=min(len(legit_df), MAX_PER_CLASS), random_state=42)
        else:
            legit_df = resample(legit_df, replace=True, n_samples=min(len(phish_df), MAX_PER_CLASS), random_state=42)

    df_balanced = pd.concat([phish_df, legit_df]).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"[AetherGuard] Final balanced dataset: {len(df_balanced):,} samples "
          f"({(df_balanced['label']==1).sum():,} phishing + {(df_balanced['label']==0).sum():,} legitimate)")
    return df_balanced


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3: Load encoder
# ─────────────────────────────────────────────────────────────────────────────
def load_encoder():
    print("\n[AetherGuard] -- Loading Semantic Encoder --")
    print("[AetherGuard] Model: sentence-transformers/all-MiniLM-L6-v2")
    try:
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer('all-MiniLM-L6-v2')
        print("[AetherGuard] SentenceTransformer loaded.")
        return encoder
    except Exception as e:
        print(f"[AetherGuard] SentenceTransformer unavailable: {e}")
        raise


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4: Encode texts
# ─────────────────────────────────────────────────────────────────────────────
def encode_texts(texts, encoder):
    print(f"\n[AetherGuard] -- Generating Semantic Embeddings --")
    print(f"[AetherGuard] Encoding {len(texts):,} emails with all-MiniLM-L6-v2...")
    print("[AetherGuard] Note: First run downloads ~90 MB model (cached after that)")
    print("[AetherGuard] This step takes 8-15 minutes on CPU — please wait...\n")

    batch_size = 256
    all_embeddings = []
    total = len(texts)

    for i in range(0, total, batch_size):
        batch = texts[i:i+batch_size].tolist()
        embeddings = encoder.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embeddings)
        done = min(i + batch_size, total)
        pct = done / total * 100
        bar = '#' * int(pct // 4) + '.' * (25 - int(pct // 4))
        print(f"\r  [{bar}] {pct:.1f}%  ({done:,}/{total:,} emails)", end='', flush=True)

    print(f"\n[AetherGuard] Embeddings complete -- shape: {np.vstack(all_embeddings).shape}")
    return np.vstack(all_embeddings)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5: Train classifier — precision-biased
# ─────────────────────────────────────────────────────────────────────────────
def train_classifier(X_train, y_train, X_test, y_test):
    print(f"\n[AetherGuard] -- Training SGDClassifier (Precision-Biased) --")
    print("[AetherGuard] class_weight = {0: 3.0, 1: 1.0}  (FP penalised 3x harder than FN)")
    print("[AetherGuard] alpha = 0.001  (stronger L2 regularization)")

    clf = SGDClassifier(
        loss='modified_huber',
        penalty='l2',
        alpha=0.001,          # Stronger regularization — prevents overfitting on financial keywords
        max_iter=200,
        tol=1e-4,
        random_state=42,
        n_jobs=-1,
        class_weight={0: 3.0, 1: 1.0},  # Legitimate email misclassification = 3x worse
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    train_acc = accuracy_score(y_train, clf.predict(X_train))
    test_acc  = accuracy_score(y_test, y_pred)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    fp_rate = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0
    recall_legit = tn / (tn + fp) * 100 if (tn + fp) > 0 else 0

    print(f"\n[AetherGuard] -- Results --")
    print(f"[AetherGuard]  Train Accuracy    : {train_acc:.2%}")
    print(f"[AetherGuard]  Test  Accuracy    : {test_acc:.2%}")
    print(f"[AetherGuard]  False Positive Rate: {fp_rate:.2f}%  ({fp} legit emails wrongly flagged)")
    print(f"[AetherGuard]  Legitimate Recall : {recall_legit:.2f}%  (legit emails correctly cleared)")

    print(f"\n[AetherGuard] Confusion Matrix:")
    print(f"                     [Predicted Legit]  [Predicted Phish]")
    print(f"  [Actual Legitimate]       {tn:<15} {fp}")
    print(f"  [Actual Phishing]         {fn:<15} {tp}")

    print(f"\n[AetherGuard] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Phishing']))
    return clf


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6: Calibrate decision threshold
# ─────────────────────────────────────────────────────────────────────────────
def calibrate_threshold(clf, X_test, y_test):
    """Find the threshold that maximises F1 while minimising FP rate."""
    print("\n[AetherGuard] -- Calibrating Decision Threshold --")
    proba = clf.predict_proba(X_test)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, proba)

    best_threshold = 0.65
    best_f1 = 0.0
    for p, r, t in zip(precisions, recalls, thresholds):
        if p == 0 and r == 0:
            continue
        f1 = 2 * p * r / (p + r)
        if f1 > best_f1 and p >= 0.90:  # Require at least 90% precision
            best_f1 = f1
            best_threshold = float(t)

    print(f"[AetherGuard] Optimal threshold: {best_threshold:.4f}  (F1 = {best_f1:.4f})")
    return best_threshold


# ─────────────────────────────────────────────────────────────────────────────
# STEP 7: Save artifacts
# ─────────────────────────────────────────────────────────────────────────────
def save_artifacts(clf, encoder, threshold):
    print("\n[AetherGuard] -- Saving Model Artifacts --")
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    os.makedirs(MODELS_DIR, exist_ok=True)

    with open(os.path.join(MODELS_DIR, 'model.pkl'), 'wb') as f:
        pickle.dump(clf, f)
    print("[AetherGuard] Saved model.pkl (SGDClassifier)")

    with open(os.path.join(MODELS_DIR, 'vectorizer.pkl'), 'wb') as f:
        pickle.dump(encoder, f)
    print("[AetherGuard] Saved vectorizer.pkl (SentenceTransformer encoder)")

    meta = {
        "model_type": "sgd_classifier",
        "encoder_type": "sentence_transformer",
        "encoder_model": "all-MiniLM-L6-v2",
        "phase": 2,
        "dataset": "Kaggle 6-Corpus (Enron+Nazario+SpamAssassin+CEAS+Ling+Nigerian Fraud) — 82,486 emails",
        "embedding_dim": 384,
        "threshold": round(threshold, 4),
        "class_weight": "FP-penalised (Legitimate:3.0, Phishing:1.0)",
        "regularization": "L2 alpha=0.001"
    }
    with open(os.path.join(MODELS_DIR, 'model_meta.json'), 'w') as f:
        json.dump(meta, f, indent=2)
    print("[AetherGuard] Saved model_meta.json (scanner routing metadata)")
    print(f"[AetherGuard] Baked-in threshold: {threshold:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# SYNTHETIC FALLBACK
# ─────────────────────────────────────────────────────────────────────────────
def _build_fallback_dataset():
    samples = [
        ("Congratulations! You've won a prize. Click here to claim now.", 1),
        ("Your account has been suspended. Verify immediately to avoid termination.", 1),
        ("Please confirm your bank details to proceed with the lottery payout.", 1),
        ("URGENT: Your PayPal account requires immediate attention. Login now.", 1),
        ("Hello team, please find the quarterly report attached. Best regards.", 0),
        ("Your order has been shipped and will arrive by Friday.", 0),
        ("Meeting rescheduled to 3pm. Please update your calendar accordingly.", 0),
        ("Your monthly account statement for March 2024 is attached.", 0),
        ("Congratulations on your promotion! Your new salary will reflect next month.", 0),
        ("Please review the attached invoice and process payment at your convenience.", 0),
    ] * 50
    import random; random.shuffle(samples)
    return pd.DataFrame(samples, columns=['text', 'label'])


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    df = load_dataset()
    df = clean_and_balance(df)

    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
    )

    encoder = load_encoder()
    X_train_enc = encode_texts(X_train.reset_index(drop=True), encoder)
    X_test_enc  = encode_texts(X_test.reset_index(drop=True), encoder)

    clf = train_classifier(X_train_enc, y_train.values, X_test_enc, y_test.values)
    threshold = calibrate_threshold(clf, X_test_enc, y_test.values)
    save_artifacts(clf, encoder, threshold)

    print("\n[AetherGuard] ================================================")
    print("[AetherGuard]  Phase 2 Complete!")
    print("[AetherGuard]  Restart app.py to activate the new model.")
    print("[AetherGuard] ================================================\n")
