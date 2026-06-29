import os
import random
import re
import json
import bcrypt
import requests
from flask import render_template, request, redirect, url_for, flash, session, current_app, send_from_directory, jsonify
from flask_mail import Message
from pypdf import PdfReader
from . import online_bibliothek_bp
from .db_helper import get_db

OLLAMA_URL = "https://ollama.com/v1/chat/completions"
OLLAMA_API_KEY = "25341745defc47f8b6af81c2a6c6e91a.4nEigoTHxY7kUpl6pdCXUc_q"

# ==============================================================================
# DECORATORS & HELPERS
# ==============================================================================

def login_required(f):
    import functools
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'nutzer_id' not in session:
            return redirect(url_for('online_bibliothek.login'))
        return f(*args, **kwargs)
    return decorated

def mitarbeiter_required(f):
    import functools
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if 'nutzer_id' not in session or session.get('rolle') != 'mitarbeiter':
            flash("Berechtigungsfehler: Zugriff verweigert.", "danger")
            return redirect(url_for('online_bibliothek.index'))
        return f(*args, **kwargs)
    return decorated

def check_password(password_plain, password_hash):
    """Verifies a bcrypt password hash, converting PHP $2y$ prefix if necessary."""
    try:
        hash_bytes = password_hash.encode('utf-8')
        if hash_bytes.startswith(b'$2y$'):
            hash_bytes = b'$2b$' + hash_bytes[4:]
        return bcrypt.checkpw(password_plain.encode('utf-8'), hash_bytes)
    except Exception as e:
        print(f"Fehler bei Passwortprüfung: {e}")
        return False

def hash_password(password_plain):
    """Hashes a password using bcrypt."""
    hashed = bcrypt.hashpw(password_plain.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def send_verification_email(name, email, token):
    """Sends a verification email using Flask-Mail."""
    mail = current_app.extensions.get('mail')
    if not mail:
        print("Fehler: Flask-Mail ist nicht initialisiert.")
        return False
        
    subject = "Verifizierungscode für deine Registrierung"
    body = (
        f"Hallo {name},\n\n"
        f"Dein Bestätigungscode für die Registrierung lautet: {token}\n\n"
        f"Bitte gib diesen Code auf der Verifizierungsseite ein, um dein Passwort festzulegen.\n\n"
        f"Dein Bibliotheksteam"
    )
    
    msg = Message(
        subject=subject,
        recipients=[email],
        body=body
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Fehler beim E-Mail-Versand: {e}")
        return False

# ==============================================================================
# AUTH ROUTES
# ==============================================================================

@online_bibliothek_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'nutzer_id' in session:
        return redirect(url_for('online_bibliothek.index'))
        
    meldung = ""
    erfolgsmeldung = request.args.get('registriert') == '1' and "Registrierung erfolgreich! Sie können sich jetzt anmelden." or ""
    
    if request.method == 'POST':
        # Honeypot Check
        if request.form.get('username_hp'):
            return "Bot detected", 400
            
        email = request.form.get('email', '').strip()
        passwort = request.form.get('passwort', '')
        
        if email and passwort:
            db = get_db()
            try:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM nutzer WHERE email = ?", (email,))
                nutzer = cursor.fetchone()
                
                if nutzer and check_password(passwort, nutzer['passwort']):
                    if int(nutzer['ist_aktiv']) != 1:
                        meldung = "Ihr Account wurde noch nicht verifiziert oder ist gesperrt."
                        session['registrierte_email'] = email
                    else:
                        session['nutzer_id'] = nutzer['id']
                        session['nutzer_name'] = nutzer['name']
                        session['rolle'] = nutzer['rolle']
                        return redirect(url_for('online_bibliothek.index'))
                else:
                    meldung = "Ungültige E-Mail-Adresse oder Passwort."
            except Exception as e:
                meldung = f"Datenbankfehler: {e}"
        else:
            meldung = "Bitte alle Felder ausfüllen."
            
    return render_template('ob_login.html', meldung=meldung, erfolgsmeldung=erfolgsmeldung)

@online_bibliothek_bp.route('/logout')
def logout():
    session.pop('nutzer_id', None)
    session.pop('nutzer_name', None)
    session.pop('rolle', None)
    session.pop('registrierte_email', None)
    session.pop('verifizierte_email', None)
    return redirect(url_for('online_bibliothek.login'))

@online_bibliothek_bp.route('/registrieren', methods=['GET', 'POST'])
def registrieren():
    if 'nutzer_id' in session:
        return redirect(url_for('online_bibliothek.index'))
        
    meldung = ""
    if request.method == 'POST':
        # Honeypot Check
        if request.form.get('username_hp'):
            return "Bot detected", 400
            
        name = request.form.get('name', '').strip()
        adresse = request.form.get('adresse', '').strip()
        email = request.form.get('email', '').strip()
        
        if name and adresse and email:
            if '@' not in email or '.' not in email:
                meldung = "Ungültige E-Mail-Adresse!"
            else:
                db = get_db()
                try:
                    # Check if email exists
                    cursor = db.cursor()
                    cursor.execute("SELECT id FROM nutzer WHERE email = ?", (email,))
                    if cursor.fetchone():
                        meldung = "Diese E-Mail-Adresse wird bereits verwendet!"
                    else:
                        token = f"{random.randint(100000, 999999):06d}"
                        
                        db.execute(
                            "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv, bestaetigungstoken) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (name, adresse, email, '', 'user', 0, token)
                        )
                        db.commit()
                        
                        # Send E-Mail
                        send_verification_email(name, email, token)
                        
                        session['registrierte_email'] = email
                        return redirect(url_for('online_bibliothek.verifizieren'))
                except Exception as e:
                    meldung = f"Datenbankfehler: {e}"
        else:
            meldung = "Bitte alle Felder ausfüllen!"
            
    return render_template('ob_registrieren.html', meldung=meldung)

@online_bibliothek_bp.route('/verifizieren', methods=['GET', 'POST'])
def verifizieren():
    email = session.get('registrierte_email', '')
    meldung = ""
    erfolgsmeldung = ""
    
    if request.method == 'POST':
        if 'code' in request.form:
            code = request.form.get('code', '').strip()
            if code and email:
                db = get_db()
                try:
                    cursor = db.cursor()
                    cursor.execute("SELECT bestaetigungstoken, ist_aktiv FROM nutzer WHERE email = ?", (email,))
                    nutzer = cursor.fetchone()
                    
                    if nutzer:
                        if int(nutzer['ist_aktiv']) == 1:
                            meldung = "Dieses Konto ist bereits aktiviert. Bitte melde dich an."
                        elif nutzer['bestaetigungstoken'] == code:
                            session['verifizierte_email'] = email
                            session.pop('registrierte_email', None)
                            return redirect(url_for('online_bibliothek.passwort_erstellen'))
                        else:
                            meldung = "Der eingegebene Bestätigungscode ist ungültig."
                    else:
                        meldung = "E-Mail-Adresse wurde nicht gefunden."
                except Exception as e:
                    meldung = f"Datenbankfehler: {e}"
            else:
                meldung = "Bitte geben Sie den Bestätigungscode ein."
                
        elif 'resend' in request.form:
            resend_email = request.form.get('resend_email', '').strip()
            if resend_email:
                db = get_db()
                try:
                    cursor = db.cursor()
                    cursor.execute("SELECT name, ist_aktiv FROM nutzer WHERE email = ?", (resend_email,))
                    nutzer = cursor.fetchone()
                    
                    if nutzer:
                        if int(nutzer['ist_aktiv']) == 1:
                            meldung = "Diese E-Mail ist bereits aktiv. Bitte logge dich ein."
                        else:
                            token = f"{random.randint(100000, 999999):06d}"
                            db.execute("UPDATE nutzer SET bestaetigungstoken = ? WHERE email = ?", (token, resend_email))
                            db.commit()
                            
                            send_verification_email(nutzer['name'], resend_email, token)
                            session['registrierte_email'] = resend_email
                            email = resend_email
                            erfolgsmeldung = "Ein neuer Bestätigungscode wurde erfolgreich gesendet!"
                    else:
                        meldung = "Zu dieser E-Mail-Adresse wurde keine ausstehende Registrierung gefunden."
                except Exception as e:
                    meldung = f"Datenbankfehler: {e}"
                    
    return render_template('ob_verifizieren.html', email=email, meldung=meldung, erfolgsmeldung=erfolgsmeldung)

@online_bibliothek_bp.route('/passwort-erstellen', methods=['GET', 'POST'])
def passwort_erstellen():
    email = session.get('verifizierte_email', '')
    if not email:
        return redirect(url_for('online_bibliothek.registrieren'))
        
    meldung = ""
    if request.method == 'POST':
        passwort = request.form.get('passwort', '')
        passwort_wdh = request.form.get('passwort_wdh', '')
        
        if passwort and passwort_wdh:
            if passwort != passwort_wdh:
                meldung = "Die Passwörter stimmen nicht überein!"
            elif len(passwort) < 6:
                meldung = "Das Passwort muss mindestens 6 Zeichen lang sein."
            else:
                db = get_db()
                try:
                    hashed = hash_password(passwort)
                    db.execute(
                        "UPDATE nutzer SET passwort = ?, ist_aktiv = 1, bestaetigungstoken = NULL WHERE email = ?",
                        (hashed, email)
                    )
                    db.commit()
                    session.pop('verifizierte_email', None)
                    return redirect(url_for('online_bibliothek.login', registriert='1'))
                except Exception as e:
                    meldung = f"Datenbankfehler: {e}"
        else:
            meldung = "Bitte füllen Sie alle Felder aus."
            
    return render_template('ob_passwort_erstellen.html', email=email, meldung=meldung)

# ==============================================================================
# MAIN PAGE & CHATBOT
# ==============================================================================

@online_bibliothek_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    db = get_db()
    meldung = request.args.get('meldung', '')
    leih_erfolg = request.args.get('leih_erfolg') == '1'
    
    # Handle borrowing errors
    leih_fehler = request.args.get('leih_fehler')
    if leih_fehler:
        if leih_fehler == 'bestand':
            meldung = "Fehler: Dieses Medium ist momentan vergriffen."
        elif leih_fehler == 'notfound':
            meldung = "Fehler: Das gewünschte Medium wurde nicht gefunden."
        elif leih_fehler == 'gesperrt':
            meldung = "Fehler: Ihr Benutzerkonto ist gesperrt."
        elif leih_fehler == 'rechte':
            meldung = "Fehler: Sie haben keine Berechtigung für diese Aktion."
        else:
            meldung = "Fehler: Der Ausleihvorgang konnte nicht durchgeführt werden."

    rolle = session.get('rolle')
    aktueller_nutzer_id = session.get('nutzer_id')
    
    # AI Chatbot Logic
    ki_antwort = ""
    ki_frage = ""
    if request.method == 'POST' and 'ki_frage' in request.form:
        ki_frage = request.form.get('ki_frage', '').strip()
        if ki_frage:
            try:
                # Load context (RAG)
                cursor = db.cursor()
                cursor.execute("""
                    SELECT b.id, b.titel, b.autor, b.typ, b.bestand, a.zusammenfassung, a.inhaltsverzeichnis 
                    FROM buecher b
                    LEFT JOIN buch_analysen a ON b.id = a.buch_id
                """)
                ctx_books = cursor.fetchall()
                books_context = ""
                for bk in ctx_books:
                    books_context += f"- ID: {bk['id']}, Titel: '{bk['titel']}', Autor: '{bk['autor']}', Format: '{bk['typ']}', Bestand: {bk['bestand']}\n"
                    if bk['zusammenfassung']:
                        books_context += f"  Zusammenfassung: {bk['zusammenfassung']}\n"
                    if bk['inhaltsverzeichnis']:
                        books_context += f"  Inhaltsverzeichnis: {bk['inhaltsverzeichnis']}\n"
                
                system_prompt = (
                    "Du bist ein hilfsbereiter, kompetenter und freundlicher KI-Bibliothekar namens Ollama. "
                    "Beantworte die Fragen des Nutzers und gib detaillierte, ausführliche und qualitativ hochwertige Buchempfehlungen "
                    "basierend auf dem folgenden Buchbestand sowie den Inhalten (Zusammenfassungen und Inhaltsverzeichnisse):\n"
                    f"{books_context}\n"
                    "Regeln für deine Antwort:\n"
                    "1. Beziehe dich primär auf die Bücher aus dieser Liste. Nutze die hinterlegten Zusammenfassungen und Inhaltsverzeichnisse intensiv, um dem Nutzer fundierte und maßgeschneiderte Empfehlungen auszusprechen.\n"
                    "2. Antworte auf Deutsch. Nimm dir ausreichend Raum, um die Bücher verständlich, flüssig und strukturiert vorzustellen (z. B. durch Absätze, Stichpunkte oder kurze Auszüge aus den Zusammenfassungen).\n"
                    "3. Wenn kein Buch aus der Liste zu der Frage passt oder das gewünschte Thema nicht abgedeckt ist, weise freundlich darauf hin und schlage passende Alternativen aus dem Bestand vor."
                )
                
                payload = {
                    "model": "gemma3:12b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": ki_frage}
                    ],
                    "stream": False
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OLLAMA_API_KEY}"
                }
                
                response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=20)
                if response.status_code == 200:
                    res_data = response.json()
                    ki_antwort = res_data['choices'][0]['message']['content']
                else:
                    ki_antwort = "Der KI-Bibliothekar ist momentan nicht erreichbar (Ollama meldet Fehler)."
            except Exception as e:
                ki_antwort = f"Fehler bei der KI-Anfrage: {e}"

    # Load data for user dashboard
    daten = []
    buecher_katalog = []
    
    try:
        cursor = db.cursor()
        if rolle == 'mitarbeiter':
            # Load all clients and their lent books
            cursor.execute("""
                SELECT nutzer.*, ausleihen.id AS ausleihe_id, buecher.titel AS buch_titel 
                FROM nutzer 
                LEFT JOIN ausleihen ON nutzer.id = ausleihen.nutzer_id
                LEFT JOIN buecher ON ausleihen.buch_id = buecher.id
                ORDER BY nutzer.id DESC
            """)
            daten = cursor.fetchall()
        else:
            # Load own active loans
            cursor.execute("""
                SELECT ausleihen.id AS ausleihe_id, buecher.id AS buch_id, buecher.titel AS buch_titel, buecher.typ, buecher.pdf_pfad, ausleihen.ausgeliehen_am 
                FROM ausleihen 
                JOIN buecher ON ausleihen.buch_id = buecher.id 
                WHERE ausleihen.nutzer_id = ? 
                ORDER BY ausleihen.id DESC
            """, (aktueller_nutzer_id,))
            daten = cursor.fetchall()
            
            # Load catalog for borrowing
            cursor.execute("""
                SELECT buecher.*, buch_analysen.zusammenfassung 
                FROM buecher 
                LEFT JOIN buch_analysen ON buecher.id = buch_analysen.buch_id 
                ORDER BY buecher.titel ASC
            """)
            buecher_katalog = cursor.fetchall()
    except Exception as e:
        meldung = f"Datenbankfehler: {e}"
        
    return render_template(
        'ob_index.html',
        rolle=rolle,
        daten=daten,
        buecher_katalog=buecher_katalog,
        meldung=meldung,
        leih_erfolg=leih_erfolg,
        ki_antwort=ki_antwort,
        ki_frage=ki_frage
    )

# ==============================================================================
# BOOK MANAGEMENT (CRUD)
# ==============================================================================

@online_bibliothek_bp.route('/buecher')
@login_required
@mitarbeiter_required
def buch_uebersicht():
    db = get_db()
    meldung = ""
    success = request.args.get('success') == '1'
    
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT buecher.*, buch_analysen.zusammenfassung, buch_analysen.inhaltsverzeichnis 
            FROM buecher 
            LEFT JOIN buch_analysen ON buecher.id = buch_analysen.buch_id 
            ORDER BY buecher.autor COLLATE NOCASE ASC, buecher.titel COLLATE NOCASE ASC
        """)
        buecher = cursor.fetchall()
    except Exception as e:
        buecher = []
        meldung = f"Fehler beim Laden des Buchbestands: {e}"
        
    return render_template('ob_buch_uebersicht.html', buecher=buecher, meldung=meldung, success=success)

@online_bibliothek_bp.route('/buecher/loeschen/<int:book_id>')
@login_required
@mitarbeiter_required
def buch_loeschen(book_id):
    db = get_db()
    try:
        db.execute("DELETE FROM buecher WHERE id = ?", (book_id,))
        db.commit()
        return redirect(url_for('online_bibliothek.buch_uebersicht', success='1'))
    except Exception as e:
        flash(f"Fehler beim Löschen des Buches: {e}", "danger")
        return redirect(url_for('online_bibliothek.buch_uebersicht'))

@online_bibliothek_bp.route('/buecher/neu', methods=['GET', 'POST'])
@login_required
@mitarbeiter_required
def buch_anlegen():
    meldung = ""
    erfolgsmeldung = ""
    titel = ""
    autor = ""
    isbn = ""
    
    if request.method == 'POST':
        titel = request.form.get('titel', '').strip()
        autor = request.form.get('autor', '').strip()
        isbn = request.form.get('isbn', '').strip()
        bestand = int(request.form.get('bestand', 1))
        typ = request.form.get('typ', 'physisch')
        pdf_pfad = None
        entries = []
        
        pdf_datei = request.files.get('pdf_datei')
        
        # 1. PDF Upload & Analysis
        if typ == 'pdf' and pdf_datei and pdf_datei.filename != '':
            uploads_dir = os.path.join(current_app.root_path, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Secure file name
            filename = f"{int(request.form.get('timestamp', 0)) or 'upload'}_{pdf_datei.filename}"
            filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
            dest_path = os.path.join(uploads_dir, filename)
            
            try:
                pdf_datei.save(dest_path)
                pdf_pfad = f"uploads/{filename}"
                bestand = 0
                
                # Extract text using pypdf
                text_auszug = ""
                reader = PdfReader(dest_path)
                for page in reader.pages[:3]: # Extract first few pages
                    text = page.extract_text()
                    if text:
                        text_auszug += text + "\n"
                
                text_auszug = text_auszug.strip()[:2500]
                
                if text_auszug:
                    system_instruction = (
                        "Du bist ein präziser Datenextraktions-Assistent. "
                        "Analysiere den folgenden Text aus einer hochgeladenen PDF-Datei. "
                        "Bestimme, ob der Text Informationen über Bücher (Titel, Autor, ISBN) oder Nutzer/Kunden (Name, Adresse, E-Mail) enthält. "
                        "Es können ein oder mehrere Bücher, und/oder ein oder mehrere Nutzer enthalten sein. "
                        "Antworte AUSSCHLIESSLICH im folgenden JSON-Format. "
                        "Gib KEINEN Text vor oder nach dem JSON aus. Benutze KEINE Markdown-Formatierung wie ```json.\n\n"
                        "Format:\n"
                        "{\n"
                        "  \"entries\": [\n"
                        "    {\n"
                        "      \"type\": \"book\",\n"
                        "      \"title\": \"Titel des Buches\",\n"
                        "      \"author\": \"Autor des Buches\",\n"
                        "      \"isbn\": \"ISBN-Nummer\",\n"
                        "      \"summary\": \"Kurze, dreizeilige Zusammenfassung des Inhalts\",\n"
                        "      \"table_of_contents\": \"Kurzes Inhaltsverzeichnis oder wichtige Kapitel\",\n"
                        "      \"format\": \"pdf\",\n"
                        "      \"stock\": 0\n"
                        "    },\n"
                        "    {\n"
                        "      \"type\": \"user\",\n"
                        "      \"name\": \"Name des Nutzers\",\n"
                        "      \"address\": \"Adresse des Nutzers\",\n"
                        "      \"email\": \"E-Mail-Adresse\"\n"
                        "    }\n"
                        "  ]\n"
                        "}"
                    )
                    
                    payload = {
                        "model": "gemma3:12b",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": f"Hier ist der extrahierte Text:\n{text_auszug}"}
                        ],
                        "stream": False
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OLLAMA_API_KEY}"
                    }
                    
                    response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=25)
                    if response.status_code == 200:
                        raw_content = response.json()['choices'][0]['message']['content'].strip()
                        # Clean markdown json fences
                        raw_content = re.sub(r'^```json\s*', '', raw_content)
                        raw_content = re.sub(r'\s*```$', '', raw_content)
                        raw_content = raw_content.strip()
                        
                        parsed = json.loads(raw_content)
                        if 'entries' in parsed:
                            entries = parsed['entries']
            except Exception as e:
                print(f"Fehler bei PDF-Verarbeitung / KI-Parsing: {e}")
                
        # 2. Fallback: Manual insertion
        if not entries and not meldung:
            if titel and autor and isbn:
                ki_zusammenfassung = ""
                ki_inhaltsverzeichnis = ""
                
                try:
                    text_auszug = f"Titel: {titel}, Autor: {autor}, ISBN: {isbn}"
                    system_instruction = (
                        "Du bist ein Literaturexperte. Generiere für das folgende Buch eine kurze Zusammenfassung und eine Kapitelübersicht aus deinem Wissen. Reagiere AUSSCHLIESSLICH im folgenden Format:\n"
                        "ZUSAMMENFASSUNG: [Schreibe eine kurze, dreizeilige Zusammenfassung des Inhalts]\n"
                        "INHALTSVERZEICHNIS: [Erstelle ein kurzes Inhaltsverzeichnis oder wichtige Kapitel]"
                    )
                    
                    payload = {
                        "model": "gemma3:12b",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": text_auszug}
                        ],
                        "stream": False
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OLLAMA_API_KEY}"
                    }
                    
                    response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=25)
                    if response.status_code == 200:
                        ki_reply = response.json()['choices'][0]['message']['content']
                        
                        m_sub = re.search(r'ZUSAMMENFASSUNG:(.*?)(?=INHALTSVERZEICHNIS:)', ki_reply, re.DOTALL | re.IGNORECASE)
                        if m_sub:
                            ki_zusammenfassung = m_sub.group(1).strip()
                            
                        m_toc = re.search(r'INHALTSVERZEICHNIS:(.*)', ki_reply, re.DOTALL | re.IGNORECASE)
                        if m_toc:
                            ki_inhaltsverzeichnis = m_toc.group(1).strip()
                            
                        if not ki_zusammenfassung:
                            ki_zusammenfassung = ki_reply.strip()
                except Exception as e:
                    ki_zusammenfassung = f"Fehler bei der Textanalyse: {e}"
                    
                entries.append({
                    'type': 'book',
                    'title': titel,
                    'author': autor,
                    'isbn': isbn,
                    'summary': ki_zusammenfassung or 'Keine Zusammenfassung vorhanden.',
                    'table_of_contents': ki_inhaltsverzeichnis or '',
                    'typ_override': typ,
                    'bestand_override': bestand
                })
                
        # 3. Save to DB
        if not meldung and entries:
            db = get_db()
            buecher_erfolgreich = 0
            nutzer_erfolgreich = 0
            fehler_details = []
            
            try:
                # Manual SQLite Transaction
                db.execute("BEGIN TRANSACTION;")
                cursor = db.cursor()
                
                for entry in entries:
                    if entry.get('type') == 'book':
                        e_titel = entry.get('title', '').strip()
                        e_autor = entry.get('author', '').strip()
                        e_isbn = entry.get('isbn', '').strip()
                        e_summary = entry.get('summary', '').strip()
                        e_toc = entry.get('table_of_contents', '').strip()
                        e_typ = entry.get('typ_override') or (entry.get('format') == 'physisch' and 'physisch' or 'pdf')
                        
                        if 'bestand_override' in entry:
                            e_bestand = int(entry['bestand_override'])
                        else:
                            e_bestand = (e_typ == 'physisch') and int(entry.get('stock', 1)) or int(entry.get('stock', 0))
                            
                        curr_pdf = (e_typ == 'pdf') and pdf_pfad or None
                        
                        if e_titel and e_autor and e_isbn:
                            cursor.execute("SELECT id FROM buecher WHERE isbn = ?", (e_isbn,))
                            if cursor.fetchone():
                                fehler_details.append(f"ISBN '{e_isbn}' existiert bereits.")
                                continue
                                
                            cursor.execute(
                                "INSERT INTO buecher (titel, autor, isbn, bestand, typ, pdf_pfad) VALUES (?, ?, ?, ?, ?, ?)",
                                (e_titel, e_autor, e_isbn, e_bestand, e_typ, curr_pdf)
                            )
                            buch_id = cursor.lastrowid
                            
                            if e_summary:
                                cursor.execute(
                                    "INSERT INTO buch_analysen (buch_id, zusammenfassung, inhaltsverzeichnis) VALUES (?, ?, ?)",
                                    (buch_id, e_summary, e_toc)
                                )
                            buecher_erfolgreich += 1
                        else:
                            fehler_details.append("Unvollständige Buchdaten.")
                            
                    elif entry.get('type') == 'user':
                        e_name = entry.get('name', '').strip()
                        e_adresse = entry.get('address', '').strip()
                        e_email = entry.get('email', '').strip()
                        
                        if e_name and e_adresse and e_email:
                            cursor.execute("SELECT id FROM nutzer WHERE email = ?", (e_email,))
                            if cursor.fetchone():
                                fehler_details.append(f"E-Mail '{e_email}' existiert bereits.")
                                continue
                                
                            default_pw = hash_password('user123')
                            cursor.execute(
                                "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv) VALUES (?, ?, ?, ?, 'user', 1)",
                                (e_name, e_adresse, e_email, default_pw)
                            )
                            nutzer_erfolgreich += 1
                        else:
                            fehler_details.append("Unvollständige Nutzerdaten.")
                
                db.execute("COMMIT;")
                
                if buecher_erfolgreich > 0 or nutzer_erfolgreich > 0:
                    msg_parts = []
                    if buecher_erfolgreich > 0:
                        msg_parts.append(f"{buecher_erfolgreich} Buch/Bücher")
                    if nutzer_erfolgreich > 0:
                        msg_parts.append(f"{nutzer_erfolgreich} Nutzer")
                    erfolgsmeldung = f"Erfolgreich erfasst: {' und '.join(msg_parts)}."
                    if fehler_details:
                        erfolgsmeldung += f" (Einige Einträge übersprungen: {', '.join(fehler_details)})"
                    titel = autor = isbn = ""
                else:
                    db.execute("ROLLBACK;")
                    meldung = "Es konnten keine neuen Medien oder Nutzer gespeichert werden."
                    if fehler_details:
                        meldung += f" Details: {', '.join(fehler_details)}"
            except Exception as e:
                try:
                    db.execute("ROLLBACK;")
                except:
                    pass
                meldung = f"Datenbankfehler: {e}"
        elif not meldung:
            meldung = "Bitte füllen Sie das Formular aus oder laden Sie ein gültiges PDF hoch."

    return render_template(
        'ob_buch_form.html',
        action="Anlegen",
        titel=titel,
        autor=autor,
        isbn=isbn,
        meldung=meldung,
        erfolgsmeldung=erfolgsmeldung
    )

@online_bibliothek_bp.route('/buecher/bearbeiten/<int:book_id>', methods=['GET', 'POST'])
@login_required
@mitarbeiter_required
def buch_bearbeiten(book_id):
    db = get_db()
    meldung = ""
    
    # Load current book
    cursor = db.cursor()
    cursor.execute("SELECT * FROM buecher WHERE id = ?", (book_id,))
    b = cursor.fetchone()
    if not b:
        flash("Buch nicht gefunden.", "danger")
        return redirect(url_for('online_bibliothek.buch_uebersicht'))
        
    if request.method == 'POST':
        titel = request.form.get('titel', '').strip()
        autor = request.form.get('autor', '').strip()
        isbn = request.form.get('isbn', '').strip()
        bestand = int(request.form.get('bestand', 1))
        
        try:
            # Check if summary needs analysis
            cursor.execute("SELECT zusammenfassung FROM buch_analysen WHERE buch_id = ?", (book_id,))
            has_summary = cursor.fetchone()
            
            needs_analysis = not has_summary or (b['titel'] != titel or b['autor'] != autor)
            
            db.execute("BEGIN TRANSACTION;")
            db.execute(
                "UPDATE buecher SET titel = ?, autor = ?, isbn = ?, bestand = ?, aktualisiert_am = CURRENT_TIMESTAMP WHERE id = ?",
                (titel, autor, isbn, bestand, book_id)
            )
            
            if needs_analysis:
                ki_zusammenfassung = ""
                ki_inhaltsverzeichnis = ""
                try:
                    text_auszug = f"Titel: {titel}, Autor: {autor}, ISBN: {isbn}"
                    system_instruction = (
                        "Du bist ein Literaturexperte. Generiere für das folgende Buch eine kurze Zusammenfassung und eine Kapitelübersicht aus deinem Wissen. Reagiere AUSSCHLIESSLICH im folgenden Format:\n"
                        "ZUSAMMENFASSUNG: [Schreibe eine kurze, dreizeilige Zusammenfassung des Inhalts]\n"
                        "INHALTSVERZEICHNIS: [Erstelle ein kurzes Inhaltsverzeichnis oder wichtige Kapitel]"
                    )
                    
                    payload = {
                        "model": "gemma3:12b",
                        "messages": [
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": text_auszug}
                        ],
                        "stream": False
                    }
                    
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {OLLAMA_API_KEY}"
                    }
                    
                    response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=25)
                    if response.status_code == 200:
                        ki_reply = response.json()['choices'][0]['message']['content']
                        
                        m_sub = re.search(r'ZUSAMMENFASSUNG:(.*?)(?=INHALTSVERZEICHNIS:)', ki_reply, re.DOTALL | re.IGNORECASE)
                        if m_sub:
                            ki_zusammenfassung = m_sub.group(1).strip()
                            
                        m_toc = re.search(r'INHALTSVERZEICHNIS:(.*)', ki_reply, re.DOTALL | re.IGNORECASE)
                        if m_toc:
                            ki_inhaltsverzeichnis = m_toc.group(1).strip()
                            
                        if not ki_zusammenfassung:
                            ki_zusammenfassung = ki_reply.strip()
                except Exception as e:
                    print(f"Ollama API Error during editing: {e}")
                    
                if ki_zusammenfassung:
                    cursor.execute("""
                        INSERT INTO buch_analysen (buch_id, zusammenfassung, inhaltsverzeichnis) VALUES (?, ?, ?)
                        ON CONFLICT(buch_id) DO UPDATE SET 
                            zusammenfassung = excluded.zusammenfassung, 
                            inhaltsverzeichnis = excluded.inhaltsverzeichnis, 
                            aktualisiert_am = CURRENT_TIMESTAMP
                    """, (book_id, ki_zusammenfassung, ki_inhaltsverzeichnis))
                    
            db.execute("COMMIT;")
            return redirect(url_for('online_bibliothek.buch_uebersicht'))
        except Exception as e:
            try:
                db.execute("ROLLBACK;")
            except:
                pass
            meldung = f"Fehler beim Ändern der Daten: {e}"
            
    return render_template('ob_buch_form.html', action="Bearbeiten", b=b, meldung=meldung)

# ==============================================================================
# CLIENT MANAGEMENT (CRUD)
# ==============================================================================

@online_bibliothek_bp.route('/kunden/neu', methods=['GET', 'POST'])
@login_required
@mitarbeiter_required
def kunde_anlegen():
    meldung = ""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        adresse = request.form.get('adresse', '').strip()
        email = request.form.get('email', '').strip()
        
        if name and adresse and email:
            if '@' not in email or '.' not in email:
                meldung = "Fehler: Ungültige E-Mail-Adresse!"
            else:
                db = get_db()
                try:
                    default_pw = hash_password('user123')
                    db.execute(
                        "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv) VALUES (?, ?, ?, ?, 'user', 1)",
                        (name, adresse, email, default_pw)
                    )
                    db.commit()
                    return redirect(url_for('online_bibliothek.index', success='1'))
                except Exception as e:
                    meldung = "Fehler: E-Mail existiert bereits!" if "UNIQUE" in str(e) else f"Datenbankfehler: {e}"
        else:
            meldung = "Bitte alle Felder ausfüllen!"
            
    return render_template('ob_kunde_form.html', action="Anlegen", meldung=meldung)

@online_bibliothek_bp.route('/kunden/bearbeiten/<int:user_id>', methods=['GET', 'POST'])
@login_required
@mitarbeiter_required
def kunde_bearbeiten(user_id):
    db = get_db()
    meldung = ""
    
    # Load current client
    cursor = db.cursor()
    cursor.execute("SELECT * FROM nutzer WHERE id = ?", (user_id,))
    kunde = cursor.fetchone()
    if not kunde:
        flash("Kunde nicht gefunden.", "danger")
        return redirect(url_for('online_bibliothek.index'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        adresse = request.form.get('adresse', '').strip()
        email = request.form.get('email', '').strip()
        ist_aktiv = int(request.form.get('ist_aktiv', 1))
        
        if name and adresse and email:
            try:
                db.execute(
                    "UPDATE nutzer SET name = ?, adresse = ?, email = ?, ist_aktiv = ?, aktualisiert_am = CURRENT_TIMESTAMP WHERE id = ?",
                    (name, adresse, email, ist_aktiv, user_id)
                )
                db.commit()
                return redirect(url_for('online_bibliothek.index', success='1'))
            except Exception as e:
                meldung = f"Fehler beim Ändern der Daten: {e}"
        else:
            meldung = "Pflichtfelder ausfüllen!"
            
    return render_template('ob_kunde_form.html', action="Bearbeiten", kunde=kunde, meldung=meldung)

@online_bibliothek_bp.route('/kunden/loeschen/<int:user_id>')
@login_required
@mitarbeiter_required
def kunde_loeschen(user_id):
    db = get_db()
    try:
        db.execute("DELETE FROM nutzer WHERE id = ?", (user_id,))
        db.commit()
        return redirect(url_for('online_bibliothek.index', success='1'))
    except Exception as e:
        flash(f"Fehler beim Löschen des Kunden: {e}", "danger")
        return redirect(url_for('online_bibliothek.index'))

# ==============================================================================
# LENDING & RETURNING
# ==============================================================================

@online_bibliothek_bp.route('/ausleihen/<int:book_id>')
@login_required
def ausleihen(book_id):
    nutzer_id = session.get('nutzer_id')
    db = get_db()
    
    try:
        db.execute("BEGIN TRANSACTION;")
        cursor = db.cursor()
        
        # 1. Check if user is active
        cursor.execute("SELECT ist_aktiv FROM nutzer WHERE id = ?", (nutzer_id,))
        nutzer = cursor.fetchone()
        
        if not nutzer or int(nutzer['ist_aktiv']) != 1:
            db.execute("ROLLBACK;")
            return redirect(url_for('online_bibliothek.index', leih_fehler='gesperrt'))
            
        # 2. Check stock and type
        cursor.execute("SELECT typ, bestand FROM buecher WHERE id = ?", (book_id,))
        buch = cursor.fetchone()
        
        if buch:
            if int(buch['bestand']) > 0:
                # Decrement stock
                db.execute("UPDATE buecher SET bestand = bestand - 1 WHERE id = ?", (book_id,))
                
                # Insert loan record
                db.execute(
                    "INSERT INTO ausleihen (nutzer_id, buch_id, ausgeliehen_am) VALUES (?, ?, datetime('now', 'localtime'))",
                    (nutzer_id, book_id)
                )
                db.execute("COMMIT;")
                return redirect(url_for('online_bibliothek.index', leih_erfolg='1'))
            else:
                db.execute("ROLLBACK;")
                return redirect(url_for('online_bibliothek.index', leih_fehler='bestand'))
        else:
            db.execute("ROLLBACK;")
            return redirect(url_for('online_bibliothek.index', leih_fehler='notfound'))
    except Exception as e:
        try:
            db.execute("ROLLBACK;")
        except:
            pass
        flash(f"Datenbankfehler beim Ausleihen: {e}", "danger")
        return redirect(url_for('online_bibliothek.index'))

@online_bibliothek_bp.route('/rueckgabe/<int:loan_id>')
@login_required
def rueckgabe(loan_id):
    db = get_db()
    
    try:
        cursor = db.cursor()
        cursor.execute("SELECT buch_id, nutzer_id FROM ausleihen WHERE id = ?", (loan_id,))
        ausleihe = cursor.fetchone()
        
        if ausleihe:
            # Authorization check
            if session.get('rolle') != 'mitarbeiter' and int(ausleihe['nutzer_id']) != int(session.get('nutzer_id')):
                return redirect(url_for('online_bibliothek.index', leih_fehler='rechte'))
                
            book_id = ausleihe['buch_id']
            
            db.execute("BEGIN TRANSACTION;")
            # Increment stock
            db.execute("UPDATE buecher SET bestand = bestand + 1 WHERE id = ?", (book_id,))
            # Delete loan record
            db.execute("DELETE FROM ausleihen WHERE id = ?", (loan_id,))
            db.commit()
            return redirect(url_for('online_bibliothek.index', success='1'))
        else:
            return redirect(url_for('online_bibliothek.index', leih_fehler='notfound'))
    except Exception as e:
        try:
            db.execute("ROLLBACK;")
        except:
            pass
        flash(f"Datenbankfehler bei der Rückgabe: {e}", "danger")
        return redirect(url_for('online_bibliothek.index'))

# ==============================================================================
# FILE SERVING (E-BOOKS)
# ==============================================================================

@online_bibliothek_bp.route('/uploads/<path:filename>')
@login_required
def serve_upload(filename):
    uploads_dir = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(uploads_dir, filename)

# ==============================================================================
# DATABASE SETUP/RESET ROUTE (analog zu setup.php)
# ==============================================================================

@online_bibliothek_bp.route('/setup')
def setup_database():
    db = get_db()
    try:
        # Clear tables
        db.execute("DROP TABLE IF EXISTS buch_analysen")
        db.execute("DROP TABLE IF EXISTS ausleihen")
        db.execute("DROP TABLE IF EXISTS buecher")
        db.execute("DROP TABLE IF EXISTS nutzer")
        db.commit()
        
        # Re-create tables using the helper
        from .db_helper import init_db
        init_db()
        
        # Create dummy PDF for testing
        uploads_dir = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        dummy_pdf_path = os.path.join(uploads_dir, 'php_handbuch.pdf')
        with open(dummy_pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4 [Dummy PDF Content for Testing]')
            
        # Create default users
        pw_admin = hash_password('admin123')
        pw_user = hash_password('user123')
        pw_blocked = hash_password('geblockt123')
        
        db.execute(
            "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv) VALUES (?, ?, ?, ?, ?, ?)",
            ('Bibliothekar Chef', 'Hauptstraße 1, Hamburg', 'admin@bib.de', pw_admin, 'mitarbeiter', 1)
        )
        db.execute(
            "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv) VALUES (?, ?, ?, ?, ?, ?)",
            ('Jan Vanderfalk', 'Hocheneichen 8, Hamburg', 'jan@va.de', pw_user, 'user', 1)
        )
        db.execute(
            "INSERT INTO nutzer (name, adresse, email, passwort, rolle, ist_aktiv) VALUES (?, ?, ?, ?, ?, ?)",
            ('Gesperrter Tester', 'Schuldenweg 1, Nirgendwo', 'gesperrt@test.de', pw_blocked, 'user', 0)
        )
        
        # Create default books
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO buecher (titel, autor, isbn, bestand, typ, pdf_pfad) VALUES (?, ?, ?, ?, ?, ?)",
            ('Der Herr der Ringe', 'J.R.R. Tolkien', '978-3-608-93828-9', 3, 'physisch', None)
        )
        cursor.execute(
            "INSERT INTO buecher (titel, autor, isbn, bestand, typ, pdf_pfad) VALUES (?, ?, ?, ?, ?, ?)",
            ('Clean Code', 'Robert C. Martin', '978-3-826-65548-7', 2, 'physisch', None)
        )
        cursor.execute(
            "INSERT INTO buecher (titel, autor, isbn, bestand, typ, pdf_pfad) VALUES (?, ?, ?, ?, ?, ?)",
            ('PHP-Handbuch Digitale Edition', 'Michael Kofler', '978-3-836-27485-2', 5, 'pdf', 'uploads/php_handbuch.pdf')
        )
        buch_id_pdf = cursor.lastrowid
        
        # Create default analysis
        db.execute(
            "INSERT INTO buch_analysen (buch_id, zusammenfassung, inhaltsverzeichnis) VALUES (?, ?, ?)",
            (
                buch_id_pdf,
                'Eine umfassende Einführung in die Programmiersprache PHP, Datenbankanbindung mit PDO, Sicherheit (SQL-Injections, XSS) und objektorientierte Programmierung.',
                'Kapitel 1: Einführung in PHP; Kapitel 2: Kontrollstrukturen; Kapitel 3: PDO-Datenbankverbindungen; Kapitel 4: Sicherheitsmechanismen.'
            )
        )
        db.commit()
        
        return "<h3>Setup erfolgreich!</h3><p>Datenbank wurde zurückgesetzt und Standard-Testdaten wurden geladen.</p><p><a href='" + url_for('online_bibliothek.login') + "'>Hier geht es zum Login</a></p>"
    except Exception as e:
        return f"<h3>Fehler beim Ausführen des Setups:</h3><p style='color:red;'>{e}</p>"
