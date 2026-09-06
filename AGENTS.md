# Entwicklungs- & Arbeitsrichtlinien (Agent Guidelines)

## Workflow-Vorgabe für Code-Änderungen

Für sämtliche Code-Änderungen in diesem Projekt gilt zwingend folgender 4-stufiger Workflow:

### 1. Planung
- **Changelog- & Kontext-Check**: Vor jeder Recherche und Planung MUSS zwingend die `CHANGELOG.md` sowie der aktuelle Codebestand geprüft werden, um den exakten Entwicklungsstand zu kennen, Doppelarbeit/Déjà-vus zu verhindern und keine bereits gelösten Probleme oder überholten Ansätze zu wiederholen.
- Erstelle vor größeren Änderungen immer einen kurzen Implementierungsplan.
- Kläre Abhängigkeiten, betroffene Dateien und das Vorgehen vor der eigentlichen Umsetzung.

### 2. Umsetzung
- Führe den genehmigten bzw. definierten Plan schrittweise und strukturiert aus.
- Halte Änderungen fokussiert und nachvollziehbar.

### 3. Verifikation (Commit-Sperre)
- **Commit- und Push-Sperre**: Bevor ein Git-Commit oder Push erfolgt, MUSS die Änderung zwingend auf Fehler geprüft werden.
  - Führe Syntax-Checks, Build-/Type-Checks, Linting oder vorhandene automatisierte Tests aus (z. B. Syntaxprüfungen via Python, Linter, Komponententests).
  - **Fehlerbehandlung**: Schlägt ein Test fehl oder treten Compiler-/Linter-Fehler auf, behebe das Problem zuerst.
  - **Strikte Vorgabe**: Commits und Pushes unvollständiger oder fehlerhafter Zwischenstände sind strikt untersagt.

### 4. Abschluss & Dokumentation
Erst wenn alle Prüfungen erfolgreich und ohne Fehler bestanden sind:
1. **CHANGELOG.md aktualisieren**: Ergänze automatisch die `CHANGELOG.md` mit den vorgenommenen Änderungen und behobenen Problemen (gemäß *Keep a Changelog*).
2. **Git Commit & Push**: Erstelle einen sauberen Git-Commit mit einer präzisen, aussagekräftigen Commit-Message und pushe den Stand zu GitHub.
3. **Nächsten Schritt anfragen**: Frage anschließend, welcher Schritt als Nächstes ansteht.
