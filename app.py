import os
import io
import json
import zipfile
import requests
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from core.scanner import scan_payload, model, vectorizer
from core.database import db, ScanRecord, User
from core.alerts import send_webhook_alert

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — env vars must be set manually

# Initialize Flask app
# Serve static files directly from frontend directory
app = Flask(__name__, static_folder='frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aetherguard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'AETHERGUARD_ENTERPRISE_KEY_2026_X'
db.init_app(app)
CORS(app, origins=[
    'http://localhost:3000', 
    'http://127.0.0.1:3000', 
    'http://localhost:5173',
    'https://mail.google.com',
    'https://outlook.live.com',
    'https://outlook.office.com',
    'https://mail.yahoo.com'
], supports_credentials=True)

# Allow Chrome extension fetch requests (their Origin is chrome-extension://...)
@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin', '')
    if origin.startswith('chrome-extension://'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@app.route('/api/scan', methods=['OPTIONS'])
@app.route('/api/telemetry/stats', methods=['OPTIONS'])
@app.route('/api/history', methods=['OPTIONS'])
def handle_preflight():
    response = jsonify({})
    origin = request.headers.get('Origin', '')
    if origin.startswith('chrome-extension://'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response, 200

with app.app_context():
    db.create_all()
    # Safe migration: add user_id column if it doesn't exist yet
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE scan_records ADD COLUMN user_id INTEGER REFERENCES users(id)'))
            conn.commit()
    except Exception:
        pass  # Column already exists — safe to ignore
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE scan_records ADD COLUMN user_feedback VARCHAR(20)'))
    except Exception:
        pass  # Column already exists — safe to ignore
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE users ADD COLUMN api_key VARCHAR(64)'))
            conn.commit()
    except Exception:
        pass
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE users ADD COLUMN webhook_url VARCHAR(255)'))
            conn.commit()
    except Exception:
        pass  # Column already exists — safe to ignore
    if not User.query.filter_by(username='admin').first():
        hashed = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode('utf-8')
        db.session.add(User(username='admin', password_hash=hashed))
        db.session.commit()

# ==========================================
# AUTOMATED ML RETRAINING SCHEDULER
# ==========================================
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

def scheduled_retrain_job():
    """Runs the ML active learning retrain loop and hot-swaps the model if successful."""
    with app.app_context():
        try:
            from scripts.retrain_model import retrain
            from core.scanner import reload_ml_engine
            success = retrain()
            if success:
                reload_ml_engine()
        except Exception as e:
            print(f"[AetherGuard] Scheduler Error during retrain: {e}")

# Only run scheduler if not in Werkzeug auto-reload subprocess
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    scheduler = BackgroundScheduler()
    # Run every night at midnight
    scheduler.add_job(func=scheduled_retrain_job, trigger="cron", hour=0, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())

# ==========================================
# AUTHENTICATION MIDDLEWARE
# ==========================================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Try X-API-Key header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            if User.query.filter_by(api_key=api_key).first():
                return f(*args, **kwargs)

        # 2. Try Authorization Bearer
        token = request.headers.get('Authorization', '')
        if not token:
            return jsonify({'error': 'Unauthorized: Token or API Key is missing!'}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            # API Key as Bearer
            if len(token) == 64 and '.' not in token:
                if User.query.filter_by(api_key=token).first():
                    return f(*args, **kwargs)

            # Admin Mock Bypass
            if token == 'admin_mock_token_123':
                return f(*args, **kwargs)

            # AetherGuard JWT (fast path)
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
                if User.query.filter_by(username=data.get('user')).first():
                    return f(*args, **kwargs)
            except Exception:
                pass

            # Firebase ID token (Google SSO fallback — slower but handles social login)
            if token.count('.') == 2 and len(token) > 200:
                print(f"[AUTH] Detected Firebase token length {len(token)}...")
                if _resolve_firebase_token(token):
                    return f(*args, **kwargs)
                else:
                    print(f"[AUTH] _resolve_firebase_token returned None!")

            print("[AUTH] Token validation failed all checks.")
            return jsonify({'error': 'Unauthorized: Token is invalid!'}), 401

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Token error: {e}")
            return jsonify({'error': 'Unauthorized: Token is invalid!', 'details': str(e)}), 401
    return decorated


import time
_firebase_token_cache = {}

import json
import base64

def _resolve_firebase_token(token):
    """Decode a Firebase ID token locally to avoid Google API network timeouts."""
    if token in _firebase_token_cache:
        cached_user, expiry = _firebase_token_cache[token]
        if time.time() < expiry:
            return cached_user
            
    try:
        # A JWT is: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            print("[AUTH] Invalid JWT structure.")
            return None
            
        payload_b64 = parts[1]
        # Pad base64 string
        payload_b64 += '=' * (-len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
        
        uid = claims.get('user_id') or claims.get('sub', '')
        email = claims.get('email', '')
        name = claims.get('name', email.split('@')[0] if email else uid[:8])
        
        if not uid:
            print("[AUTH] Token missing user_id/sub claim.")
            return None
            
        user = User.query.filter_by(username=uid).first()
        if not user:
            user = User(username=uid, email=email, full_name=name,
                        auth_provider='google', password_hash='')
            db.session.add(user)
            db.session.commit()
            
        _firebase_token_cache[token] = (user, time.time() + 3600)  # cache for 1 hour
        return user
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[AUTH] _resolve_firebase_token error: {e}")
        return None

def get_user_from_token():
    """Silently try to resolve the current user from the Authorization or X-API-Key header.
    Handles: AetherGuard JWT, API Key, and raw Firebase ID tokens (Google SSO fallback).
    Returns a User object or None — never raises."""
    try:
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return User.query.filter_by(api_key=api_key).first()
            
        raw = request.headers.get('Authorization', '')
        token = raw.replace('Bearer ', '').strip()
        if not token:
            return None
            
        # API Key passed as Bearer
        if len(token) == 64 and '.' not in token:
            return User.query.filter_by(api_key=token).first()

        # Admin Mock Bypass (return None so they get unrestricted global access)
        if token == 'admin_mock_token_123':
            return None

        # Try AetherGuard JWT first (fast, no network call)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return User.query.filter_by(username=data.get('user')).first()
        except Exception:
            pass

        # Fallback: Firebase ID token (Google SSO path)
        # Firebase tokens are long JWTs with 3 segments — AetherGuard JWTs also have 3
        # but they'll fail the decode above, so this catches the Google fallback case
        if token.count('.') == 2 and len(token) > 200:
            return _resolve_firebase_token(token)

        return None
    except Exception:
        return None

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing credentials'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        # Encode JWT token valid for 8 hours
        token = jwt.encode({
            'user': user.username,
            'exp': datetime.now(timezone.utc) + timedelta(hours=8)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({'token': token, 'username': user.username})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/social', methods=['POST'])
def api_social_auth():
    """
    Accepts a Firebase ID Token, decodes it locally (no network call),
    creates/updates the user record, and returns an AetherGuard JWT.
    """
    data = request.json or {}
    id_token = data.get('id_token')
    provider = data.get('provider', 'google')
    if not id_token:
        return jsonify({'error': 'Missing id_token'}), 400
    try:
        # Fast local base64 decode — no Google network call needed
        parts = id_token.split('.')
        if len(parts) != 3:
            return jsonify({'error': 'Malformed JWT'}), 400

        payload_b64 = parts[1]
        payload_b64 += '=' * (-len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))

        uid   = claims.get('user_id') or claims.get('sub', '')
        email = claims.get('email', '')
        name  = claims.get('name', email.split('@')[0] if email else uid[:8])

        if not uid:
            return jsonify({'error': 'Token missing user identifier'}), 401

        # Create or update the user record
        user = User.query.filter_by(username=uid).first()
        if not user:
            user = User(
                username=uid, email=email, full_name=name,
                auth_provider=provider, password_hash=''
            )
            db.session.add(user)
        else:
            if name and not user.full_name:
                user.full_name = name
            if email and not user.email:
                user.email = email

        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        # Issue an AetherGuard JWT so the React dashboard can use it normally
        aether_token = jwt.encode({
            'user': uid,
            'exp': datetime.now(timezone.utc) + timedelta(hours=8)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token': aether_token, 'username': name or email, 'user_id': user.id})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': f'Token processing failed: {str(e)}'}), 401


@app.route('/api/profile', methods=['GET'])
@token_required
def api_get_profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    user = User.query.filter_by(username=data['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    total_scans = ScanRecord.query.count()
    threats = ScanRecord.query.filter(ScanRecord.final_risk_score >= 70).count()
    return jsonify({**user.to_dict(), 'total_scans': total_scans, 'threats_detected': threats})

@app.route('/api/profile', methods=['PUT'])
@token_required
def api_update_profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    data_tok = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    user = User.query.filter_by(username=data_tok['user']).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    body = request.json or {}
    if 'full_name' in body:
        user.full_name = body['full_name'][:80]
    if 'avatar_url' in body:
        user.avatar_url = body['avatar_url'][:300]
    db.session.commit()
    return jsonify(user.to_dict())
# ==========================================



@app.route('/api/scan', methods=['POST'])
def api_scan():
    try:
        text_payload = request.form.get('text', '')

        file_bytes = None
        filename = ''
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file_bytes = file.read()
                filename = file.filename

        # Resolve the current user (if token is sent — silently ignored if not)
        current_user = get_user_from_token()

        # Send to scanner engine
        result = scan_payload(text_payload=text_payload, file_bytes=file_bytes, filename=filename)

        # Save to database
        preview = text_payload[:60] if text_payload else (filename if filename else "Empty Payload")
        vt_hits = sum(u.get('malicious_hits', 0) for u in result.get('vt_urls', []))

        record = ScanRecord(
            payload_preview=preview,
            final_risk_score=result.get('final_risk_score', 0),
            ml_confidence_pct=result.get('ml_classification_confidence', 0.0) * 100,
            has_failed_auth=any(v == 'fail' for v in result.get('headers_status', {}).values()),
            vt_malicious_hits=vt_hits,
            full_report_json=json.dumps(result),
            user_id=current_user.id if current_user else None,
        )
        db.session.add(record)
        db.session.commit()

        # PHASE 4: Alerting Logic — fire for dashboard scans AND Gmail extension scans
        source = request.headers.get('X-Scan-Source', 'Dashboard')
        if record.final_risk_score >= 60:  # Lower threshold to catch SUSPICIOUS too
            user_webhook = current_user.webhook_url if current_user else None
            # Always fire global DISCORD_WEBHOOK_URL if per-user webhook not set
            send_webhook_alert(record, user_webhook, source=source)

        result['scan_id'] = record.id
        return jsonify(result)

    except Exception as e:
        print(f"Error during scan: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scan/bulk', methods=['POST'])
def api_scan_bulk():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files provided"}), 400
            
        files = request.files.getlist('files')
        # Limit to 50 files
        files = files[:50]
        
        current_user = get_user_from_token()
        results = []
        
        for file in files:
            if file.filename == '':
                continue
                
            file_bytes = file.read()
            filename = file.filename
            
            # Scan
            result = scan_payload(file_bytes=file_bytes, filename=filename)
            
            # Save to database
            preview = filename
            vt_hits = sum(u.get('malicious_hits', 0) for u in result.get('vt_urls', []))
            
            record = ScanRecord(
                payload_preview=preview,
                final_risk_score=result.get('final_risk_score', 0),
                ml_confidence_pct=result.get('ml_classification_confidence', 0.0) * 100,
                has_failed_auth=any(v == 'fail' for v in result.get('headers_status', {}).values()),
                vt_malicious_hits=vt_hits,
                full_report_json=json.dumps(result),
                user_id=current_user.id if current_user else None,
            )
            db.session.add(record)
            db.session.flush() # To get the id without committing yet
            
            if record.final_risk_score >= 70:
                user_webhook = current_user.webhook_url if current_user else None
                send_webhook_alert(record, user_webhook)
                
            result['scan_id'] = record.id
            result['filename'] = filename
            results.append(result)
            
        db.session.commit()
        return jsonify({"results": results})
        
    except Exception as e:
        print(f"Error during bulk scan: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scan/<int:scan_id>/feedback', methods=['POST'])
def api_feedback(scan_id):
    """Stores user feedback for active learning. Works with any token (JWT or Firebase)."""
    try:
        feedback = request.json.get('feedback')
        if feedback not in ('correct', 'false_positive', 'false_negative'):
            return jsonify({"error": "Invalid feedback type"}), 400

        record = ScanRecord.query.get(scan_id)
        if not record:
            return jsonify({"error": "Scan not found"}), 404

        # Any user (authenticated or not) can submit feedback for active learning
        record.user_feedback = feedback
        db.session.commit()
        return jsonify({"success": True, "message": "Feedback recorded."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
@token_required
def api_status():
    """Returns system health for the Telemetry Node view."""
    vt_key = os.environ.get("VT_API_KEY", "")
    return jsonify({
        "node": "AetherGuard v1.0",
        "ml_loaded": model is not None and vectorizer is not None,
        "vt_api_active": len(vt_key) > 0,
        "gateway_status": "ONLINE"
    })

@app.route('/api/history', methods=['GET'])
@token_required
def api_history():
    """Returns the 50 most recent scans. Admin sees all; regular users see ONLY their own."""
    try:
        limit = int(request.args.get('limit', 50))
        current_user = get_user_from_token()
        query = ScanRecord.query
        if current_user and current_user.username != 'admin':
            # Show ONLY scans belonging to this user
            query = query.filter(ScanRecord.user_id == current_user.id)
        records = query.order_by(ScanRecord.timestamp.desc()).limit(limit).all()
        return jsonify([r.to_dict() for r in records])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/telemetry/stats', methods=['GET'])
@token_required
def api_telemetry_stats():
    """Returns per-user scan stats for the Telemetry Node dashboard."""
    try:
        current_user = get_user_from_token()
        if current_user and current_user.username != 'admin':
            base = ScanRecord.query.filter(ScanRecord.user_id == current_user.id)
        else:
            base = ScanRecord.query
        total = base.count()
        threats = base.filter(ScanRecord.final_risk_score > 60).count()
        warnings = base.filter(
            ScanRecord.final_risk_score > 30, ScanRecord.final_risk_score <= 60
        ).count()
        safe = base.filter(ScanRecord.final_risk_score <= 30).count()
        return jsonify({
            "total_scans": total,
            "threats": threats,
            "warnings": warnings,
            "safe": safe,
            "ml_loaded": model is not None and vectorizer is not None,
            "gateway_status": "ONLINE"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/feedback/stats', methods=['GET'])
@token_required
def api_feedback_stats():
    """Returns aggregate feedback counts for the transparency dashboard."""
    try:
        current_user = get_user_from_token()
        from sqlalchemy import func
        correct = ScanRecord.query.filter_by(user_feedback='correct').count()
        false_positive = ScanRecord.query.filter_by(user_feedback='false_positive').count()
        false_negative = ScanRecord.query.filter_by(user_feedback='false_negative').count()
        total_with_feedback = correct + false_positive + false_negative
        total_scans = ScanRecord.query.count()
        return jsonify({
            "correct": correct,
            "false_positive": false_positive,
            "false_negative": false_negative,
            "total_with_feedback": total_with_feedback,
            "total_scans": total_scans,
            "accuracy_pct": round((correct / total_with_feedback * 100) if total_with_feedback > 0 else 0, 1)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/yara', methods=['GET'])
@token_required
def get_yara_rules():
    """Returns the custom YARA rule file contents."""
    current_user = get_user_from_token()
    if not current_user or current_user.username != 'admin':
        return jsonify({"error": "Admin access required"}), 403
        
    try:
        yara_dir = os.path.join(os.path.dirname(__file__), 'core', 'yara_rules')
        custom_rule_path = os.path.join(yara_dir, 'custom_rules.yar')
        if os.path.exists(custom_rule_path):
            with open(custom_rule_path, 'r') as f:
                content = f.read()
        else:
            content = "// Write your custom YARA rules here.\n// Example:\n// rule SuspiciousString {\n//   strings: $a = \"malware\"\n//   condition: $a\n// }\n"
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/yara', methods=['POST'])
@token_required
def update_yara_rules():
    """Updates the custom YARA rule file and reloads the engine."""
    from core.scanner import reload_yara_engine
    
    current_user = get_user_from_token()
    if not current_user or current_user.username != 'admin':
        return jsonify({"error": "Admin access required"}), 403
        
    try:
        content = request.json.get('content')
        if content is None:
            return jsonify({"error": "No content provided"}), 400
            
        yara_dir = os.path.join(os.path.dirname(__file__), 'core', 'yara_rules')
        os.makedirs(yara_dir, exist_ok=True)
        custom_rule_path = os.path.join(yara_dir, 'custom_rules.yar')
        
        with open(custom_rule_path, 'w') as f:
            f.write(content)
            
        success, msg = reload_yara_engine()
        if success:
            return jsonify({"success": True, "message": "YARA rules updated and engine reloaded."})
        else:
            return jsonify({"error": f"Failed to compile YARA rules: {msg}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import secrets
@app.route('/api/settings/apikey', methods=['POST'])
@token_required
def generate_api_key():
    """Generates a new API key for the current user."""
    try:
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 403
            
        new_key = secrets.token_hex(32) # 64 char string
        current_user.api_key = new_key
        db.session.commit()
        return jsonify({"success": True, "api_key": new_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings/webhook', methods=['PUT'])
@token_required
def update_webhook():
    """Updates the user's webhook URL for alerts."""
    try:
        current_user = get_user_from_token()
        if not current_user:
            return jsonify({"error": "Unauthorized"}), 403
            
        webhook_url = request.json.get('webhook_url', '')
        # Basic validation
        if webhook_url and not webhook_url.startswith('http'):
            return jsonify({"error": "Invalid webhook URL"}), 400
            
        current_user.webhook_url = webhook_url
        db.session.commit()
        return jsonify({"success": True, "webhook_url": current_user.webhook_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/extension/download', methods=['GET'])
def download_extension():
    """Zip and serve the browser extension folder for download."""
    extension_dir = os.path.join(os.path.dirname(__file__), 'extension')
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extension_dir):
            for fname in files:
                file_path = os.path.join(root, fname)
                arcname = os.path.relpath(file_path, extension_dir)
                zf.write(file_path, arcname)
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='aetherguard-extension.zip'
    )

# ==========================================
# STATIC FRONTEND SERVING (React Dashboard)
# ==========================================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serves the built React SPA from the frontend/ folder."""
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Fallback to index.html for React Router
        if os.path.exists(os.path.join(app.static_folder, 'index.html')):
            return send_from_directory(app.static_folder, 'index.html')
        else:
            return "Dashboard not built. Run 'npm run build' in client/ and move dist/ to frontend/", 404

if __name__ == '__main__':
    import sys
    dev_mode = '--dev' in sys.argv or os.environ.get('AETHERGUARD_ENV') == 'development'

    print("=" * 55)
    print("   AetherGuard Security Gateway — STARTING UP")
    print("=" * 55)

    if dev_mode:
        print("[MODE] Development (Flask auto-reload enabled)")
        print("[URL]  http://localhost:5000")
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        # ── PRODUCTION: Waitress WSGI multi-threaded server ──
        try:
            from waitress import serve
            threads = int(os.environ.get('AETHERGUARD_THREADS', 8))
            host   = os.environ.get('AETHERGUARD_HOST', '127.0.0.1')
            port   = int(os.environ.get('AETHERGUARD_PORT', 5000))
            print(f"[MODE]    Production (Waitress WSGI — {threads} threads)")
            print(f"[URL]     http://localhost:{port}")
            print(f"[DB]      {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"[THREADS] {threads} concurrent workers")
            print("=" * 55)
            serve(app, host=host, port=port, threads=threads,
                  channel_timeout=120,
                  connection_limit=500,
                  cleanup_interval=30)
        except ImportError:
            print("[WARN] waitress not installed — falling back to Flask dev server.")
            print("[TIP]  Run: pip install waitress")
            app.run(debug=False, host='127.0.0.1', port=5000)

