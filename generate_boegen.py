#!/usr/bin/env python3
"""Kennlernbögen für ein Geburtstagskind.

Jede Person bekommt einen eigenen Bogen mit fünf Fragen. In jeder Antwort
ist bereits ein Wort vorgedruckt. Der eigene Satz wird links und rechts
darum herum geschrieben. Liest man danach nur diese Wörter
in der Runde, ergibt sich eine Laudatio.

Die Wörterliste unten ist die einzige Quelle. Es müssen genau
SHEET_COUNT × 5 Fragen Wörter sein, in der Vorlesereihenfolge.
Die Wörter werden round-robin auf die Bögen verteilt: Wort 1 auf Bogen 1,
Wort 2 auf Bogen 2, …, Wort 11 wieder auf Bogen 1.
Satzzeichen gehören zum Wort, damit beim Vorlesen Punkt und Komma sitzen.

Aufruf:
    python3 generate_boegen.py

Erzeugt im Ordner pdf/:
    bogen-01.pdf …               (die Bögen zum Auslegen)
    alle-boegen.pdf               (dieselben Bögen in einer Datei)
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

NAME = "Doro"

# Fließender Text aus input-default.md. Vorgelesen von 1 bis N (SHEET_COUNT × 5):
WORDS = [
    "Liebe", "Doro,", "heute", "feiern", "wir",
    "dich!", "Es", "ist", "wunderbar,", "dass",
    "es", "dich", "gibt.", "Du", "bist",
    "nicht", "nur", "eine", "tolle", "Mama,",
    "sondern", "auch", "eine", "großartige", "Freundin.",
    "Wir", "schätzen", "deine", "ehrliche,", "wertschätzende,",
    "liebevolle", "und", "großzügige", "Art.", "Dein",
    "Humor", "ist", "weltklasse,", "denn", "mit",
    "dir", "hat", "man", "immer", "was",
    "zu", "Lachen.", "Wir", "lieben", "dich!",
]

QUESTIONS = [
    "Da bin ich Doro das erste Mal begegnet",
    "Mein schönstes/lustigstes/... Erlebnis mit Doro",
    "Diese Eigenschaft schätze ich an Doro",
    "Dieses Essen oder Getränk verbinde ich mit Doro",
    "Welches Tier passt am besten zu ihrem Charakter?",
]

# Anteil der Schreibzeile, an dem das Wort sitzt.
# Bewusst verschieden, damit mal davor und mal dahinter mehr Platz ist.
ANCHORS = [0.48, 0.52, 0.45, 0.55, 0.50]

QUESTION_SHORT = [
    "Begegnung",
    "Erlebnis",
    "Eigenschaft",
    "Essen, Getränk",
    "Tier",
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

def instruction_text() -> str:
    return (
        "Beantworte die fünf Fragen von Hand. "
        "In jeder Antwort steht schon ein Wort. Schreib links und rechts davon weiter; "
        "das Wort bleibt mitsamt Satzzeichen stehen. "
        "Beispiel: Aus „Sommer“ wird „an einem warmen Sommer am See“. "
        f"Die vorgedruckten Wörter ergeben zusammen eine Laudatio für {NAME}. "
        "Bitte vorher nicht verraten."
    )


def laudatio_text() -> str:
    return " ".join(WORDS)


def sheets() -> list[list[tuple[int, str]]]:
    """Wörter round-robin auf die Bögen verteilen.

    Wort 1 → Bogen 1, Wort 2 → Bogen 2, …, Wort 10 → Bogen 10,
    Wort 11 → wieder Bogen 1. Jeder Bogen erhält fünf Wörter mit den
    Nummern sheet, sheet+SHEET_COUNT, sheet+2·SHEET_COUNT, …
    """
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
            index = sheet + question * SHEET_COUNT
            chunk.append((index + 1, WORDS[index]))
        built.append(chunk)
    return built


def register_fonts() -> None:
    bundled = Path(__file__).resolve().parent / "fonts"
    files = {
        "Sans": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Regular.ttf"),
            Path("/usr/share/fonts/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]),
        "Sans-Bold": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Bold.ttf"),
            Path("/usr/share/fonts/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]),
        "Sans-Italic": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-Italic.ttf"),
            Path("/usr/share/fonts/liberation/LiberationSans-Italic.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ]),
        "Sans-BoldItalic": _first_existing([
            Path("/usr/share/fonts/truetype/macos/Inter-BoldItalic.ttf"),
            Path("/usr/share/fonts/liberation/LiberationSans-BoldItalic.ttf"),
            Path("/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ]),
        "Script": bundled / "GreatVibes-Regular.ttf",
        "Display": bundled / "PlayfairDisplay-Black.ttf",
        "Serif": bundled / "PlayfairDisplay-Regular.ttf",
        "Serif-Bold": bundled / "PlayfairDisplay-Bold.ttf",
        "Serif-Italic": bundled / "PlayfairDisplay-Italic.ttf",
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


def chip_size(word: str) -> tuple[float, float, float]:
    """Width, height, word size."""
    word_size = 12
    word_w = pdfmetrics.stringWidth(word, "Serif-Bold", word_size)
    pad_x = 5.5
    ascent, descent = vertical_metrics("Serif-Bold", word_size)
    pad_y = 3.2
    width = pad_x + word_w + pad_x
    height = pad_y + (ascent - descent) + pad_y
    return width, height, word_size


def chip_center(left: float, right: float, word: str, frac: float) -> float:
    width, _height, _word_size = chip_size(word)
    min_side = mm(14)
    half = width / 2
    cx = left + (right - left) * frac
    low = left + min_side + half
    high = right - min_side - half
    if low > high:
        return (left + right) / 2
    return max(low, min(high, cx))


def draw_chip(c: canvas.Canvas, cx: float, baseline_y: float, word: str) -> tuple[float, float, float, float]:
    """Word sitting on the writing line. baseline_y is the text baseline (= line).

    Returns (left, bottom, right, top).
    """
    width, height, word_size = chip_size(word)
    pad_x = 5.5
    pad_y = 3.2
    ascent, descent = vertical_metrics("Serif-Bold", word_size)
    left = cx - width / 2
    bottom = baseline_y + descent - pad_y
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(0.9)
    c.roundRect(left, bottom, width, height, 2.5, stroke=1, fill=1)
    c.setFillColor(colors.black)
    c.setFont("Serif-Bold", word_size)
    c.drawString(left + pad_x, baseline_y, word)
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


def arch_box() -> dict[str, float]:
    """Semicircular arch, the black-and-white reading of the invitation panel."""
    side = mm(13)
    base = mm(12)
    crown_gap = mm(8)
    width = PAGE_W - 2 * side
    radius = width / 2
    crown = PAGE_H - crown_gap
    spring = crown - radius
    return {
        "x": side,
        "base": base,
        "width": width,
        "radius": radius,
        "crown": crown,
        "spring": spring,
        "cx": side + radius,
    }


def draw_arch(c: canvas.Canvas, box: dict[str, float], inset: float = 0, weight: float = 1.15) -> None:
    x = box["x"] + inset
    base = box["base"] + inset
    radius = box["radius"] - inset
    spring = box["spring"]
    width = radius * 2
    path = c.beginPath()
    path.moveTo(x, base)
    path.lineTo(x, spring)
    # arc() would moveTo the curve and break the path; the close then
    # cuts a diagonal from the bottom corner back to the springing point.
    path.arcTo(x, spring - radius, x + width, spring + radius, 180, -180)
    path.lineTo(x + width, base)
    path.close()
    c.saveState()
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.white)
    c.setLineWidth(weight)
    c.setLineJoin(0)
    c.setLineCap(0)
    c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def make_sheet(path: Path, sheet_index: int, entries: list[tuple[int, str]]) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(f"Für {NAME} — Kennlernbogen {sheet_index + 1}")
    c.setAuthor(f"Geburtstagsspiel für {NAME}")

    box = arch_box()
    draw_arch(c, box, inset=0, weight=1.2)
    draw_arch(c, box, inset=mm(2.3), weight=0.45)

    inset = mm(9)
    left = box["x"] + inset
    right = box["x"] + box["width"] - inset
    width = right - left
    center = box["cx"]

    c.setFillColor(colors.black)
    c.setFont("Script", 30)
    c.drawCentredString(center, from_top(28), "Zum Geburtstag")

    draw_tracked(c, f"FÜR {NAME.upper()}", center, from_top(52), "Display", 32, 1.15)

    c.setFont("Serif-Italic", 10)
    c.drawCentredString(center, from_top(62.5), "Ein Bogen zum Kennenlernen")

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    rule = mm(18)
    c.line(center - rule, from_top(68), center + rule, from_top(68))

    style = ParagraphStyle(
        "instr",
        fontName="Serif",
        fontSize=8.4,
        leading=11.0,
        textColor=colors.black,
        alignment=TA_CENTER,
    )
    paragraph = Paragraph(instruction_text(), style)
    _instr_w, instr_h = paragraph.wrap(width - mm(4), 240)
    instr_top = from_top(74)
    paragraph.drawOn(c, left + mm(2), instr_top - instr_h)

    footer_y = box["base"] + mm(6.5)
    block_top = instr_top - instr_h - mm(8)
    block_bottom = footer_y + mm(6)
    section_h = (block_top - block_bottom) / len(QUESTIONS)

    for q, (question, (_number, word)) in enumerate(zip(QUESTIONS, entries)):
        sec_top = block_top - q * section_h
        sec_bottom = sec_top - section_h
        if q > 0:
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.3)
            c.line(left, sec_top, right, sec_top)

        q_baseline = sec_top - mm(5.6)
        c.setFillColor(colors.black)
        c.setFont("Display", 11)
        q_label = str(q + 1)
        c.drawString(left, q_baseline, q_label)
        num_w = c.stringWidth(q_label, "Display", 11)
        q_x = left + num_w + 7
        c.setFont("Serif", 11)
        if c.stringWidth(question, "Serif", 11) > right - q_x:
            raise SystemExit(f"Frage {q + 1} ist zu lang für die Zeile: {question}")
        c.drawString(q_x, q_baseline, question)

        # Two writing lines: the arch needs the upper page, and two lines
        # still leave room to write around the printed word.
        line_top = q_baseline - mm(8.2)
        line_bottom = sec_bottom + mm(4.2)
        baselines = [line_top, line_bottom]
        cx = chip_center(left, right, word, ANCHORS[q])
        bounds = draw_chip(c, cx, baselines[0], word)
        draw_line(c, left, right, baselines[0], bounds)
        draw_line(c, left, right, baselines[1])

    c.setFillColor(colors.black)
    c.setFont("Serif", 8)
    c.drawCentredString(
        center,
        footer_y,
        f"Bogen {sheet_index + 1} von {SHEET_COUNT}",
    )

    c.showPage()
    c.save()


def make_moderation(path: Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setTitle(f"Für {NAME} — Moderation, nicht auslegen")
    c.setAuthor(f"Geburtstagsspiel für {NAME}")

    left = mm(16)
    right = PAGE_W - mm(16)
    width = right - left
    center = PAGE_W / 2

    sub = ParagraphStyle(
        "sub", fontName="Serif-Italic", fontSize=9, leading=12,
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
        "quote", fontName="Serif", fontSize=11, leading=15.4,
        alignment=TA_LEFT, textColor=colors.black,
    )
    note = ParagraphStyle(
        "note", fontName="Sans", fontSize=8, leading=10.6,
        alignment=TA_LEFT, textColor=colors.black,
    )

    c.setFillColor(colors.black)
    c.setFont("Script", 20)
    c.drawCentredString(center, from_top(16), "Nicht auslegen")
    draw_tracked(c, f"FÜR {NAME.upper()}", center, from_top(28), "Display", 22, 0.9)
    y = from_top(32)
    total = len(WORDS)

    flow = [
        Paragraph("Moderationsblatt zur Laudatio", sub),
        Paragraph("So spielt ihr", head),
        Paragraph(
            f"<b>1</b>  Die {SHEET_COUNT} Bögen verdeckt auslegen. Jede Person nimmt einen. "
            "Dieses Blatt bleibt bei dir.",
            step,
        ),
        Paragraph("<b>2</b>  Jede Person beantwortet die fünf Fragen. Das vorgedruckte Wort bleibt stehen, der eigene Satz legt sich links und rechts darum. Den eigenen Namen nicht auf den Bogen schreiben — der wird erraten.", step),
        Paragraph("<b>3</b>  Wer mag, liest die eigenen Antworten vor. So lernen sich alle kennen. Die festen Wörter machen die Sätze absichtlich etwas schief.", step),
        Paragraph(
            "<b>4</b>  Danach lest nur die vorgedruckten Wörter. "
            f"Zuerst Frage 1, von Bogen 1 bis Bogen {SHEET_COUNT}, dann Frage 2, und so weiter. "
            "An Punkt und Komma kurz innehalten.",
            step,
        ),
        Paragraph("<b>5</b>  Lies zum Schluss den Text unten noch einmal in Ruhe als Ganzes vor.", step),
        Paragraph("Die Laudatio", head),
        Paragraph(laudatio_text(), quote),
        Paragraph(
            f"{total} Wörter, {SHEET_COUNT} Bögen, auf jedem Bogen fünf Wörter. "
            f"Wort 1 liegt auf Bogen 1, Wort 2 auf Bogen 2, …, Wort {SHEET_COUNT} auf Bogen {SHEET_COUNT}; "
            f"Wort {SHEET_COUNT + 1} wieder auf Bogen 1, und so weiter.",
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
    c.drawRightString(right, mm(10.5), f"Für {NAME}")
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
