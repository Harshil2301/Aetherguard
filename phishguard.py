import argparse
import re
import sys
import os

# Define color schemes for terminal output
# Using raw ANSI escape codes for zero-dependency execution
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Enable ANSI colors in Windows CMD/PowerShell if running on Windows
if os.name == 'nt':
    os.system('color')

# Common keywords found in phishing emails
SUSPICIOUS_KEYWORDS = [
    "urgent", "verify your account", "password reset", "suspended",
    "unauthorized login", "action required", "immediate action",
    "invoice attached", "claim your prize", "update your billing"
]

# TLDs commonly abused by malicious actors
SUSPICIOUS_TLDS = [
    ".xyz", ".top", ".cf", ".gq", ".ml", ".ga", ".pw", ".cc"
]

# URL Shorteners often used to hide real destinations
URL_SHORTENERS = [
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co", "is.gd"
]

def print_banner():
    print(Colors.OKCYAN + Colors.BOLD + """
    ================================================
      🛡️  PhishGuard - Email Threat Analyzer 🛡️
    ================================================
    """ + Colors.ENDC)

def extract_urls(text):
    """Extract all URLs from a given text block."""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)

def analyze_keywords(text):
    """Check text against a list of suspicious keywords."""
    found = []
    text_lower = text.lower()
    for word in SUSPICIOUS_KEYWORDS:
        if word in text_lower:
            found.append(word)
    return found

def analyze_urls(urls):
    """Score URLs based on suspicious characteristics."""
    findings = []
    for url in urls:
        score = 0
        reasons = []
        
        # Check for numeric IP addresses instead of domains
        if re.search(r'http[s]?://[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', url):
            score += 40
            reasons.append("IP Address used instead of Domain name (High Risk)")
            
        # Check for suspicious TLDs
        for tld in SUSPICIOUS_TLDS:
            if tld in url:
                score += 30
                reasons.append(f"Suspicious Top-Level Domain found ({tld})")
                
        # Check for URL Shorteners
        for shortener in URL_SHORTENERS:
            if shortener in url:
                score += 30
                reasons.append(f"URL Shortener found hiding real destination ({shortener})")
                
        # Check if HTTP rather than HTTPS
        if url.startswith("http://"):
            score += 10
            reasons.append("Connection is not secure (HTTP)")
            
        if score > 0:
            findings.append({"url": url, "score": score, "reasons": reasons})
            
    return findings

def scan_email(file_path):
    print(f"{Colors.OKBLUE}[*] Loading email file: {file_path}{Colors.ENDC}")
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error reading file: {e}{Colors.ENDC}")
        sys.exit(1)

    print(f"{Colors.OKGREEN}[+] File loaded successfully. Analyzing content...{Colors.ENDC}\n")
    
    total_threat_score = 0
    threat_indicators = []

    # 1. Keyword Analysis
    print(f"{Colors.BOLD}--- Step 1: Psychological Manipulation Check ---{Colors.ENDC}")
    keywords = analyze_keywords(content)
    if keywords:
        print(f"{Colors.WARNING}[!] Found {len(keywords)} suspicious keywords designed to create urgency/fear.{Colors.ENDC}")
        for word in keywords:
            print(f"    - '{word}'")
        threat_score_addition = len(keywords) * 15
        total_threat_score += threat_score_addition
        threat_indicators.append(f"Psychological Urgency ({threat_score_addition} points)")
    else:
        print(f"{Colors.OKGREEN}[🗸] No overt manipulation keywords detected.{Colors.ENDC}")

    print("\n")

    # 2. Extract and Analyze Links
    print(f"{Colors.BOLD}--- Step 2: Malicious Link Extractor ---{Colors.ENDC}")
    urls = extract_urls(content)
    if not urls:
        print(f"{Colors.OKGREEN}[🗸] No links found in the email.{Colors.ENDC}")
    else:
        print(f"{Colors.OKCYAN}[i] Extracted {len(urls)} link(s):{Colors.ENDC}")
        for u in urls:
            print(f"    -> {u}")
            
        print("\nAnalyzing links for threat signatures...")
        url_threats = analyze_urls(urls)
        
        if url_threats:
            print(f"{Colors.FAIL}[!] Malicious indicators found in URLs!{Colors.ENDC}")
            for threat in url_threats:
                print(f"    URL: {threat['url']}")
                for r in threat['reasons']:
                    print(f"         {Colors.WARNING}- {r}{Colors.ENDC}")
                total_threat_score += threat['score']
                threat_indicators.append(f"Dangerous URL structures ({threat['score']} points)")
        else:
            print(f"{Colors.OKGREEN}[🗸] URLs appear structurally safe.{Colors.ENDC}")

    print("\n")

    # 3. Final Report
    print(f"{Colors.BOLD}================================================{Colors.ENDC}")
    print(f"{Colors.BOLD}              FINAL THREAT REPORT               {Colors.ENDC}")
    print(f"{Colors.BOLD}================================================{Colors.ENDC}")
    
    if total_threat_score >= 100:
        total_threat_score = 100
        
    print(f"Threat Score: ", end="")
    if total_threat_score < 30:
        print(f"{Colors.OKGREEN}{total_threat_score}/100 (SAFE){Colors.ENDC}")
    elif total_threat_score < 70:
        print(f"{Colors.WARNING}{total_threat_score}/100 (SUSPICIOUS){Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{total_threat_score}/100 (HIGH RISK - PHISHING DETECTED){Colors.ENDC}")
        
    if threat_indicators:
        print("\nKey Indicators:")
        for ti in threat_indicators:
            print(f"  - {ti}")

    print("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PhishGuard - Email Threat Analyzer")
    parser.add_argument("file", help="Path to the .txt or .eml file to analyze")
    args = parser.parse_args()
    
    print_banner()
    scan_email(args.file)
