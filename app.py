import os
import json
import configparser
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mail import Mail, Message
from calculator.routes import calculator_bp
from contact_manager.routes import contact_manager_bp
from scrum_quiz.routes import scrum_quiz_bp

# Falls du Markdown-Formatierung im Text nutzen willst: pip install markdown2
try:
    import markdown2
except ImportError:
    markdown2 = None

# =================================================
# PFADE & KONFIGURATION
# =================================================
basedir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(basedir, 'config.ini')

config = configparser.ConfigParser()
if not config.read(config_path, encoding='utf-8'):
    raise FileNotFoundError(f"Konnte config.ini unter {config_path} nicht finden!")

app = Flask(__name__)
app.secret_key = config['APP']['SECRET_KEY']

# Blueprint Registrierung
app.register_blueprint(calculator_bp, url_prefix='/taschenrechner')
app.register_blueprint(contact_manager_bp, url_prefix='/contact-manager')
app.register_blueprint(scrum_quiz_bp, url_prefix='/scrum-quiz')

# Mail-Setup aus der Config
app.config.update(
    MAIL_SERVER=config['MAIL']['SERVER'],
    MAIL_PORT=config.getint('MAIL', 'PORT'),
    MAIL_USE_TLS=config.getboolean('MAIL', 'USE_TLS'),
    MAIL_USERNAME=config['MAIL']['USERNAME'],
    MAIL_PASSWORD=config['MAIL']['PASSWORD'],
    MAIL_DEFAULT_SENDER=config['MAIL']['DEFAULT_SENDER']
)

mail = Mail(app)

# =================================================
# HILFSFUNKTIONEN
# =================================================

def get_content_file(filename, convert_markdown=False):
    """Liest Text aus static/content/ Dateiname aus und konvertiert ggf. Markdown."""
    if not filename: return ""
    filepath = os.path.join(app.root_path, 'static', 'content', filename)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if convert_markdown:
                    if markdown2:
                        return markdown2.markdown(content, extras=["break-on-newline"])
                    # Fallback: simple line break preservation if markdown2 is missing
                    return content.replace('\n', '<br>\n')
                return content
        return "Inhalt wird bald ergänzt..."
    except Exception as e:
        print(f"Fehler beim Laden von {filename}: {e}")
        return "Fehler beim Laden des Inhalts."

def send_contact_email(name, email, subject, message):
    """Versendet die Kontaktanfrage per E-Mail."""
    msg = Message(
        subject=f"Portfolio Kontakt: {subject}",
        recipients=[config['MAIL']['RECIPIENT']],
        body=f"Name: {name}\nE-Mail: {email}\nBetreff: {subject}\n\nNachricht:\n{message}"
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print("Mail-Fehler:", e)
        return False

# =================================================
# ROUTES
# =================================================

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    # Lädt den 'About Me' Text aus der Markdown-Datei
    about_text = get_content_file('about_me.md', convert_markdown=True)
    return render_template('about.html', about_text=about_text)

@app.route("/projects")
def projects():
    json_path = os.path.join(basedir, 'projects.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_projects = json.load(f)
    except FileNotFoundError:
        raw_projects = []

    processed_projects = []
    for p in raw_projects:
        # Falls es der Taschenrechner ist, nutzen wir den Blueprint-Pfad
        live_url = p["live_url"]
        if p["title"].strip() == "SmartCalc – Taschenrechner":
            try:
                live_url = url_for('calculator.index')
            except Exception:
                pass
        elif p["title"].strip() == "Contact Manager":
            try:
                live_url = url_for('contact_manager.index')
            except Exception:
                pass
        elif p["title"].strip() == "Scrum Quiz App":
            try:
                live_url = url_for('scrum_quiz.index')
            except Exception:
                pass

        processed_projects.append({
            "title": p["title"],
            "image": p["image"],
            "video": p.get("video"),
            "live_url": live_url,
            "tech": p["tech"],
            # Fallback: Entweder direkter Text aus JSON oder aus Datei laden
            "description": p.get("info_text") or get_content_file(p.get("info_file")),
            "structure": p.get("struct_text") or get_content_file(p.get("struct_file"))
        })
    
    return render_template('projects.html', projects=processed_projects)

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        if send_contact_email(name, email, subject, message):
            flash("Nachricht erfolgreich gesendet!", "success")
        else:
            flash("Fehler beim Senden. Bitte versuche es erneut.", "danger")
        
        return redirect(url_for('contact'))

    return render_template('contact.html')

if __name__ == "__main__":
    app.run(debug=config.getboolean('APP', 'DEBUG'))