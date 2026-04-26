from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)  # Firebase UID or local username
    password_hash = db.Column(db.String(255), nullable=False, default='')

    # Profile
    full_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    avatar_url = db.Column(db.String(300), nullable=True)

    # Auth
    auth_provider = db.Column(db.String(20), default='local')  # local / google / facebook / phone

    # Subscription
    subscription_plan = db.Column(db.String(20), default='free')  # free / pro / enterprise

    # Integrations
    api_key = db.Column(db.String(64), unique=True, nullable=True)
    webhook_url = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "avatar_url": self.avatar_url,
            "auth_provider": self.auth_provider,
            "subscription_plan": self.subscription_plan,
            "api_key": self.api_key,
            "webhook_url": self.webhook_url,
            "created_at": self.created_at.isoformat() + 'Z' if self.created_at else None,
            "last_login": self.last_login.isoformat() + 'Z' if self.last_login else None,
        }

class ScanRecord(db.Model):
    __tablename__ = 'scan_records'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 40-character snippet to display what was scanned
    payload_preview = db.Column(db.String(100))
    
    # Core metrics
    final_risk_score = db.Column(db.Integer, default=0)
    ml_confidence_pct = db.Column(db.Float, default=0.0)
    
    # High-level Flags
    has_failed_auth = db.Column(db.Boolean, default=False)
    vt_malicious_hits = db.Column(db.Integer, default=0)
    
    # Full JSON dump of the payload report for deeper analysis
    full_report_json = db.Column(db.Text, nullable=True)

    # Link to the user who ran this scan (nullable — legacy scans and public scans have no owner)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # User feedback for active learning (e.g., 'correct', 'false_positive', 'false_negative')
    user_feedback = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        # Append 'Z' to natively force Javascript into treating the ISO string as strict UTC
        ts_str = self.timestamp.isoformat()
        if not ts_str.endswith('Z') and '+' not in ts_str:
            ts_str += 'Z'
            
        return {
            "id": self.id,
            "timestamp": ts_str,
            "payload_preview": self.payload_preview,
            "final_risk_score": self.final_risk_score,
            "ml_confidence_pct": self.ml_confidence_pct,
            "has_failed_auth": self.has_failed_auth,
            "vt_malicious_hits": self.vt_malicious_hits,
            "user_id": self.user_id,
            "user_feedback": self.user_feedback,
        }
