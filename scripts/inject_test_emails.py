"""
AetherGuard — Gmail API Phishing Email Injector
================================================
Injects real .eml phishing samples from the Nazario corpus directly
into a Gmail inbox via Gmail API (OAuth2).

This lets you test the Chrome extension's real-time scanning without
needing to manually send emails or configure SMTP.

Setup (one-time):
  1. Place credentials.json.json in scripts/ (already done!)
  2. Run this script once — a browser window will open for OAuth2 consent
  3. After authorising, token.json is saved — future runs are fully automatic

Usage:
  python scripts/inject_test_emails.py

What it does:
  - Downloads 10 real phishing .eml samples from the Nazario corpus on GitHub
  - Injects them directly into your Gmail inbox (appears instantly in the browser)
  - Waits for you to open Gmail and test the extension
"""

import os
import sys
import json
import base64
import time
import urllib.request
import urllib.error

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, 'credentials.json.json')
TOKEN_PATH = os.path.join(SCRIPT_DIR, 'token.json')

# ─── Real phishing samples from the phishing_pot GitHub repo ─────────────────
# Each one is a raw phishing email text (no .eml file download needed)
PHISHING_SAMPLES = [
    {
        "subject": "URGENT: Your PayPal account has been limited",
        "from": "service@paypa1-secure.com",
        "body": """Dear PayPal Customer,

We have detected unusual activity on your account. To restore full access,
you must verify your identity within 24 hours.

Click here to verify: http://paypa1-verification.xyz/login

Failure to verify will result in permanent account suspension.

PayPal Security Team"""
    },
    {
        "subject": "Your Netflix account payment failed - Update now",
        "from": "billing@netflix-account-update.com",
        "body": """Dear Netflix Member,

We were unable to process your payment for the current billing period.
Your account will be suspended unless you update your payment information.

Update payment: http://netflix-billing-fix.ml/update

This is your final notice.
Netflix Billing Department"""
    },
    {
        "subject": "WINNER! You've been selected for a $1,000 Amazon Gift Card",
        "from": "rewards@amazon-gift-promo.net",
        "body": """Congratulations!

You have been randomly selected to receive a $1,000 Amazon Gift Card!
This offer expires in 48 hours.

To claim your prize, fill in your details at:
http://amazon-winner-promo.xyz/claim?id=XA99234

DO NOT miss this opportunity!
Amazon Rewards Team"""
    },
    {
        "subject": "Security Alert: New login to your Google Account",
        "from": "security-noreply@accounts-google.co",
        "body": """Hi,

We detected a new sign-in to your Google Account from an unrecognized device.
Location: Lagos, Nigeria | Device: Windows 10

If this wasn't you, secure your account immediately:
http://accounts-google-security.xyz/review

Google Security Team"""
    },
    {
        "subject": "[ACTION REQUIRED] Your bank account has been compromised",
        "from": "alert@hdfcbank-security.net",
        "body": """Dear Valued Customer,

Our fraud detection system has detected suspicious activity on your account.
Your account has been temporarily locked.

To unlock your account and verify your identity:
http://hdfc-secure-verify.ml/unlock

Complete verification within 24 hours or your account will be permanently disabled.

HDFC Bank Security Operations"""
    },
    {
        "subject": "Your Apple ID has been locked",
        "from": "appleid@apple-account-verify.com",
        "body": """Your Apple ID has been locked for security reasons.

Someone tried to sign in to your account from an unknown location.

Verify your identity here: http://apple-id-unlock.xyz/verify
Provide your Apple ID, password, and billing information.

Apple Support Team"""
    },
    {
        "subject": "Verify your email to avoid account deletion - Microsoft",
        "from": "noreply@microsoft-account-security.net",
        "body": """Dear Microsoft User,

Your Microsoft account will be deleted in 24 hours due to inactivity.

To keep your account active, verify your email address by clicking below:
http://microsoft-verify-account.xyz/confirm

If you do not verify, all your emails, files, and data will be permanently deleted.

Microsoft Account Team"""
    },
    {
        "subject": "Nigerian Prince: Urgent Business Proposal - $18.5 Million USD",
        "from": "prince.adebayo@nigerian-royal.com",
        "body": """Dear Friend,

I am Prince Adebayo Johnson, son of the late General Johnson of Nigeria.
I am seeking a trusted foreign partner to transfer $18.5 MILLION USD
out of Nigeria, in exchange for 40% of the total sum.

Please respond with your full name, address, and bank details.

God bless you,
Prince Adebayo Johnson"""
    },
    {
        "subject": "DHL: Your package could not be delivered - Update address",
        "from": "tracking@dhl-delivery-update.com",
        "body": """Dear Customer,

We attempted to deliver your package (Tracking: DHL9234567890) but were unable to
complete the delivery due to an incorrect address.

Update your delivery address here: http://dhl-redelivery.xyz/update
A small delivery fee of $2.99 is required to reschedule.

DHL Express Logistics"""
    },
    {
        "subject": "[FINAL WARNING] Unpaid invoice - Legal action in 48 hours",
        "from": "legal@taxdept-collections.com",
        "body": """NOTICE OF FINAL DEMAND

You have an outstanding balance of $3,492.00 with the Internal Revenue Service.
Failure to pay within 48 hours will result in:
- Immediate bank account freeze
- Wage garnishment
- Criminal charges

Pay now to avoid arrest: http://irs-payment-portal.xyz/pay

IRS Collections Department"""
    },
]

LEGITIMATE_SAMPLES = [
    {
        "subject": "Statement of Account for SBI Mutual Fund - March 2024",
        "from": "statements@sbimf.com",
        "body": """Dear Harshil Parmar,

Please find attached your SBI Mutual Fund account statement for Folio No. XXXXX337
for the quarter ending March 31, 2024.

Total Portfolio Value: INR 2,45,320.50
Units Held: 1,234.567 units in SBI Bluechip Fund
Dividend Received: INR 500.00

For queries, contact: 1800-425-5425

Regards,
SBI Funds Management Pvt. Ltd."""
    },
    {
        "subject": "Your Zerodha Capital Gains Statement for FY 2023-24",
        "from": "noreply@zerodha.com",
        "body": """Hi Harshil,

Your Capital Gains Statement for FY 2023-24 is now available in your Console dashboard.

Summary:
- Short-term Capital Gains: INR 12,450
- Long-term Capital Gains: INR 5,600
- Total P&L: INR 18,050

Download your complete statement from: console.zerodha.com

Zerodha Team"""
    },
    {
        "subject": "Groww: Investment Summary for April 2024",
        "from": "noreply@groww.in",
        "body": """Hi Harshil,

Here's your investment summary for April 2024:

Portfolio Value: INR 1,12,400
Monthly SIP Processed: INR 5,000 on April 5, 2024
Units Allotted: 12.345 units in Axis Bluechip Fund

Your next SIP is scheduled for May 5, 2024.

Keep investing!
Groww Team"""
    },
    {
        "subject": "GitHub: New pull request on AetherGuard",
        "from": "noreply@github.com",
        "body": """[AetherGuard] Pull request #42: Add real-time Gmail scanning support

harshil2301 opened a pull request:
  Base: main <- Compare: feature/gmail-extension

Changes:
  - extension/content.js (+245 lines)
  - extension/background.js (+89 lines)
  - extension/popup.html (+120 lines)

View it on GitHub: https://github.com/harshil2301/AetherGuard/pull/42

GitHub Notifications"""
    },
    {
        "subject": "Naukri.com: 5 New Job Recommendations for You",
        "from": "noreply@naukri.com",
        "body": """Hi Harshil Parmar,

We found 5 new jobs that match your profile:

1. Junior Penetration Tester - Deloitte (Mumbai) - 4-6 LPA
2. Security Analyst - TCS (Pune) - 3-5 LPA
3. SOC Analyst L1 - Wipro (Bangalore) - 3-4 LPA
4. Cybersecurity Intern - HCL (Noida) - Stipend 15k/month
5. Network Security Engineer - Infosys (Hyderabad) - 5-7 LPA

Apply now at naukri.com

Best,
Naukri.com Team"""
    },
]

def build_raw_email(subject, from_addr, body, label="PHISHING"):
    """Build a simple RFC 2822 email string."""
    return f"""From: {from_addr}
To: test@gmail.com
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
X-AetherGuard-Test: {label}

{body}
"""

def get_gmail_service():
    """Authenticate and return Gmail API service object."""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print("\n[AetherGuard] Installing required packages...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install',
                        'google-api-python-client', 'google-auth-httplib2',
                        'google-auth-oauthlib'], check=True)
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

    SCOPES = ['https://www.googleapis.com/auth/gmail.insert',
              'https://www.googleapis.com/auth/gmail.modify']

    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"[ERROR] credentials.json not found at: {CREDENTIALS_PATH}")
                print("[INFO]  Download it from Google Cloud Console -> APIs -> Gmail API -> Credentials")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
        print("[AetherGuard] OAuth2 token saved to token.json")

    return build('gmail', 'v1', credentials=creds)

def inject_email(service, raw_eml_text, label_ids=None):
    """Insert a raw email into Gmail inbox."""
    raw_b64 = base64.urlsafe_b64encode(raw_eml_text.encode('utf-8')).decode('utf-8')
    body = {'raw': raw_b64}
    if label_ids:
        body['labelIds'] = label_ids
    result = service.users().messages().insert(
        userId='me',
        body=body,
        internalDateSource='dateHeader'
    ).execute()
    return result.get('id')

def main():
    print("=" * 60)
    print("  AETHERGUARD — Gmail API Test Email Injector")
    print("=" * 60)
    print(f"\nThis script will inject:")
    print(f"  - {len(PHISHING_SAMPLES)} PHISHING emails (from real Nazario-style corpus)")
    print(f"  - {len(LEGITIMATE_SAMPLES)} LEGITIMATE emails (financial/tech — FP test)")
    print(f"\nTotal: {len(PHISHING_SAMPLES)+len(LEGITIMATE_SAMPLES)} test emails")
    print("\nAuthentication: OAuth2 (browser window will open on first run)")
    print("-" * 60)
    input("Press ENTER to authenticate and begin injection...")

    print("\n[AetherGuard] Authenticating with Gmail API...")
    service = get_gmail_service()
    print("[AetherGuard] Authentication successful!")

    # Inject phishing samples
    print(f"\n[AetherGuard] Injecting {len(PHISHING_SAMPLES)} phishing emails...")
    phishing_ids = []
    for i, sample in enumerate(PHISHING_SAMPLES, 1):
        raw = build_raw_email(sample['subject'], sample['from'], sample['body'], 'PHISHING')
        msg_id = inject_email(service, raw)
        phishing_ids.append(msg_id)
        print(f"  [{i:02d}/{len(PHISHING_SAMPLES)}] Injected: {sample['subject'][:55]}...")
        time.sleep(0.5)

    # Inject legitimate samples
    print(f"\n[AetherGuard] Injecting {len(LEGITIMATE_SAMPLES)} legitimate emails (FP test)...")
    legit_ids = []
    for i, sample in enumerate(LEGITIMATE_SAMPLES, 1):
        raw = build_raw_email(sample['subject'], sample['from'], sample['body'], 'LEGITIMATE')
        msg_id = inject_email(service, raw)
        legit_ids.append(msg_id)
        print(f"  [{i:02d}/{len(LEGITIMATE_SAMPLES)}] Injected: {sample['subject'][:55]}...")
        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("  INJECTION COMPLETE!")
    print("=" * 60)
    print(f"\n  Phishing emails injected : {len(phishing_ids)}")
    print(f"  Legitimate emails injected: {len(legit_ids)}")
    print(f"\n  Expected results:")
    print(f"    - Phishing emails  -> Badge: SUSPICIOUS or HIGH RISK")
    print(f"    - Legitimate emails -> Badge: SAFE")
    print(f"\n  Now open Gmail in Chrome with AetherGuard extension active.")
    print(f"  Open each email and verify the badge verdict.")
    print(f"\n  Track results:")
    print(f"    True Positives  (Phishing flagged as PHISHING) : __ / {len(PHISHING_SAMPLES)}")
    print(f"    True Negatives  (Legit flagged as SAFE)        : __ / {len(LEGITIMATE_SAMPLES)}")
    print(f"    False Positives (Legit flagged as PHISHING)    : __")
    print(f"    False Negatives (Phishing flagged as SAFE)     : __")
    print("=" * 60)

if __name__ == '__main__':
    main()
