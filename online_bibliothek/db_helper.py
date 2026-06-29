import os
import sqlite3
from flask import current_app, g

DATABASE_FILENAME = "bibliothek_02.sqlite"

def get_db_path():
    # Database is in the app root directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, DATABASE_FILENAME)

def get_db():
    """Returns a database connection. Reuses the same connection during a request."""
    if 'db' not in g:
        db_path = get_db_path()
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enable foreign key support
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Closes the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database tables if they do not exist."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # 1. Nutzer
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nutzer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                adresse TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                passwort TEXT NOT NULL,
                rolle TEXT NOT NULL DEFAULT 'user',
                ist_aktiv INTEGER DEFAULT 0,
                bestaetigungstoken TEXT DEFAULT NULL,
                angelegt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                aktualisiert_am DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Buecher
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buecher (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titel TEXT NOT NULL,
                autor TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                bestand INTEGER NOT NULL DEFAULT 1,
                typ TEXT NOT NULL DEFAULT 'physisch',
                pdf_pfad TEXT DEFAULT NULL,
                angelegt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                aktualisiert_am DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Ausleihen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ausleihen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nutzer_id INTEGER,
                buch_id INTEGER,
                ausgeliehen_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (nutzer_id) REFERENCES nutzer(id) ON DELETE CASCADE,
                FOREIGN KEY (buch_id) REFERENCES buecher(id) ON DELETE CASCADE
            )
        """)
        
        # 4. Buch-Analysen
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buch_analysen (
                buch_id INTEGER PRIMARY KEY,
                zusammenfassung TEXT,
                inhaltsverzeichnis TEXT,
                aktualisiert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buch_id) REFERENCES buecher(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Fehler bei der Datenbankinitialisierung: {e}")
    finally:
        conn.close()

# Run initialization
init_db()
