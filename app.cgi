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
libs_to_import = ['flask_wtf', 'requests', 'pypdf', 'bcrypt']
missing_libs = []
for lib in libs_to_import:
    try:
        __import__(lib)
    except ImportError:
        missing_libs.append(lib)

if missing_libs:
    import subprocess
    try:
        req_path = os.path.join(basedir, 'requirements.txt')
        # Erst normaler install/upgrade
        subprocess.check_output([sys.executable, "-m", "pip", "install", "-r", req_path], stderr=subprocess.STDOUT)
        
        # Wenn bcrypt gefehlt hat/beschädigt war, erzwingen wir eine Reinstallation davon
        if 'bcrypt' in missing_libs:
            subprocess.check_output([sys.executable, "-m", "pip", "install", "--upgrade", "--force-reinstall", "bcrypt==3.2.2"], stderr=subprocess.STDOUT)
            
        # Überprüfen, ob nun alle geladen werden können
        for lib in libs_to_import:
            __import__(lib)
    except Exception as e:
        print("Content-Type: text/html\n")
        print("<h3>Fehler bei der Installation der Abhängigkeiten:</h3>")
        print(f"<p>Fehler-Details: <code>{str(e)}</code></p>")
        if hasattr(e, 'output') and e.output:
            print(f"<h4>Pip Output:</h4><pre>{e.output.decode('utf-8', errors='ignore')}</pre>")
        
        # Diagnose-Ausgabe
        try:
            print("<h4>Diagnose-Informationen:</h4>")
            print(f"<p>Python Version: <code>{sys.version}</code></p>")
            print(f"<p>Python Executable: <code>{sys.executable}</code></p>")
            
            # Überprüfen, ob ldd verfügbar ist und Ausführen auf bcrypt library
            bcrypt_so_path = None
            site_packages_root = os.path.join(venv_path, 'lib')
            if os.path.exists(site_packages_root):
                for dir_name in os.listdir(site_packages_root):
                    if dir_name.startswith('python'):
                        target_so = os.path.join(site_packages_root, dir_name, 'site-packages', 'bcrypt', '_bcrypt.abi3.so')
                        if os.path.exists(target_so):
                            bcrypt_so_path = target_so
                            break
            
            if bcrypt_so_path:
                print(f"<p>Gefundene bcrypt.so: <code>{bcrypt_so_path}</code></p>")
                try:
                    ldd_out = subprocess.check_output(["ldd", bcrypt_so_path], stderr=subprocess.STDOUT)
                    print(f"<h4>ldd Ausgabe für _bcrypt.abi3.so:</h4><pre>{ldd_out.decode('utf-8', errors='ignore')}</pre>")
                except Exception as ldd_err:
                    print(f"<p>ldd-Ausführung fehlgeschlagen: {str(ldd_err)}</p>")
            else:
                print("<p>Datei <code>_bcrypt.abi3.so</code> konnte nicht im venv gefunden werden.</p>")
        except Exception as diag_err:
            print(f"<p>Fehler beim Sammeln der Diagnose-Infos: {str(diag_err)}</p>")
            
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