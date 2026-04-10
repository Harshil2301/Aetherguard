import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
import pickle

def create_and_train_model():
    print("[AetherGuard] Building enhanced training dataset (110 examples)...")

    data = [
        # ==================================================
        # PHISHING EMAILS — label: 1
        # ==================================================
        # Account / Identity Theft
        {"text": "URGENT: Your account has been suspended. Click here to verify your details immediately.", "label": 1},
        {"text": "Warning: Unauthorized login attempt detected. Reset your password at http://bit.ly/secure-login", "label": 1},
        {"text": "Your PayPal account is limited. Provide your SSN to restore access immediately.", "label": 1},
        {"text": "Verify your Apple ID within 24 hours or your device will be permanently locked.", "label": 1},
        {"text": "Your Netflix account has been suspended due to billing issues. Update your payment here.", "label": 1},
        {"text": "SECURITY ALERT: Unusual activity detected. Confirm your identity now or account will be closed.", "label": 1},
        {"text": "Your Amazon account will be closed. Click the link immediately to prevent suspension.", "label": 1},
        {"text": "FINAL WARNING: Your bank account has been flagged for suspicious activity. Act now.", "label": 1},
        {"text": "Your Google account will be disabled in 48 hours unless you verify your information.", "label": 1},
        {"text": "URGENT: Your credit card has been compromised. Call us immediately to protect your account.", "label": 1},
        {"text": "Your account has been accessed from an unknown device. Verify your identity to secure your account.", "label": 1},
        {"text": "Microsoft: Your subscription has expired. Login immediately at http://micros0ft-renew.xyz to restore.", "label": 1},

        # Prize / Lottery Scams
        {"text": "Congratulations! You've been selected as today's winner. Claim your $500 prize now!", "label": 1},
        {"text": "Claim your $1000 Amazon gift card now! Action required within 24 hours.", "label": 1},
        {"text": "You are the lucky winner of our annual lottery! Provide your bank details to receive your prize.", "label": 1},
        {"text": "YOU HAVE WON! Click here to claim your exclusive reward before it expires at midnight.", "label": 1},
        {"text": "Special offer: You've been selected for a free iPhone 15. Complete your profile now to claim.", "label": 1},
        {"text": "WINNER ANNOUNCEMENT: You won $5,000 in our monthly giveaway. Click to verify and receive funds.", "label": 1},

        # Package / Delivery Scams
        {"text": "Your package could not be delivered. Pay the shipping fee here to release it.", "label": 1},
        {"text": "DHL: Your parcel is pending delivery. Pay the customs fee to release your shipment.", "label": 1},
        {"text": "USPS: Your package is held at customs. Click to schedule redelivery and pay the handling fee.", "label": 1},
        {"text": "FedEx: We attempted to deliver your package. Confirm your address to reschedule delivery.", "label": 1},
        {"text": "Your order shipment requires immediate action. Update your delivery preferences now.", "label": 1},
        {"text": "ALERT: Your parcel has been seized. Pay the clearance fee within 24h to release.", "label": 1},

        # Tax / Financial / Government
        {"text": "FINAL NOTICE: You have an outstanding tax debt. Contact us immediately to avoid arrest.", "label": 1},
        {"text": "IRS NOTICE: You owe back taxes. Failure to respond within 24 hours may result in legal action.", "label": 1},
        {"text": "Your tax refund of $3,240 is pending. Verify your bank account details to receive funds.", "label": 1},
        {"text": "URGENT: Your financial account shows suspicious transactions. Verify immediately.", "label": 1},
        {"text": "The government owes you a refund. Submit your banking details at this secure portal.", "label": 1},
        {"text": "Social Security Administration: Your SSN has been suspended due to suspicious activity.", "label": 1},

        # Tech Support Scams
        {"text": "WARNING: Your computer is infected with a virus! Call our support line immediately.", "label": 1},
        {"text": "Microsoft Security Alert: Your Windows license has expired. Renew now to avoid data loss.", "label": 1},
        {"text": "Your device has been hacked! Install our security software immediately to protect yourself.", "label": 1},
        {"text": "CRITICAL: Multiple viruses detected on your PC. Call tech support NOW before data is stolen.", "label": 1},
        {"text": "Adobe Flash update required. Download the latest version from our secure server now.", "label": 1},

        # Healthcare / COVID Scams
        {"text": "You are eligible for a free COVID-19 relief payment. Apply now at this secure link.", "label": 1},
        {"text": "Your Medicare benefits are expiring. Confirm your details to retain full coverage.", "label": 1},
        {"text": "FREE health insurance quote. You qualify based on your zip code. Claim today!", "label": 1},

        # HR / Payroll / Business Email Compromise
        {"text": "Invoice #82914 attached. Urgent: Please process payment within 24 hours to avoid penalties.", "label": 1},
        {"text": "Payroll update required. Verify your banking details to ensure correct direct deposit.", "label": 1},
        {"text": "Your W-2 forms are ready. Access them through this secure employee portal link.", "label": 1},
        {"text": "Action required: Update your direct deposit information before the next pay period.", "label": 1},
        {"text": "URGENT: Your timesheet submission is overdue. Submit through this link or miss payroll.", "label": 1},
        {"text": "CEO: Please process this wire transfer of $45,000 today. I'm in a meeting, handle urgently.", "label": 1},
        {"text": "HR Department requires you to confirm your personal details for our updated records system.", "label": 1},

        # Social Engineering
        {"text": "Hi, I'm stuck abroad and my wallet was stolen. Can you wire me money urgently?", "label": 1},
        {"text": "I need your urgent help. Please keep this confidential and respond to me immediately.", "label": 1},
        {"text": "Your friend tagged you in a photo. View the embarrassing photo before it spreads.", "label": 1},
        {"text": "Someone shared a private video of you. Click here immediately to view and remove it.", "label": 1},

        # Credential Harvesting
        {"text": "Your email storage is 98% full. Click here to upgrade your account and avoid data loss.", "label": 1},
        {"text": "Your Office365 subscription has expired. Login now to renew and retain all your files.", "label": 1},
        {"text": "Immediate Action Required: Your email account will be suspended in 24 hours.", "label": 1},
        {"text": "DocuSign: You have an urgent document waiting for your signature. Click to review and sign.", "label": 1},
        {"text": "Dropbox: A confidential file has been shared with you. Click to view the document.", "label": 1},
        {"text": "Your iCloud storage is full. Your data may be lost. Click to upgrade your storage plan.", "label": 1},
        {"text": "Verify your login: Unusual sign-in from Russia detected on your account. Secure it now.", "label": 1},

        # Malware / Attachment Lures
        {"text": "Your order receipt is attached. Open the document to view purchase details and confirm.", "label": 1},
        {"text": "Scan the attached QR code to complete your mandatory account verification process.", "label": 1},
        {"text": "The document you requested is ready. Download it from our secure server at the link below.", "label": 1},
        {"text": "BANK STATEMENT: Your monthly statement is ready. Download the encrypted PDF to view.", "label": 1},
        {"text": "Legal Notice: You are summoned to appear in court. Review the attached documents immediately.", "label": 1},

        # ==================================================
        # LEGITIMATE EMAILS — label: 0
        # ==================================================
        # Work / Professional
        {"text": "Hey John, are we still on for lunch tomorrow? Let me know if you need to reschedule.", "label": 0},
        {"text": "Please see the attached quarterly report for your review before the board meeting.", "label": 0},
        {"text": "Can you send me the project files by Friday? The client is expecting them by end of week.", "label": 0},
        {"text": "I've reviewed your pull request, looks good to merge. Nice optimization on the API calls.", "label": 0},
        {"text": "Let's sync up on the new project requirements at 2 PM in the main conference room.", "label": 0},
        {"text": "The meeting notes from yesterday's standup are attached for your reference.", "label": 0},
        {"text": "Are you going to the conference next month? We should coordinate travel arrangements.", "label": 0},
        {"text": "Reminder: The sprint planning meeting is scheduled for Monday at 10 AM. See you there.", "label": 0},
        {"text": "Just a reminder that the deadline for the Q4 report is next Thursday at 5 PM.", "label": 0},
        {"text": "Can you review this proposal before I send it to the client? Your feedback is appreciated.", "label": 0},
        {"text": "The new intern starts on Monday. Could you give them a quick onboarding tour of the office?", "label": 0},
        {"text": "I finished implementing the new API endpoint. All tests are passing. Ready for code review.", "label": 0},
        {"text": "Hey, could you cover my on-call shift next Tuesday? I have a family commitment that day.", "label": 0},
        {"text": "Server maintenance is scheduled for Sunday 2-4 AM. Please plan your deploys accordingly.", "label": 0},
        {"text": "Your leave request for April 15-20 has been approved. Have a great vacation!", "label": 0},
        {"text": "Here are the action items from today's project kickoff meeting.", "label": 0},
        {"text": "Let me know your availability for a quick call this week to discuss the roadmap.", "label": 0},

        # Personal
        {"text": "Happy birthday! Hope your day is amazing. Drinks tonight to celebrate?", "label": 0},
        {"text": "Thanks for the update. Let me know if there's anything else I can help with.", "label": 0},
        {"text": "Check out this cool article I found on Python programming. Thought you'd enjoy it.", "label": 0},
        {"text": "Are you free this weekend? We're planning a hike up the mountain trail.", "label": 0},
        {"text": "Loved the article you shared. Really insightful perspective on industry trends.", "label": 0},
        {"text": "Just got back from vacation — Italy was incredible. Let's catch up soon!", "label": 0},
        {"text": "Did you watch the game last night? Incredible comeback in the final quarter!", "label": 0},
        {"text": "I'll be in your city next week for a conference. Would love to grab coffee.", "label": 0},
        {"text": "Thanks for the gift! It was so thoughtful. Really appreciate your kindness.", "label": 0},
        {"text": "Just wanted to check in and see how you're settling into the new role.", "label": 0},

        # Legitimate Transactional
        {"text": "Your order #4521 has shipped. Expected delivery: Thursday, April 14.", "label": 0},
        {"text": "Thank you for your purchase. Your receipt is attached for your records.", "label": 0},
        {"text": "Your subscription has been renewed. You will be billed monthly on the 15th.", "label": 0},
        {"text": "We received your support ticket #8821. Our team will respond within 24 hours.", "label": 0},
        {"text": "Your account statement for March is now available in your online banking portal.", "label": 0},
        {"text": "Reminder: Your doctor appointment is scheduled for tomorrow at 3:30 PM.", "label": 0},
        {"text": "Your Uber Eats order from Pizza Place is on its way. Estimated arrival: 25 minutes.", "label": 0},
        {"text": "Flight confirmation: Your booking for April 20, NYC to LAX is confirmed. Safe travels!", "label": 0},
        {"text": "Your Amazon package has been delivered to your front door.", "label": 0},
        {"text": "Thanks for attending our webinar. The recording and slides are linked below.", "label": 0},
        {"text": "Your GitHub repository received 3 new pull requests today.", "label": 0},
        {"text": "Invoice #1042 from Acme Corp is due on May 1st. Total: $350.00.", "label": 0},

        # IT / System Notifications (Legitimate)
        {"text": "Your company VPN access has been renewed for another year. No action required.", "label": 0},
        {"text": "Welcome to the team! Your IT credentials and laptop will be ready by Monday morning.", "label": 0},
        {"text": "Please complete the mandatory security awareness training by end of this month.", "label": 0},
        {"text": "Your password will expire in 14 days. Please update through the company SSO portal.", "label": 0},
        {"text": "Scheduled maintenance window: Our systems will be offline tonight from 11 PM to 1 AM.", "label": 0},

        # Newsletter / Content
        {"text": "This week in tech: OpenAI announces new model, Google updates its core search algorithm.", "label": 0},
        {"text": "Your weekly Hacker News digest is ready. Top stories in machine learning this week.", "label": 0},
        {"text": "New blog post: 10 tips for writing cleaner Python code. Read the full article here.", "label": 0},
        {"text": "Your GitHub repository has received 5 new stars this week. Keep up the great work!", "label": 0},

        # Legitimate HR / Admin
        {"text": "As a reminder, the office will be closed on Monday for the public holiday.", "label": 0},
        {"text": "Please submit your expense reports by the 5th of each month for reimbursement.", "label": 0},
        {"text": "Your performance review is scheduled for next Wednesday with your line manager.", "label": 0},
        {"text": "Company picnic is on Saturday. RSVP by Thursday so we can finalize the catering order.", "label": 0},
        {"text": "Benefits enrollment begins April 1. Visit the HR portal to review your plan options.", "label": 0},

        # Education / Learning
        {"text": "Course update: New module on neural networks is now available in your learning portal.", "label": 0},
        {"text": "Your certificate of completion for Python Fundamentals has been issued.", "label": 0},
        {"text": "Your assignment submission was received. Results will be posted within 5 business days.", "label": 0},
        {"text": "Library reminder: The book you reserved is now available for pickup at the front desk.", "label": 0},
        {"text": "Conference recap: Slides from the keynote sessions are now available for download.", "label": 0},
    ]

    df = pd.DataFrame(data)
    print(f"[AetherGuard] Dataset: {len(df)} samples ({df['label'].sum()} phishing, {(df['label']==0).sum()} legitimate)")

    # Train / test split (80/20, stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        df['text'], df['label'],
        test_size=0.2, random_state=42, stratify=df['label']
    )

    # Pipeline: TF-IDF bigrams + Logistic Regression
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            stop_words='english',
            max_features=3000,
            ngram_range=(1, 2),   # unigrams + bigrams
            sublinear_tf=True,    # log(1+tf) scaling
        )),
        ('clf', LogisticRegression(
            random_state=42,
            max_iter=500,
            C=1.0,
            solver='lbfgs'
        ))
    ])

    pipeline.fit(X_train, y_train)

    train_acc = pipeline.score(X_train, y_train)
    test_acc  = pipeline.score(X_test, y_test)

    print(f"[AetherGuard] Train accuracy : {train_acc:.2%}")
    print(f"[AetherGuard] Test  accuracy : {test_acc:.2%}")
    print("\n[AetherGuard] Classification Report:")
    print(classification_report(
        y_test,
        pipeline.predict(X_test),
        target_names=['Legitimate', 'Phishing']
    ))

    # Save vectorizer and model separately (scanner.py loads them independently)
    with open('model.pkl', 'wb') as f:
        pickle.dump(pipeline.named_steps['clf'], f)
    with open('vectorizer.pkl', 'wb') as f:
        pickle.dump(pipeline.named_steps['tfidf'], f)
    # Also save full pipeline for convenience
    with open('pipeline.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

    print("[AetherGuard] Saved model.pkl, vectorizer.pkl, and pipeline.pkl")

if __name__ == "__main__":
    create_and_train_model()
