# José Luis Juárez - Portfolio

Willkommen auf meinem Portfolio-Projekt! Diese Anwendung dient als digitale Visitenkarte und Showcase meiner Projekte als angehender Anwendungsentwickler.

## Tech Stack

- **Backend**: Python (Flask)
- **Frontend**: HTML5, Vanilla CSS3, Bootstrap 5 (für Layout-Grundlagen)
- **Templating**: Jinja2
- **Mail**: Flask-Mail (für das Kontaktformular)
- **Content**: Markdown (via `markdown2` für dynamische Texte)

## Features

- **Redesigned Home Page**: Moderner Einstieg mit Glassmorphism-Effekten und klarer Struktur.
- **Premium About Me**: Radikal überarbeitetes Design mit Fokus auf visuelle Präsenz und professionellen Minimalismus.
- **Project Showcase**: Dynamische Anzeige von Projekten aus einer zentralen `projects.json`.
- **Contact Form**: Voll funktionsfähiges Formular mit E-Mail-Integration.

## Multi-Application Architecture (Blueprints)

Dieses Portfolio nutzt **Flask Blueprints**, um mehrere eigenständige Anwendungen unter einer einzigen Domäne strukturiert zu bündeln. Jede Anwendung ist als modularer Blueprint implementiert:

- **Taschenrechner** (`/taschenrechner`): Ein interaktiver Smart-Rechner.
- **Contact Manager** (`/contact-manager`): Eine Anwendung zur Kontaktverwaltung.
- **Scrum Quiz** (`/scrum-quiz`): Eine Lern-App für Scrum-Zertifizierungen.

Diese Architektur ermöglicht es, spezialisierte Projekte in separaten Verzeichnissen zu entwickeln und sie nahtlos in das Hauptportfolio zu integrieren, ohne den Code der Hauptanwendung zu überladen.

## Autor

**José Luis Juárez** - Angehender Anwendungsentwickler aus Hamburg.
[GitHub Profil](https://github.com/Luis-Juarez-Juarez)
[Strato Portfolio](https://jljuarez.de/)
