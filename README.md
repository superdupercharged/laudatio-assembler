# Kennlernbögen — konfigurierbarer Generator

Interaktive Website (GitHub Pages): Anzahl Bögen, fünf Fragen, Laudatio-Text
und Name einstellen, dann PDF im Browser erzeugen und herunterladen.

Lokal die Site ansehen:

```bash
python3 -m http.server 8000 --directory docs
```

Dann http://localhost:8000 öffnen.

## PDF auch per Skript

```bash
pip install -r requirements.txt
python3 generate_boegen.py
```

Konfiguration oben in `generate_boegen.py` (`NAME`, `SHEET_COUNT`, `QUESTIONS`, `WORDS`).
Die Wortanzahl muss genau `SHEET_COUNT × 5` sein; Satzzeichen gehören zum Wort.
Die Wörter liegen round-robin auf den Bögen: Wort 1 auf Bogen 1, Wort 2 auf Bogen 2, Wort 11 wieder auf Bogen 1.
