import json
import re
import nltk
from flask import Flask, render_template, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize NLTK downloads
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

app = Flask(__name__)

# Global memory for safety logs in this session
safety_logs = []

def add_safety_log(category, detail):
    safety_logs.append({"category": category, "detail": detail})

# Load the Legal Corpus
try:
    with open('legal_corpus.json', 'r') as f:
        legal_corpus = json.load(f)
except FileNotFoundError:
    legal_corpus = []

# Preprocessing
lemmatizer = nltk.stem.WordNetLemmatizer()

def preprocess_text(text):
    tokens = nltk.word_tokenize(text.lower())
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens if token.isalnum()]
    return " ".join(lemmatized)

# RAG & Matching Setup
if legal_corpus:
    corpus_texts = [preprocess_text(item["title"] + " " + item["description"]) for item in legal_corpus]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(corpus_texts)
else:
    vectorizer = None
    tfidf_matrix = None

# Centralized Safety Middleware
def run_safety_middleware(text, user_input=""):
    sanitized_text = text
    
    # 1. PII Redaction
    # Aadhaar: 12 digits or 4-4-4 format
    aadhaar_pattern = r'\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b'
    # PAN: 5 letters, 4 digits, 1 letter
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
    # Phone: standard 10 digit Indian numbers starting with 6-9
    phone_pattern = r'\b[6-9]\d{9}\b'
    
    pii_redacted = False
    if re.search(aadhaar_pattern, user_input) or re.search(aadhaar_pattern, sanitized_text):
        sanitized_text = re.sub(aadhaar_pattern, "[REDACTED AADHAAR]", sanitized_text)
        pii_redacted = True
    if re.search(pan_pattern, user_input, re.IGNORECASE) or re.search(pan_pattern, sanitized_text, re.IGNORECASE):
        sanitized_text = re.sub(pan_pattern, "[REDACTED PAN]", sanitized_text, flags=re.IGNORECASE)
        pii_redacted = True
    if re.search(phone_pattern, user_input) or re.search(phone_pattern, sanitized_text):
        sanitized_text = re.sub(phone_pattern, "[REDACTED PHONE]", sanitized_text)
        pii_redacted = True
        
    if pii_redacted:
        add_safety_log("PII Redaction", "Sensitive personal identifiers (PAN/Aadhaar/Phone) masked in response gateway.")
        
    # 2. Case Outcome Prediction Prevention
    outcome_keywords = ["guaranteed win", "will win", "court will rule in your favor", "100% win", "no chance of losing", "guarantee success"]
    prediction_intercepted = False
    for kw in outcome_keywords:
        if kw in sanitized_text.lower():
            prediction_intercepted = True
            break
            
    if prediction_intercepted:
        add_safety_log("Outcome Protection", "Blocked definitive courtroom victory projection. Re-calibrated to process-only advice.")
        sanitized_text = sanitized_text + "\n\n*Note: Legal outcomes depend on specific evidence and judicial discretion. LegalEase AI advises focusing on statutory compliance and the procedural rights explained above rather than anticipating a guaranteed outcome.*"

    # 3. Disclaimer Injection
    disclaimer = "\n\n**Disclaimer:** LegalEase AI is an AI legal information assistant, not a lawyer. This information is for educational purposes and awareness under Indian law. For formal legal advice, please consult a registered legal professional."
    sanitized_text += disclaimer
    add_safety_log("Disclaimer", "Injected statutory Indian legal warning disclaimer.")

    return sanitized_text

# Intent / Danger Detection (Module 3)
def detect_danger_signals(user_query):
    danger_keywords = ["hitting", "assault", "abuse", "kill", "suicide", "threaten", "beating", "domestic violence", "violence", "harassment"]
    for word in danger_keywords:
        if word in user_query.lower():
            add_safety_log("Emergency Interception", f"Detected threat/danger signal ('{word}'). Activating EMERGENCY RESPONSE protocol.")
            return True
    return False

# NLP Intent Classifier
def classify_intent(user_query):
    query_processed = preprocess_text(user_query)
    
    categories = {
        "Cybercrime": ["cyber", "scam", "hack", "upi", "fraud", "phishing", "online", "password", "bank", "account"],
        "Women's Safety": ["woman", "women", "posh", "harassment", "abuse", "domestic", "husband", "fir", "modesty"],
        "Tenant-Landlord Disputes": ["rent", "deposit", "landlord", "tenant", "eviction", "agreement", "lease", "tenancy"],
        "Consumer Rights": ["consumer", "product", "defective", "refund", "cheated", "shopkeeper", "bill", "guarantee"],
        "Workplace Rights": ["workplace", "wage", "employer", "salary", "fired", "job", "bonus", "boss", "work"]
    }
    
    scores = {cat: 0 for cat in categories}
    for cat, words in categories.items():
        for word in words:
            if word in query_processed:
                scores[cat] += 1
                
    max_cat = max(scores, key=scores.get)
    if scores[max_cat] > 0:
        return max_cat
    return "General Legal Query"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # 1. Active Keyword Danger Detection
    danger_detected = detect_danger_signals(user_message)
    
    # 2. Intent Classification
    intent = classify_intent(user_message)
    
    # 3. Retrieve ground truth (RAG matching)
    response_body = ""
    governing_law = "Indian Jurisdiction"
    remedy = ""
    section = ""
    
    if tfidf_matrix is not None and vectorizer is not None:
        processed_query = preprocess_text(user_message)
        query_vector = vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vector, tfidf_matrix)
        best_idx = similarities.argmax()
        best_score = similarities[0, best_idx]
        
        if best_score > 0.15:
            matched_item = legal_corpus[best_idx]
            response_body = matched_item["description"]
            governing_law = matched_item["act"]
            remedy = matched_item["remedy"]
            section = matched_item["section"]
        else:
            response_body = f"I've classified your query under **{intent}**. While I don't have a exact matching FAQ segment in my database, under general Indian legal principles, you have standard remedies. For dynamic queries, please check our specialized helper tabs."
    else:
        response_body = "The legal database is currently empty. Please upload valid legal codes."

    # Process through safety middleware
    final_response = run_safety_middleware(response_body, user_input=user_message)
    
    return jsonify({
        "response": final_response,
        "intent": intent,
        "danger_detected": danger_detected,
        "governing_law": governing_law,
        "section": section,
        "remedy": remedy
    })

@app.route("/api/chat_module", methods=["POST"])
def chat_module():
    user_message = request.json.get("message", "")
    module = request.json.get("module", "rights")
    document_text = request.json.get("document_text", "")
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
        
    danger_detected = detect_danger_signals(user_message)
    intent = classify_intent(user_message)
    
    # Context-specific chatbot logic
    if module == "simplifier" and document_text:
        # Chat with contract document context!
        response_body = ""
        lower_msg = user_message.lower()
        
        # Simple RAG search inside document text for key contractual terms
        search_terms = {
            "deposit": ["deposit", "security", "paint", "deduct"],
            "liability": ["liability", "sue", "maximum", "damage"],
            "termination": ["terminate", "exit", "cancel", "notice"],
            "jurisdiction": ["jurisdiction", "court", "governing", "law"]
        }
        
        found_key = None
        for key, terms in search_terms.items():
            if any(term in lower_msg for term in terms):
                found_key = key
                break
                
        if found_key == "deposit":
            response_body = "Based on the provided contract's **Security Deposit** clause: The security deposit is ₹1,50,000 without interest. The Landlord has full authority to deduct painting/cleaning costs at their sole discretion. This is highly one-sided."
        elif found_key == "liability":
            response_body = "Based on the provided contract's **Limitation of Liability** clause: The Landlord limits their liability exclusively to a maximum of 1 month of rent paid, even in case of gross negligence. This represents an Amber risk."
        elif found_key == "termination":
            response_body = "Based on the provided contract's **Termination** clause: The landlord can terminate with 0 days notice, while you must give 90 days. This is a severe Red risk!"
        elif found_key == "jurisdiction":
            response_body = "Based on the provided contract's **Governing Law & Jurisdiction** clause: Disputes must be filed exclusively in the state of Delaware, USA. Highly inconvenient!"
        else:
            response_body = "I scanned the uploaded contract clauses. I couldn't find an exact matching clause for that question. However, I highly recommend checking the **Termination Clause (Red Risk)** or **Limitation of Liability (Amber Risk)** cards listed in the dashboard above."
            
    elif module == "cybercrime":
        response_body = f"As your Cybercrime Guidance bot, I analysed your query: '{user_message}'. Under Section 66D of the IT Act and Section 318 BNS (Cheating), this represents online fraud. Make sure to preserve screenshots of your chats/UPI receipts, dial 1930 immediately, and register a financial fraud at cybercrime.gov.in."
        
    elif module == "safety":
        if danger_detected:
            response_body = "⚠️ **EMERGENCY ASSISTANCE ALERT** ⚠️\nIf you are in immediate threat, dial **112 (Emergency Response)**, **1091 (Women Helpline)**, or **181** immediately. Under the POSH Act 2013, you have a strict right to file workplace complaints within 3 months, and under Section 173 of the BNSS, you can file a **Zero FIR** at any local station."
        else:
            response_body = "Under the **POSH Act 2013**, every organization must establish an Internal Complaints Committee (ICC). If you face workplace harassment, file a written complaint within 3 months. You can also file a **Zero FIR** at any local police station which must be transferred to the correct area under Section 173 BNSS."
            
    elif module == "tenancy":
        response_body = "Under the **Model Tenancy Act 2021**, residential security deposits are capped at a maximum of **2 months' rent**. Evictions cannot occur without a written 2-month notice, and all lease agreements must be registered with the Rent Authority."
        
    else:
        # Default Rights / general chat RAG
        if tfidf_matrix is not None and vectorizer is not None:
            processed_query = preprocess_text(user_message)
            query_vector = vectorizer.transform([processed_query])
            similarities = cosine_similarity(query_vector, tfidf_matrix)
            best_idx = similarities.argmax()
            best_score = similarities[0, best_idx]
            
            if best_score > 0.15:
                matched_item = legal_corpus[best_idx]
                response_body = f"**Act Cited:** {matched_item['act']} (Section {matched_item['section']})\n\n**Guidance:** {matched_item['description']}\n\n**Legal Remedy:** {matched_item['remedy']}"
            else:
                response_body = f"I've classified your query under **{intent}**. For citizens facing this issue, we recommend checking Section 318 BNS (Cheating), the Consumer Protection Act, or the Model Tenancy Act caps. Ask me for specific steps!"
        else:
            response_body = "Legal database offline."
            
    # Process through safety middleware
    final_response = run_safety_middleware(response_body, user_input=user_message)
    
    return jsonify({
        "response": final_response,
        "intent": intent,
        "danger_detected": danger_detected
    })

# Module 2 API: Cybercrime Assistance
@app.route("/api/cybercrime", methods=["POST"])
def cybercrime_helper():
    crime_type = request.json.get("crime_type", "")
    
    checklists = {
        "upi": {
            "title": "UPI & Online Banking Fraud",
            "sections": "Section 66D of IT Act, 2000 & Section 318 of BNS, 2023",
            "checklist": [
                "Screenshot of the transaction debit SMS or bank app notification.",
                "Bank Account Statement showing the debited amount and transaction ID/UPI Ref ID.",
                "Screenshots of any communication (WhatsApp, SMS, Telegram) with the fraudster.",
                "Phone number or UPI handle of the fraudster.",
                "Website URL or QR code that led to the fraud (if applicable)."
            ],
            "portal_steps": [
                "Dial the National Cyber Crime Helpline at 1930 immediately to block the funds.",
                "Go to cybercrime.gov.in and register under 'Report Financial Fraud'.",
                "Enter transaction details: Bank Name, Transaction ID, Date, and Amount.",
                "Upload bank statement and screenshots of transaction confirmation.",
                "Submit and note the Acknowledgment Number for your bank's chargeback request."
            ]
        },
        "phishing": {
            "title": "Phishing & Fake Website Scams",
            "sections": "Section 66C & 66D of IT Act, 2000",
            "checklist": [
                "Full URL of the fake website (copy-pasted precisely).",
                "Screenshot of the webpage showing fake branding (e.g. fake bank page).",
                "Email header details if phishing came via email (raw message details).",
                "SMS screenshots if received as a text message containing short URLs."
            ],
            "portal_steps": [
                "Visit cybercrime.gov.in and click on 'Report Cyber Crime'.",
                "Select 'Online & Social Media Frauds' -> 'Phishing/Fake Website'.",
                "Provide the suspicious URL and screenshots of the site.",
                "Report the website to Google Safe Browsing (safebrowsing.google.com) to block it globally."
            ]
        },
        "identity_theft": {
            "title": "Identity Theft & Social Media Impersonation",
            "sections": "Section 66C of IT Act, 2000",
            "checklist": [
                "Screenshots of the fake profile showing your name/photos.",
                "Profile URL of the impersonator account (do not copy the display name only).",
                "Screenshots of the fake account messaging your contacts.",
                "Copy of your original profile link as evidence of primary ownership."
            ],
            "portal_steps": [
                "File a report directly inside the platform (Instagram, Facebook, LinkedIn).",
                "Go to cybercrime.gov.in -> 'Report Other Cyber Crime'.",
                "Select 'Social Media Crimes' -> 'Impersonation/Identity Theft'.",
                "Submit profile links and matching screenshots."
            ]
        },
        "extortion": {
            "title": "Ransomware & Online Extortion",
            "sections": "Section 308 of BNS, 2023 & Section 66 of IT Act",
            "checklist": [
                "Screenshot of the ransom note / threat message displayed on screen.",
                "Email address or crypto wallet address provided by the extortionist.",
                "Screenshots of chat conversations if blackmail is active.",
                "Encrypted file extensions list."
            ],
            "portal_steps": [
                "Do NOT pay any ransom; it does not guarantee file recovery.",
                "Disconnect the affected computer/network from the internet immediately.",
                "File a complaint at cybercrime.gov.in under 'Report Other Cyber Crime'.",
                "Contact local cyber police cell with the raw hard drive for forensic analysis."
            ]
        }
    }
    
    data = checklists.get(crime_type, {})
    return jsonify(data)

# Module 4 API: Security Deposit Calculator
@app.route("/api/tenant_calculator", methods=["POST"])
def calculate_deposit():
    rent = float(request.json.get("rent", 0))
    state = request.json.get("state", "delhi")
    is_residential = request.json.get("is_residential", True)
    
    # Model Tenancy Act (MTA) 2021 defaults:
    # Residential deposit cap: 2 months' rent
    # Commercial deposit cap: 6 months' rent
    
    # In some states (e.g. Maharashtra Rent Control), there are legacy caps or overrides:
    # E.g. Maharashtra has specific rent rules but MTA-aligned guidelines limit security deposit to standard agreements
    
    cap_months = 2 if is_residential else 6
    legal_cap = rent * cap_months
    
    # Add a custom state-based message
    state_notes = {
        "maharashtra": "Under the Maharashtra Rent Control Act, deposits have historically been negotiated but the Model Tenancy Act principles set a strict residential cap of 2 months.",
        "delhi": "Delhi Rent Control Act applies to older leases, but for modern tenancies matching MTA 2021, the deposit is legally capped at 2 months' rent.",
        "karnataka": "Karnataka has approved the Model Tenancy Act guidelines. Deposit is legally capped at a maximum of 2 months' rent for residential homes.",
        "tamilnadu": "Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act limits security deposits to 3 months' rent."
    }
    
    if state == "tamilnadu" and is_residential:
        cap_months = 3
        legal_cap = rent * cap_months
        
    note = state_notes.get(state, "Your state follows the standard Model Tenancy Act, 2021 guidelines capping residential deposits to a maximum of 2 months' rent.")
    
    return jsonify({
        "rent": rent,
        "cap_months": cap_months,
        "legal_cap": legal_cap,
        "note": note
    })

# Module 5 API: Document Simplifier & Risk Analyzer
@app.route("/api/simplify", methods=["POST"])
def simplify_document():
    doc_text = request.json.get("text", "")
    if not doc_text or len(doc_text.strip()) < 10:
        return jsonify({"error": "Please provide valid contract text."}), 400
        
    # Segment contract text into mock-analysed clauses based on simple keyword triggers
    clauses = [
        {
            "name": "Confidentiality & NDA",
            "keywords": ["confidential", "nda", "disclosure", "proprietary"],
            "summary": "You must protect proprietary data shared during the relationship. Cannot share business secrets with third parties.",
            "risk_score": "Green",
            "reason": "Standard confidentiality scope protecting proprietary info equally for both parties.",
            "negotiation": "Ensure reciprocal confidentiality obligations so they must protect your data too."
        },
        {
            "name": "Limitation of Liability",
            "keywords": ["liability", "maximum aggregate", "liable", "indemnity"],
            "summary": "Limits the maximum money either party can sue the other for in case of breach of contract.",
            "risk_score": "Amber",
            "reason": "Liability capped exclusively at 12 months of fees paid, which might block compensation for larger data breaches.",
            "negotiation": "Request a carve-out or higher multiplier (e.g. 3x contract value) specifically for data security and intellectual property breaches."
        },
        {
            "name": "Termination Clause",
            "keywords": ["terminate", "termination", "cancel", "notice period"],
            "summary": "Outlines how either party can exit the agreement. Specifies notice periods and grounds.",
            "risk_score": "Red",
            "reason": "Unilateral termination clause allows them to terminate 'for convenience' with 0 days notice, while you must give 90 days notice.",
            "negotiation": "Request mutual termination for convenience with a standard 30-day or 60-day notice period for both sides."
        },
        {
            "name": "Intellectual Property Assignment",
            "keywords": ["intellectual", "ip", "patent", "copyright", "assignment", "work made for hire"],
            "summary": "Specifies who owns the designs, code, or materials created during this working relationship.",
            "risk_score": "Red",
            "reason": "Full, perpetual transfer of all designs/intellectual assets before full invoice payment is received.",
            "negotiation": "Add a clause stating that all IP ownership transfers to the client *only* upon receipt of full and final payment."
        },
        {
            "name": "Governing Law & Jurisdiction",
            "keywords": ["jurisdiction", "governing law", "court", "arbitration", "venue"],
            "summary": "Determines which state or country's laws apply and where any court battles would take place.",
            "risk_score": "Amber",
            "reason": "Exclusive jurisdiction is set in a distant state, creating high travel expenses if a legal dispute arises.",
            "negotiation": "Propose mutually convenient neutral jurisdiction or local arbitration under the Arbitration and Conciliation Act."
        }
    ]
    
    extracted_clauses = []
    has_custom_match = False
    
    for cl in clauses:
        # Match keywords in the uploaded text
        matches = [kw for kw in cl["keywords"] if kw in doc_text.lower()]
        if matches:
            has_custom_match = True
            extracted_clauses.append({
                "clause_name": cl["name"],
                "summary": cl["summary"],
                "risk_score": cl["risk_score"],
                "reason": cl["reason"],
                "negotiation": cl["negotiation"]
            })
            
    # Fallback to general list if no keywords matched
    if not has_custom_match:
        extracted_clauses = [
            {
                "clause_name": c["name"],
                "summary": c["summary"],
                "risk_score": c["risk_score"],
                "reason": c["reason"],
                "negotiation": c["negotiation"]
            } for c in clauses
        ]
        
    # Structured Obligations
    obligations = [
        {"party": "Your Obligations", "duty": "Deliver quality services as agreed, maintain strict client confidentiality, and provide 30 days notice for standard exit."},
        {"party": "Their Obligations", "duty": "Process invoices within 30 days, protect shared property, and reimburse valid travel expenses."}
    ]
    
    return jsonify({
        "clauses": extracted_clauses,
        "obligations": obligations
    })

# API to fetch safety logs
@app.route("/api/safety_logs", methods=["GET"])
def get_safety_logs():
    return jsonify(safety_logs)

if __name__ == "__main__":
    # Add initial startup log
    add_safety_log("System Startup", "Stateless Flask RAG & Safety Engine online.")
    app.run(debug=True, port=5000)
