#!/home/www/portfolio/venv/bin/python3
import os
import sys

# Basisverzeichnis ermitteln
basedir = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(basedir, 'venv')

# Suche nach site-packages im venv (deine Logik)
site_packages_root = os.path.join(venv_path, 'lib')
if os.path.exists(site_packages_root):
    for dir_name in os.listdir(site_packages_root):
        if dir_name.startswith('python'):
            sys.path.insert(0, os.path.join(site_packages_root, dir_name, 'site-packages'))

# App-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, basedir)

# Live-Installer für fehlende Bibliotheken (z.B. Flask-WTF, requests, pypdf, bcrypt bei Basic-Hosting)
try:
    import flask_wtf
    import requests
    import pypdf
    import bcrypt
except ImportError:
    import subprocess
    try:
        req_path = os.path.join(basedir, 'requirements.txt')
        subprocess.check_output([sys.executable, "-m", "pip", "install", "-r", req_path], stderr=subprocess.STDOUT)
    except Exception as e:
        print("Content-Type: text/html\n")
        print(f"<h3>Abhängigkeits-Installation fehlgeschlagen: {str(e)}</h3>")
        if hasattr(e, 'output') and e.output:
            print(f"<pre>{e.output.decode('utf-8', errors='ignore')}</pre>")
        sys.exit(1)

from wsgiref.handlers import CGIHandler
try:
    from app import app
except Exception as e:
    import traceback
    print("Content-Type: text/html\n")
    print("<h3>Fehler beim Laden der App-Instanz:</h3>")
    print(f"<pre>{traceback.format_exc()}</pre>")
    sys.exit(1)

# Fix für saubere URLs bei Strato
class ScriptNameFixer(object):
    def __init__(self, app):
        self.app = app
    def __call__(self, environ, start_response):
        environ['SCRIPT_NAME'] = ''
        return self.app(environ, start_response)

if __name__ == '__main__':
    # Hier wird jetzt der Fixer genutzt statt nur 'app'
    CGIHandler().run(ScriptNameFixer(app))