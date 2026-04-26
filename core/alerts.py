import os
import requests
import threading
from datetime import datetime


def _send_discord_payload(webhook_url, record_dict, source='Dashboard'):
    """Internal function running inside a thread to dispatch the POST request."""
    try:
        score = record_dict.get('final_risk_score', 0)

        # Colour and severity label based on score
        if score >= 70:
            colour = 15548997   # Red
            severity = '🚨 CRITICAL THREAT'
            description = '**High-severity phishing payload detected and quarantined by ML & YARA Sandbox.**'
        elif score >= 40:
            colour = 16744272   # Orange
            severity = '⚡ SUSPICIOUS EMAIL'
            description = '**Email flagged as suspicious. Manual review recommended.**'
        else:
            colour = 3066993    # Green
            severity = '✅ LOW RISK'
            description = '**Email cleared with low risk score.**'

        embed = {
            'title': f'AETHERGUARD — {severity}',
            'description': description,
            'color': colour,
            'fields': [
                {
                    'name': '📧 Payload Preview',
                    'value': f"```\n{str(record_dict.get('payload_preview', 'N/A'))[:200]}\n```",
                    'inline': False
                },
                {
                    'name': '⚠️ Risk Score',
                    'value': f"**{score} / 100**",
                    'inline': True
                },
                {
                    'name': '🤖 ML Confidence',
                    'value': f"{record_dict.get('ml_confidence_pct', 0.0):.1f}%",
                    'inline': True
                },
                {
                    'name': '🔗 VT Flags',
                    'value': f"{record_dict.get('vt_malicious_hits', 0)} malicious",
                    'inline': True
                },
                {
                    'name': '📍 Scan Source',
                    'value': source,
                    'inline': True
                },
            ],
            'footer': {
                'text': 'AetherGuard Threat Intelligence Node — Real-Time Email Security',
                'icon_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Shield-icon.svg/1024px-Shield-icon.svg.png'
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        payload = {
            'username': 'AetherGuard SOC',
            'avatar_url': 'https://img.icons8.com/color/48/000000/cyber-security.png',
            'embeds': [embed]
        }

        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code not in (200, 204):
            print(f'[AetherGuard] Webhook failed with status: {response.status_code}')
        else:
            print(f'[AetherGuard] Discord alert sent for score {score} from {source}')
    except Exception as e:
        print(f'[AetherGuard] Error dispatching Webhook: {e}')


def send_webhook_alert(record, user_webhook_url=None, source='Dashboard'):
    """
    Spawns a non-blocking background thread to execute the webhook alert if
    a webhook URL is provided or DISCORD_WEBHOOK_URL is populated in the .env file.
    """
    webhook_url = user_webhook_url or os.environ.get('DISCORD_WEBHOOK_URL', '').strip()
    if not webhook_url:
        return

    # Convert SQLAlchemy model to dict to avoid session thread sharing issues
    record_dict = record
    if hasattr(record, 'to_dict'):
        record_dict = record.to_dict()

    t = threading.Thread(target=_send_discord_payload, args=(webhook_url, record_dict, source))
    t.daemon = True
    t.start()
