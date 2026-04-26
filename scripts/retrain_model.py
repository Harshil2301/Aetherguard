import os
import json
import pickle
import sys

# Ensure we can import from core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from core.database import ScanRecord
from core.scanner import MODEL_META, MODELS_DIR

def retrain():
    print("[AetherGuard] Starting active learning retraining pipeline...")
    with app.app_context():
        # Get all records with user feedback
        feedbacks = ScanRecord.query.filter(ScanRecord.user_feedback.isnot(None)).all()
        if not feedbacks:
            print("[AetherGuard] No user feedback found. Nothing to retrain.")
            return False

        texts = []
        labels = []
        
        for record in feedbacks:
            report = json.loads(record.full_report_json) if record.full_report_json else {}
            # Reconstruct the original text or use the preview if not available in the report.
            # Usually we need the full text for retraining. For this demo we'll extract it if possible.
            # In a real scenario we'd save the full text_payload in the DB or re-fetch it.
            # Here we just use the preview if the full text is not saved.
            # Actually, `full_report_json` does not contain the original text by default. 
            # We should probably save it, or just use what we have.
            # Let's assume we can add it to the report or use the preview for now.
            text = report.get('text_payload', record.payload_preview)
            
            if record.user_feedback == 'correct':
                # Label remains the same as ml_result 
                # (if it was elevated risk -> phishing=1, else legitimate=0)
                label = 1 if record.final_risk_score > 50 else 0
            elif record.user_feedback == 'false_positive':
                label = 0
            elif record.user_feedback == 'false_negative':
                label = 1
            else:
                continue

            texts.append(text)
            labels.append(label)

        print(f"[AetherGuard] Found {len(texts)} feedback samples.")

        # Load existing model and vectorizer
        try:
            with open(os.path.join(MODELS_DIR, 'model.pkl'), 'rb') as f:
                model = pickle.load(f)
            with open(os.path.join(MODELS_DIR, 'vectorizer.pkl'), 'rb') as f:
                vectorizer = pickle.load(f)
        except Exception as e:
            print(f"[AetherGuard] Error loading models: {e}")
            return False

        # Retrain using partial_fit if available (SGDClassifier supports it)
        encoder_type = MODEL_META.get('encoder_type', 'tfidf')
        
        if encoder_type == 'sentence_transformer':
            print("[AetherGuard] Encoding feedback texts with SentenceTransformer...")
            X_new = vectorizer.encode(texts, normalize_embeddings=True)
        else:
            print("[AetherGuard] Transforming feedback texts with TF-IDF...")
            X_new = vectorizer.transform(texts)

        if hasattr(model, 'partial_fit'):
            print("[AetherGuard] Applying partial_fit (active learning)...")
            # Classes are typically [0, 1]
            model.partial_fit(X_new, labels, classes=[0, 1])
            
            # Save updated model
            with open(os.path.join(MODELS_DIR, 'model.pkl'), 'wb') as f:
                pickle.dump(model, f)
            print("[AetherGuard] Model retrained and saved successfully.")
            return True
        else:
            print("[AetherGuard] The loaded model does not support partial_fit. Full retraining is required.")
            return False

if __name__ == '__main__':
    retrain()
