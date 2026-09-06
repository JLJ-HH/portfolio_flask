# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/)
und dieses Projekt folgt weitgehend [Semantic Versioning](https://semver.org/lang/de/).

---

## [1.2.1] - 2026-09-06

### Hinzugefügt (Added)
- **Agent Guidelines & Workflow-Vorgabe (`AGENTS.md`)**:
  - Etablierung verbindlicher Entwicklungsrichtlinien für Code-Änderungen (Planung, schrittweise Umsetzung, Verifikation mit Commit-Sperre sowie standardisierte Dokumentation & Push).
  - Verbindlicher **Changelog- & Kontext-Check** in Phase 1 (Planung) zur Vermeidung von Halluzinationen, Déjà-vus und redundanter Doppelarbeit.

### Entfernt (Removed)
- **Redundante `GEMINI.md`**:
  - Bereinigung redundanter Regel-Dateien zur Vermeidung von Token-Doppelung und Inkonsistenzen zugunsten von `AGENTS.md` als Single Source of Truth.

---

## [1.2.0] - 2026-09-04

### Hinzugefügt (Added)
- **KI-Antwort-Cache (`ki_cache`)**:
  - Neue SQLite-Tabelle `ki_cache` in `online_bibliothek/db_helper.py` zur persistenten Speicherung von Benutzeranfragen und KI-Antworten mittels SHA256-Hash.
  - Wiederholte oder identische Fragen werden direkt aus dem lokalen Cache beantwortet, ohne API-Tokens zu verbrauchen oder Latenzen zu erzeugen.
- **Graceful Degradation & Ausfall-Fallback**:
  - Intelligente Heuristik-Suche bei Ausfall, Timeout oder Rate-Limits des Ollama-Dienstes: Die Anwendung führt automatisch eine lokale SQLite-Katalogsuche (`LIKE`-Query) durch und liefert passende Treffer aus dem Bestand zurück.

### Geändert (Changed)
- **Ollama AI-Upgrade auf `gemma4:31b`**:
  - Umstellung des KI-Modells von `gemma3:12b` auf `gemma4:31b` in allen Blueprint-Routen (`online_bibliothek/routes.py`) für verbesserte Empfehlungsqualität, Textverständnis und Metadaten-Extraktion.
- **RAG-Kontext- & Token-Optimierung**:
  - Reduktion des Input-Token-Verbrauchs um bis zu 80 % durch gezielte Kontext-Kompaktierung (Kürzung von Buchzusammenfassungen auf maximal 180 Zeichen, Verzicht auf rohe Inhaltsverzeichnisse im Prompt).
  - Einführung eines festen `max_tokens`-Budgets (500 Tokens) und strukturierter 3-Absatz-Regeln für prägnante, schnelle und leserfreundliche Buchempfehlungen.
- **Architektur- & Dokumentations-Aktualisierung**:
  - Aktualisierung von [README.md](file:///c:/github/portfolio_flask/README.md), [online_bibliothek_info.txt](file:///c:/github/portfolio_flask/static/content/online_bibliothek_info.txt) und dem Mermaid-Architekturdiagramm [online_bibliothek_structure.mmd](file:///c:/github/portfolio_flask/static/content/online_bibliothek_structure.mmd) zur Dokumentation des neuen Modells und der Caching-Schicht.

---

## [1.1.0] - 2026-07-26

### Behoben (Fixed)
- **Hosting- & CGI-Kompatibilität (Strato)**:
  - Anpassung der `bcrypt`-Bibliothek auf Version `3.2.2` zur Behebung von Kompatibilitätsproblemen in Shared-Hosting-Umgebungen.
  - Optimierung des `app.cgi`-Wrappers mit automatischem Dependency-Check und `ScriptNameFixer` für suchmaschinenfreundliche URLs.

### Geändert (Changed)
- **Interaktiver Projekt-Showcase**:
  - Implementierung eines interaktiven Projekt-Sliders mit dynamischen Glassmorphic-Effekten und sequentiellen Hover- bzw. Klick-Animationen.
  - Erweiterung der Projektdaten (`projects.json`) und Video-Showcases zur Veranschaulichung der Funktionalität.
- **Dokumentationsüberarbeitung**:
  - Umfassende Überarbeitung der `README.md` zur Präsentation des modularen Blueprint-Ökosystems und des persönlichen Werdegangs ("Vom Koch zum Coder").

---

## [1.0.0] - 2026-03-12

### Hinzugefügt (Added)
- **Modulare Flask-Blueprint-Architektur**:
  - Zentraler Server (`app.py`) mit dynamischer Einbindung modularer Teil-Anwendungen.
  - **SmartCalc** (`/taschenrechner`): Wissenschaftlicher Web-Taschenrechner mit Formel-Parser, Whitelist-Validierung, RegEx-Preprocessing und Rechenhistorie.
  - **Online-Bibliothek** (`/bibliothek`): Vollständiges Bibliotheksverwaltungssystem mit Rollenkonzept (Mitarbeiter & Kunde), PDF-Text-Extraktion via `pypdf`, RAG-gestütztem KI-Bibliothekar via Ollama API und SQLite3-Persistenz mit Kaskadierung.
  - **Scrum Quiz** (`/scrum-quiz`): Zertifizierungstrainer für PSM I mit mehrsprachigem Fragenkatalog (DE/EN) und dynamischem Zeitmanagement.
- **Sicherheits- & Kommunikationsfeatures**:
  - Kontaktformular mit mehrschichtigem Spamschutz (CSRF-Tokens, Honeypot-Feld, Zeitmessungsüberprüfung und Mathe-Captcha).
  - E-Mail-Verifikationsworkflow bei Registrierungen via `Flask-Mail`.
- **Frontend & Design System**:
  - Responsive UI mit Bootstrap 5, modernen Custom Stylesheets und dynamischem Markdown-Rendering (`markdown2`).
