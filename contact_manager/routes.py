import os
from flask import Blueprint, render_template, request, jsonify

contact_manager_bp = Blueprint('contact_manager', __name__,
                               template_folder='templates',
                               static_folder='static')

DATEINAME = "contacts.txt"

# ==============================================================================
# DATA MANAGER LOGIC
# ==============================================================================

def ist_gueltiger_text(text):
    """Prüft, ob der Text nicht leer ist."""
    return text.strip() != ""

def ist_gueltige_email(email):
    """Prüft auf ein @-Zeichen und einen Punkt in der E-Mail."""
    return "@" in email and "." in email

def laden():
    """Lädt Kontakte aus der Datei (Format: Vorname|Nachname|Straße|PLZ|Email|Tel|Mobil)."""
    liste = []
    # Path relative to the current file's parent's parent (app root)
    # or just use the root directory relative to where the app runs.
    # We'll use absolute path based on the file location to be safe.
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    file_path = os.path.join(base_path, DATEINAME)

    if not os.path.exists(file_path):
        return liste
        
    try:
        with open(file_path, "r", encoding="utf-8") as datei:
            for zeile in datei:
                teile = zeile.strip().split("|")
                if len(teile) == 7:
                    vorname, nachname, strasse, plz, email, rufnummer, mobil = teile
                    liste.append({
                        "vorname": vorname,
                        "nachname": nachname,
                        "strasse": strasse,
                        "plz": plz,
                        "email": email,
                        "rufnummer": rufnummer,
                        "mobil": mobil
                    })
                elif len(teile) == 6:
                    vorname, nachname, strasse, plz, email, rufnummer = teile
                    liste.append({
                        "vorname": vorname,
                        "nachname": nachname,
                        "strasse": strasse,
                        "plz": plz,
                        "email": email,
                        "rufnummer": rufnummer,
                        "mobil": ""
                    })
                elif len(teile) == 5:
                    voller_name, strasse, plz, email, rufnummer = teile
                    namen_teile = voller_name.split(" ", 1)
                    vorname = namen_teile[0]
                    nachname = namen_teile[1] if len(namen_teile) > 1 else ""
                    liste.append({
                        "vorname": vorname,
                        "nachname": nachname,
                        "strasse": strasse,
                        "plz": plz,
                        "email": email,
                        "rufnummer": rufnummer,
                        "mobil": ""
                    })
    except Exception as e:
        print(f"Fehler beim Laden: {e}")
    return liste

def speichern(contact_liste):
    """Speichert die Liste alphabetisch sortiert nach Nachname."""
    contact_liste.sort(key=lambda e: (e["nachname"].lower(), e["vorname"].lower()))
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    file_path = os.path.join(base_path, DATEINAME)
    try:
        with open(file_path, "w", encoding="utf-8") as datei:
            for e in contact_liste:
                mobil = e.get("mobil", "")
                datei.write(f"{e['vorname']}|{e['nachname']}|{e['strasse']}|{e['plz']}|{e['email']}|{e['rufnummer']}|{mobil}\n")
    except IOError as e:
        print(f"Fehler beim Speichern: {e}")

# ==============================================================================
# ROUTES
# ==============================================================================

@contact_manager_bp.route('/')
def index():
    return render_template('cm_index.html')

@contact_manager_bp.route('/api/contacts', methods=['GET'])
def get_contacts():
    contacts = laden()
    return jsonify(contacts)

@contact_manager_bp.route('/api/contacts', methods=['POST'])
def add_contact():
    new_contact = request.json
    contacts = laden()
    contacts.append(new_contact)
    speichern(contacts)
    return jsonify({"status": "success", "message": "Contact added"}), 201

@contact_manager_bp.route('/api/contacts/<int:index>', methods=['PUT'])
def update_contact(index):
    updated_data = request.json
    contacts = laden()
    if 0 <= index < len(contacts):
        contacts[index] = updated_data
        speichern(contacts)
        return jsonify({"status": "success", "message": "Contact updated"})
    return jsonify({"status": "error", "message": "Index out of range"}), 404

@contact_manager_bp.route('/api/contacts/<int:index>', methods=['DELETE'])
def delete_contact(index):
    contacts = laden()
    if 0 <= index < len(contacts):
        contacts.pop(index)
        speichern(contacts)
        return jsonify({"status": "success", "message": "Contact deleted"})
    return jsonify({"status": "error", "message": "Index out of range"}), 404
