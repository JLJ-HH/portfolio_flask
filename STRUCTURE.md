# Projekt-Struktur & Architektur

Dieser Plan gibt eine Übersicht über den Aufbau des Flask-Portfolios und die Verantwortlichkeiten der einzelnen Komponenten.

## Architektur-Übersicht

```mermaid
graph TD
    A[app.py - Flask Server] --> B[templates/ - Jinja2 Templates]
    A --> C[static/ - Statische Dateien]
    A --> D[projects.json - Datenquelle]
    
    B --> B1[base.html - Grundgerüst]
    B1 --> B2[home.html]
    B1 --> B3[about.html]
    B1 --> B4[projects.html]
    B1 --> B5[contact.html]
    
    C --> C1[css/ - Styling]
    C --> C2[js/ - Logik]
    C --> C3[content/ - Content]
    C --> C4[images/ - Assets]
    
    C3 --> C3a[about_me.md]
    C1 --> C1a[home.css]
    C1 --> C1b[about.css]
    C1 --> C1c[layout.css]
```

## Dateiverzeichnis

- **`app.py`**: Der zentrale Einstiegspunkt. Hier werden die Routes definiert, die `projects.json` geladen und das Mail-Setup verwaltet.
- **`projects.json`**: Enthält alle Projektdaten (Titel, Tech-Stack, Links, Beschreibungen).
- **`templates/`**:
    - `base.html`: Beinhaltet Navbar und Footer, die auf jeder Seite gleich sind.
    - `about.html`: Nutzt ein 70/30 Split-Layout für maximale visuelle Wirkung.
- **`static/`**:
    - `content/about_me.md`: Erlaubt es, den "Über mich" Text einfach in Markdown/HTML zu pflegen, ohne den Code zu ändern.
    - `css/home.css` & `about.css`: Enthalten das spezifische Premium-Styling für die jeweiligen Seiten.

## Datenfluss

1. Der Nutzer ruft eine URL auf (z.B. `/projects`).
2. Flask-Route in `app.py` verarbeitet die Anfrage.
3. Daten werden aus `projects.json` oder `.md` Dateien geladen.
4. Jinja2 rendert das passende Template und injiziert die Daten.
5. Die fertige HTML-Seite wird an den Browser geliefert.
