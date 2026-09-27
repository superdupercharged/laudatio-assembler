#!/usr/bin/env python3
"""Kennlernbögen für Doros Geburtstag.

Jede Person bekommt einen eigenen Bogen mit fünf Fragen. In jeder Antwort
ist bereits ein Wort vorgedruckt. Der eigene Satz wird links und rechts
darum herum geschrieben. Liest man danach nur die nummerierten Wörter
von 1 bis 50, ergibt sich eine Laudatio.

Die Wörterliste unten ist die einzige Quelle. Es müssen genau
10 Bögen × 5 Fragen = 50 Wörter sein, in der Vorlesereihenfolge.
Satzzeichen gehören zum Wort, damit beim Vorlesen Punkt und Komma sitzen.

Aufruf:
    python3 generate_boegen.py

Erzeugt im Ordner pdf/:
    bogen-01.pdf … bogen-10.pdf   (die Bögen zum Auslegen)
    alle-boegen.pdf               (dieselben zehn Bögen in einer Datei)
    moderation-nicht-auslegen.pdf (Ablauf und Lösung, nur für die Moderation)
"""

from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

# Fließender Text, 50 Wörter. Vorgelesen von 1 bis 50:
# Doro, du bist ein Licht. Dein Lachen öffnet die Herzen. Deine Wärme
# schenkt Geborgenheit. Unsere Freundschaft trägt uns durch helle und
# durch schwere Tage. Du hörst zu, ohne zu urteilen. Du feierst das Leben
# und bleibst dir treu. Danke für deinen Mut und dein Leuchten. Heute
# feiern wir dich, Doro.
WORDS = [
    "Doro,", "du", "bist", "ein", "Licht.",
    "Dein", "Lachen", "öffnet", "die", "Herzen.",
    "Deine", "Wärme", "schenkt", "Geborgenheit.", "Unsere",
    "Freundschaft", "trägt", "uns", "durch", "helle",
    "und", "durch", "schwere", "Tage.", "Du",
    "hörst", "zu,", "ohne", "zu", "urteilen.",
    "Du", "feierst", "das", "Leben", "und",
    "bleibst", "dir", "treu.", "Danke", "für",
    "deinen", "Mut", "und", "dein", "Leuchten.",
    "Heute", "feiern", "wir", "dich,", "Doro.",
]

QUESTIONS = [
    "Da bin ich Doro zum ersten Mal begegnet",
    "So lange kenne ich Doro schon",
    "Mein schönstes Erlebnis mit Doro",
    "Das liebe ich an Doro",
    "Welches Essen oder Trinken verbinde ich mit ihr",
]

# Anteil der Schreibzeile, an dem das Wort sitzt.
# Bewusst verschieden, damit mal davor und mal dahinter mehr Platz ist.
ANCHORS = [0.40, 0.62, 0.34, 0.55, 0.46]

QUESTION_SHORT = [
    "Begegnung",
    "Wie lange",
    "Erlebnis",
    "Das liebe ich",
    "Essen, Trinken",
]

SHEET_COUNT = 10

def _first_existing(candidates: list[Path]) -> Path:
    for path in candidates:
        if path.exists():
            return path
    joined = "\n".join(str(path) for path in candidates)
    raise SystemExit(f"Schrift fehlt, keine dieser Dateien existiert:\n{joined}")

PAGE_W, PAGE_H = A4
MM = 72 / 25.4

INSTRUCTION = (
    "Trag deinen Namen ein und beantworte die fünf Fragen von Hand. "
    "In jeder Antwort steht schon ein Wort. Schreib links und rechts davon weiter; "
    "das Wort bleibt mitsamt Satzzeichen stehen. "
    "Beispiel: Aus „Sommer“ wird „an einem warmen Sommer am See“. "
    "Die Zahl ist die Vorlesereihenfolge. Liest man die Wörter von 1 bis 50, "
    "ergibt das eine Laudatio für Doro. Bitte vorher nicht verraten."
)


def laudatio_text() -> str:
    return " ".join(WORDS)


def sheets() -> list[list[tuple[int, str]]]:
    expected = SHEET_COUNT * len(QUESTIONS)
    if len(WORDS) != expected:
        raise SystemExit(
            f"Die Laudatio hat {len(WORDS)} Wörter, gebraucht werden {expected} "
            f"({SHEET_COUNT} Bögen × {len(QUESTIONS)} Fragen)."
        )
    if len(QUESTIONS) != len(ANCHORS):
        raise SystemExit("Zu jeder Frage gehört eine Position in ANCHORS.")
    built = []
    for sheet in range(SHEET_COUNT):
        chunk = []
        for question in range(len(QUESTIONS)):
            index = sheet * len(QUESTIONS) + question
            chunk.append((index + 1, WORDS[index]))
        built.append(chunk)
    return built


def register_fonts() -> None:
    files = {
        "Sans": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]),
        "Sans-Bold": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]),
        "Sans-Italic": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Italic.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]),
        "Sans-BoldItalic": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-BoldItalic.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]),
        "Serif-Italic": _first_existing([
            Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        ]),
        "Serif": _first_existing([
            Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"),
        ]),
        "Serif-Bold": _first_existing([
            Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"),
        ]),
    }
    for name, path in files.items():
        if not path.exists():
            raise SystemExit(f"Schrift fehlt: {path}")
        pdfmetrics.registerFont(TTFont(name, str(path)))
    pdfmetrics.registerFontFamily(
        "Sans",
        normal="Sans",
        bold="Sans-Bold",
        italic="Sans-Italic",
        boldItalic="Sans-BoldItalic",
    )
    pdfmetrics.registerFontFamily(
        "Serif",
        normal="Serif",
        bold="Serif-Bold",
        italic="Serif-Italic",
        boldItalic="Serif-Bold",
    )


def mm(value: float) -> float:
    return value * MM


def from_top(value_mm: float) -> float:
    return PAGE_H - mm(value_mm)


def draw_tracked(c: canvas.Canvas, text: str, cx: float, y: float,
                 font: str, size: float, tracking: float) -> None:
    c.setFont(font, size)
    widths = [c.stringWidth(ch, font, size) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, width in zip(text, widths):
        c.drawString(x, y, ch)
        x += width + tracking


def vertical_metrics(font: str, size: float) -> tuple[float, float]:
    face = pdfmetrics.getFont(font).face
    return face.ascent * size / 1000, face.descent * size / 1000


def chip_size(number: int, word: str) -> tuple[float, float, float, float, float]:
    """Width, height, number width, word width, word size."""
    word_size = 12
    num_size = 8
    word_w = pdfmetrics.stringWidth(word, "Sans-Bold", word_size)
    num_w = pdfmetrics.stringWidth(f"({number})", "Sans-Bold", num_size)
    pad_x = 5.5
    gap = 3.5
    ascent, descent = vertical_metrics("Sans-Bold", word_size)
    pad_y = 3.2
    width = pad_x + num_w + gap + word_w + pad_x
    height = pad_y + (ascent - descent) + pad_y
    return width, height, num_w, word_w, word_size


def chip_center(left: float, right: float, number: int, word: str, frac: float) -> float:
    width, _height, _nw, _ww, _ws = chip_size(number, word)
    min_side = mm(14)
    half = width / 2
    cx = left + (right - left) * frac
    low = left + min_side + half
    high = right - min_side - half
    if low > high:
        return (left + right) / 2
    return max(low, min(high, cx))


def draw_chip(c: canvas.Canvas, cx: float, cy: float, number: int, word: str) -> tuple[float, float, float, float]:
    """Label centered on (cx, cy). Returns (left, bottom, right, top)."""
    width, height, num_w, _word_w, word_size = chip_size(number, word)
    num_size = 8
    left = cx - width / 2
    bottom = cy - height / 2
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(0.9)
    c.roundRect(left, bottom, width, height, 2.5, stroke=1, fill=1)
    ascent, descent = vertical_metrics("Sans-Bold", word_size)
    word_baseline = cy - (ascent + descent) / 2
    num_ascent, num_descent = vertical_metrics("Sans-Bold", num_size)
    num_baseline = cy - (num_ascent + num_descent) / 2
    pad_x = 5.5
    gap = 3.5
    c.setFillColor(colors.black)
    c.setFont("Sans-Bold", num_size)
    c.drawString(left + pad_x, num_baseline, f"({number})")
    c.setFont("Sans-Bold", word_size)
    c.drawString(left + pad_x + num_w + gap, word_baseline, word)
    c.restoreState()
    return left, bottom, left + width, bottom + height


def draw_line(c: canvas.Canvas, x0: float, x1: float, y: float,
              chip: tuple[float, float, float, float] | None = None) -> None:
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)
    c.setLineWidth(0.7)
    c.setLineCap(0)
    if chip is None:
        c.line(x0, y, x1, y)
    else:
        left, _bottom, right, _top = chip
        if left > x0:
            c.line(x0, y, left, y)
        if right < x1:
            c.line(right, y, x1, y)
    c.restoreState()


def draw_frame(c: canvas.Canvas) -> None:
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.7)
    inset = mm(11)
    c.rect(inset, inset, PAGE_W - 2 * inset, PAGE_H - 2 * inset, stroke=1, fill=0)
    c.restoreState()


def make_sheet(path: Path, sheet_index: int, entries: list[tuple[int, str]]) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(f"Für Doro — Kennlernbogen {sheet_index + 1}")
    c.setAuthor("Geburtstagsspiel für Doro")
    draw_frame(c)

    left = mm(18)
    right = PAGE_W - mm(18)
    width = right - left
    center = PAGE_W / 2

    draw_tracked(c, "ZUM GEBURTSTAG", center, from_top(20.2), "Sans", 8, 2.15)
    c.setFillColor(colors.black)
    c.setFont("Serif-Italic", 28)
    c.drawCentredString(center, from_top(31.6), "Für Doro")

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.6)
    rule_w = mm(26)
    c.line(center - rule_w / 2, from_top(35.6), center + rule_w / 2, from_top(35.6))

    c.setFont("Sans", 9)
    c.drawCentredString(center, from_top(40.4), "Ein Bogen zum Kennenlernen")

    style = ParagraphStyle(
        "instr",
        fontName="Sans",
        fontSize=8.3,
        leading=11.0,
        textColor=colors.black,
        alignment=TA_LEFT,
    )
    paragraph = Paragraph(INSTRUCTION, style)
    _instr_w, instr_h = paragraph.wrap(width, 220)
    instr_top = from_top(46.2)
    paragraph.drawOn(c, left, instr_top - instr_h)

    name_y = instr_top - instr_h - mm(8.2)
    c.setFillColor(colors.black)
    c.setFont("Sans", 11)
    label = "Ich heiße"
    c.drawString(left, name_y, label)
    label_w = c.stringWidth(label, "Sans", 11)
    draw_line(c, left + label_w + 8, right, name_y - 1.2)

    footer_rule_y = mm(18.2)
    block_top = name_y - mm(7.2)
    block_bottom = footer_rule_y + mm(5.5)
    section_h = (block_top - block_bottom) / len(QUESTIONS)

    for q, (question, (number, word)) in enumerate(zip(QUESTIONS, entries)):
        sec_top = block_top - q * section_h
        sec_bottom = sec_top - section_h
        if q > 0:
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.35)
            c.line(left, sec_top, right, sec_top)

        q_baseline = sec_top - mm(6.4)
        c.setFillColor(colors.black)
        c.setFont("Sans-Bold", 11)
        q_label = str(q + 1)
        c.drawString(left, q_baseline, q_label)
        num_w = c.stringWidth(q_label, "Sans-Bold", 11)
        q_x = left + num_w + 8
        c.setFont("Sans", 11.5)
        if c.stringWidth(question, "Sans", 11.5) > right - q_x:
            raise SystemExit(f"Frage {q + 1} ist zu lang für die Zeile: {question}")
        c.drawString(q_x, q_baseline, question)

        line_top = q_baseline - mm(8.6)
        line_bottom = sec_bottom + mm(5.2)
        gap = (line_top - line_bottom) / 2
        baselines = [line_top - i * gap for i in range(3)]

        cx = chip_center(left, right, number, word, ANCHORS[q])
        bounds = draw_chip(c, cx, baselines[0], number, word)
        draw_line(c, left, right, baselines[0], bounds)
        for y in baselines[1:]:
            draw_line(c, left, right, y)

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.45)
    c.line(left, footer_rule_y, right, footer_rule_y)
    first, last = entries[0][0], entries[-1][0]
    c.setFillColor(colors.black)
    c.setFont("Sans", 8)
    foot_y = mm(13.6)
    c.drawString(left, foot_y, f"Bogen {sheet_index + 1} von {SHEET_COUNT}")
    c.drawRightString(right, foot_y, f"Wörter {first}–{last}")

    c.showPage()
    c.save()


def make_moderation(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle("Für Doro — Moderation, nicht auslegen")
    c.setAuthor("Geburtstagsspiel für Doro")

    left = mm(16)
    right = PAGE_W - mm(16)
    width = right - left
    center = PAGE_W / 2

    title = ParagraphStyle(
        "title", fontName="Serif-Italic", fontSize=22, leading=26,
        alignment=TA_CENTER, textColor=colors.black,
    )
    sub = ParagraphStyle(
        "sub", fontName="Sans", fontSize=9, leading=12,
        alignment=TA_CENTER, textColor=colors.black,
    )
    head = ParagraphStyle(
        "head", fontName="Sans-Bold", fontSize=10, leading=13,
        alignment=TA_LEFT, textColor=colors.black,
    )
    step = ParagraphStyle(
        "step", fontName="Sans", fontSize=9, leading=12.1,
        alignment=TA_LEFT, textColor=colors.black,
        leftIndent=13, firstLineIndent=-13,
    )
    quote = ParagraphStyle(
        "quote", fontName="Serif", fontSize=11.5, leading=16.4,
        alignment=TA_LEFT, textColor=colors.black,
    )
    note = ParagraphStyle(
        "note", fontName="Sans", fontSize=8, leading=10.6,
        alignment=TA_LEFT, textColor=colors.black,
    )

    # Kicker is drawn by hand so the letter-spacing matches the Bögen.
    y = from_top(16)
    draw_tracked(c, "NICHT AUSLEGEN", center, y - 8, "Sans-Bold", 8, 1.6)
    y -= 22

    flow = [
        Paragraph("Für Doro", title),
        Paragraph("Moderationsblatt zur Laudatio", sub),
        Paragraph("So spielt ihr", head),
        Paragraph("<b>1</b>  Die zehn Bögen verdeckt auslegen. Jede Person nimmt einen. Dieses Blatt bleibt bei dir.", step),
        Paragraph("<b>2</b>  Jede Person trägt ihren Namen ein und beantwortet die fünf Fragen. Das vorgedruckte Wort bleibt stehen, der eigene Satz legt sich links und rechts darum.", step),
        Paragraph("<b>3</b>  Wer mag, liest die eigenen Antworten vor. So lernen sich alle kennen. Die festen Wörter machen die Sätze absichtlich etwas schief.", step),
        Paragraph("<b>4</b>  Danach lest nur die nummerierten Wörter, von 1 bis 50. Du nennst die Zahl, wer sie auf dem Bogen hat, liest das Wort vor. An Punkt und Komma kurz innehalten.", step),
        Paragraph("<b>5</b>  Lies zum Schluss den Text unten noch einmal in Ruhe als Ganzes vor.", step),
        Paragraph("Die Laudatio", head),
        Paragraph(laudatio_text(), quote),
        Paragraph(
            "50 Wörter, zehn Bögen, auf jedem Bogen fünf Wörter in der richtigen Reihenfolge. "
            "Bogen 1 trägt die Wörter 1 bis 5, Bogen 2 die Wörter 6 bis 10, und so weiter.",
            note,
        ),
        Paragraph("Welches Wort auf welchem Bogen liegt", head),
    ]

    for block in flow:
        extra = 7 if block.style.name == "head" else 0
        if block.style.name == "sub":
            extra = 1
        y -= extra
        _w, h = block.wrap(width if block.style.name != "quote" else width - 12, 800)
        if block.style.name == "sub":
            block.drawOn(c, left, y - h)
            y -= h + 5
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.line(center - mm(20), y, center + mm(20), y)
            y -= 8
            continue
        if block.style.name == "quote":
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.8)
            c.line(left, y - h + 1, left, y - 1)
            block.drawOn(c, left + 10, y - h)
            y -= h + 6
            continue
        block.drawOn(c, left, y - h)
        y -= h + (5 if block.style.name == "head" else 2)

    # Zuordnung, zweispaltig, jede Fünfergruppe ist ein Bogen.
    flat: list[list[str]] = []
    for sheet_index, entries in enumerate(sheets()):
        for q, (number, word) in enumerate(entries):
            flat.append([str(number), word, str(sheet_index + 1), QUESTION_SHORT[q]])
    mid = len(flat) // 2
    header = ["Nr.", "Wort", "Bogen", "Frage"]

    def key_table(data: list[list[str]]) -> Table:
        col_w = (width - mm(6)) / 2
        cols = [col_w * 0.12, col_w * 0.40, col_w * 0.16, col_w * 0.32]
        table = Table([header, *data], colWidths=cols)
        commands = [
            ("FONTNAME", (0, 0), (-1, 0), "Sans-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Sans"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.6),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 1.55),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.35),
            ("ALIGN", (0, 0), (0, -1), "RIGHT"),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ]
        # Fünf Wörter gehören zu einem Bogen: danach eine klarere Linie.
        for row in range(5, len(data), 5):
            commands.append(("LINEBELOW", (0, row), (-1, row), 0.45, colors.black))
        commands.append(("LINEBELOW", (0, -1), (-1, -1), 0.6, colors.black))
        table.setStyle(TableStyle(commands))
        return table

    gap = mm(6)
    left_table = key_table(flat[:mid])
    right_table = key_table(flat[mid:])
    lw, lh = left_table.wrap(width, 700)
    _rw, rh = right_table.wrap(width, 700)
    table_h = max(lh, rh)
    if y - table_h < mm(16):
        raise SystemExit("Die Moderation passt nicht mehr auf eine Seite.")
    left_table.drawOn(c, left, y - table_h)
    right_table.drawOn(c, left + lw + gap, y - table_h)

    c.setFont("Sans", 8)
    c.drawString(left, mm(10.5), "Moderation, nicht auslegen")
    c.drawRightString(right, mm(10.5), "Für Doro")
    c.showPage()
    c.save()


def merge_sheets(paths: list[Path], dest: Path) -> None:
    try:
        from pypdf import PdfReader, PdfWriter
    except ImportError:
        print("Hinweis: pypdf fehlt, alle-boegen.pdf wird nicht erzeugt.", file=sys.stderr)
        return
    writer = PdfWriter()
    for path in paths:
        reader = PdfReader(str(path))
        for page in reader.pages:
            writer.add_page(page)
    with dest.open("wb") as handle:
        writer.write(handle)


def main() -> None:
    register_fonts()
    built = sheets()
    text = laudatio_text()
    if text.split() != WORDS:
        raise SystemExit("Interner Fehler: Laudatio und Wörterliste passen nicht zusammen.")

    out = Path(__file__).resolve().parent / "pdf"
    out.mkdir(exist_ok=True)

    paths = []
    for index, entries in enumerate(built):
        path = out / f"bogen-{index + 1:02d}.pdf"
        make_sheet(path, index, entries)
        paths.append(path)
        print(f"{path.name}: " + " | ".join(f"{n} {word}" for n, word in entries))

    merge_sheets(paths, out / "alle-boegen.pdf")
    make_moderation(out / "moderation-nicht-auslegen.pdf")
    print()
    print(f"{len(WORDS)} Wörter")
    print(text)


if __name__ == "__main__":
    main()
