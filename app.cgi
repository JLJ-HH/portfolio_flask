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

from wsgiref.handlers import CGIHandler
from app import app

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