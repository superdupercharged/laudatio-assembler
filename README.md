# Kennlernbögen für Doro

Schwarz-weiße A4-Bögen zum Geburtstag am 03. Oktober 2026. Das Layout nimmt die Einladung auf: runder Bogen, Schreibschrift, fette Versalien und Blätter in den Ecken, nur als Linie.

Jede Person bekommt einen eigenen Bogen und schreibt zu fünf Fragen einen Satz um ein schon gedrucktes Wort herum. Liest man danach nur die nummerierten Wörter von 1 bis 50, ergibt sich die Laudatio:

> Doro, du bist ein Licht. Dein Lachen öffnet die Herzen. Deine Wärme schenkt Geborgenheit. Unsere Freundschaft trägt uns durch helle und durch schwere Tage. Du hörst zu, ohne zu urteilen. Du feierst das Leben und bleibst dir treu. Danke für deinen Mut und dein Leuchten. Heute feiern wir dich, Doro.

## Drucken

- `pdf/alle-boegen.pdf` — die zehn Bögen, eine Seite je Gast
- `pdf/moderation-nicht-auslegen.pdf` — Ablauf und Lösung, dieses Blatt nicht auslegen

Am einfachsten schwarz-weiß auf A4, ohne Randskalierung („tatsächliche Größe“).

## Neu erzeugen

```bash
pip install -r requirements.txt
python3 generate_boegen.py
```

Die 50 Wörter stehen oben in `generate_boegen.py`. Satzzeichen gehören zum Wort, die Reihenfolge ist die Vorlesereihenfolge.
