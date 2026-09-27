/**
 * Client-side PDF generation for Kennlernbögen (mirrors generate_boegen.py layout).
 */
import {
  PDFDocument,
  rgb,
  LineCapStyle,
  LineJoinStyle,
  moveTo,
  lineTo,
  appendBezierCurve,
  closePath,
  stroke,
  setLineWidth,
  setStrokingRgbColor,
  setFillingRgbColor,
  setLineCap,
  setLineJoin,
} from "https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/+esm";
import fontkitModule from "https://cdn.jsdelivr.net/npm/@pdf-lib/fontkit@1.1.1/+esm";

const fontkit = fontkitModule.default ?? fontkitModule;
const PAGE_W = 595.28;
const PAGE_H = 841.89;
const MM = 72 / 25.4;
const ANCHORS = [0.48, 0.52, 0.45, 0.55, 0.5];
const BLACK = rgb(0, 0, 0);
const WHITE = rgb(1, 1, 1);
const KAPPA = 0.5522847498;

export function countWords(text) {
  const t = text.trim();
  if (!t) return 0;
  return t.split(/\s+/).length;
}

export function splitWords(text) {
  const t = text.trim();
  if (!t) return [];
  return t.split(/\s+/);
}

function mm(v) {
  return v * MM;
}

function fromTop(vMm) {
  return PAGE_H - mm(vMm);
}

function archBox() {
  const side = mm(13);
  const base = mm(12);
  const crownGap = mm(8);
  const width = PAGE_W - 2 * side;
  const radius = width / 2;
  const crown = PAGE_H - crownGap;
  const spring = crown - radius;
  return { x: side, base, width, radius, crown, spring, cx: side + radius };
}

function drawArch(page, box, inset = 0, weight = 1.15) {
  const x = box.x + inset;
  const base = box.base + inset;
  const radius = box.radius - inset;
  const spring = box.spring;
  const width = radius * 2;
  const right = x + width;
  const cx = x + radius;
  const crown = spring + radius;
  const k = radius * KAPPA;

  page.pushOperators(
    setStrokingRgbColor(0, 0, 0),
    setFillingRgbColor(1, 1, 1),
    setLineWidth(weight),
    setLineJoin(LineJoinStyle.Miter),
    setLineCap(LineCapStyle.Butt),
    moveTo(x, base),
    lineTo(x, spring),
    // Upper semicircle left → right via crown
    appendBezierCurve(x, spring + k, cx - k, crown, cx, crown),
    appendBezierCurve(cx + k, crown, right, spring + k, right, spring),
    lineTo(right, base),
    closePath(),
    stroke(),
  );
}

function drawTracked(page, text, cx, y, font, size, tracking) {
  const widths = [...text].map((ch) => font.widthOfTextAtSize(ch, size));
  const total = widths.reduce((a, b) => a + b, 0) + tracking * Math.max(0, text.length - 1);
  let x = cx - total / 2;
  for (let i = 0; i < text.length; i++) {
    page.drawText(text[i], { x, y, size, font, color: BLACK });
    x += widths[i] + tracking;
  }
}

function chipSize(fontSerifBold, word) {
  const wordSize = 12;
  const wordW = fontSerifBold.widthOfTextAtSize(word, wordSize);
  const padX = 5.5;
  const ascent = wordSize * 0.8;
  const descent = wordSize * -0.2;
  const padY = 3.2;
  const width = padX + wordW + padX;
  const height = padY + (ascent - descent) + padY;
  return { width, height, wordSize, padX, ascent, descent };
}

function chipCenter(left, right, fontSerifBold, word, frac) {
  const { width } = chipSize(fontSerifBold, word);
  const minSide = mm(14);
  const half = width / 2;
  const cx = left + (right - left) * frac;
  const low = left + minSide + half;
  const high = right - minSide - half;
  if (low > high) return (left + right) / 2;
  return Math.max(low, Math.min(high, cx));
}

function drawChip(page, fonts, cx, cy, word) {
  const { serifBold } = fonts;
  const s = chipSize(serifBold, word);
  const left = cx - s.width / 2;
  const bottom = cy - s.height / 2;
  page.drawRectangle({
    x: left,
    y: bottom,
    width: s.width,
    height: s.height,
    borderColor: BLACK,
    borderWidth: 0.9,
    color: WHITE,
  });
  const wordBaseline = cy - (s.ascent + s.descent) / 2;
  page.drawText(word, {
    x: left + s.padX,
    y: wordBaseline,
    size: s.wordSize,
    font: serifBold,
    color: BLACK,
  });
  return { left, bottom, right: left + s.width, top: bottom + s.height };
}

function drawWritingLine(page, x0, x1, y, chip) {
  if (!chip) {
    page.drawLine({ start: { x: x0, y }, end: { x: x1, y }, thickness: 0.7, color: BLACK });
    return;
  }
  if (chip.left > x0) {
    page.drawLine({
      start: { x: x0, y },
      end: { x: chip.left, y },
      thickness: 0.7,
      color: BLACK,
    });
  }
  if (chip.right < x1) {
    page.drawLine({
      start: { x: chip.right, y },
      end: { x: x1, y },
      thickness: 0.7,
      color: BLACK,
    });
  }
}

function wrapCenteredText(text, font, size, maxWidth, leading) {
  const words = text.split(/\s+/);
  const lines = [];
  let current = "";
  for (const word of words) {
    const trial = current ? `${current} ${word}` : word;
    if (font.widthOfTextAtSize(trial, size) <= maxWidth) {
      current = trial;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  }
  if (current) lines.push(current);
  return { lines, height: lines.length * leading };
}

function instructionText(name) {
  return (
    `Beantworte die fünf Fragen von Hand. ` +
    `In jeder Antwort steht schon ein Wort. Schreib links und rechts davon weiter; ` +
    `das Wort bleibt mitsamt Satzzeichen stehen. ` +
    `Beispiel: Aus „Sommer“ wird „an einem warmen Sommer am See“. ` +
    `Die vorgedruckten Wörter ergeben zusammen eine Laudatio für ${name}. ` +
    `Bitte vorher nicht verraten.`
  );
}

async function loadFonts(pdfDoc) {
  const load = async (path) => {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Schrift fehlt: ${path}`);
    return res.arrayBuffer();
  };
  const [scriptB, displayB, serifB, serifBoldB, serifItalicB] = await Promise.all([
    load("fonts/GreatVibes-Regular.ttf"),
    load("fonts/PlayfairDisplay-Black.ttf"),
    load("fonts/PlayfairDisplay-Regular.ttf"),
    load("fonts/PlayfairDisplay-Bold.ttf"),
    load("fonts/PlayfairDisplay-Italic.ttf"),
  ]);
  const [script, display, serif, serifBold, serifItalic] = await Promise.all([
    pdfDoc.embedFont(scriptB),
    pdfDoc.embedFont(displayB),
    pdfDoc.embedFont(serifB),
    pdfDoc.embedFont(serifBoldB),
    pdfDoc.embedFont(serifItalicB),
  ]);
  return { script, display, serif, serifBold, serifItalic };
}

function drawSheet(page, fonts, config, sheetIndex, entries) {
  const { name, sheetCount, questions } = config;
  const titleName = name.trim().toUpperCase();

  const box = archBox();
  drawArch(page, box, 0, 1.2);
  drawArch(page, box, mm(2.3), 0.45);

  const inset = mm(9);
  const left = box.x + inset;
  const right = box.x + box.width - inset;
  const width = right - left;
  const center = box.cx;

  page.drawText("Zum Geburtstag", {
    x: center - fonts.script.widthOfTextAtSize("Zum Geburtstag", 30) / 2,
    y: fromTop(28),
    size: 30,
    font: fonts.script,
    color: BLACK,
  });

  drawTracked(page, `FÜR ${titleName}`, center, fromTop(52), fonts.display, 32, 1.15);

  const subtitle = "Ein Bogen zum Kennenlernen";
  page.drawText(subtitle, {
    x: center - fonts.serifItalic.widthOfTextAtSize(subtitle, 10) / 2,
    y: fromTop(62.5),
    size: 10,
    font: fonts.serifItalic,
    color: BLACK,
  });

  page.drawLine({
    start: { x: center - mm(18), y: fromTop(68) },
    end: { x: center + mm(18), y: fromTop(68) },
    thickness: 0.5,
    color: BLACK,
  });

  const instr = instructionText(name.trim());
  const leading = 11;
  const wrapped = wrapCenteredText(instr, fonts.serif, 8.4, width - mm(4), leading);
  let instrY = fromTop(74);
  for (const line of wrapped.lines) {
    const lw = fonts.serif.widthOfTextAtSize(line, 8.4);
    page.drawText(line, {
      x: left + mm(2) + (width - mm(4) - lw) / 2,
      y: instrY - 8.4,
      size: 8.4,
      font: fonts.serif,
      color: BLACK,
    });
    instrY -= leading;
  }

  const footerY = box.base + mm(6.5);
  const blockTop = instrY - mm(8);
  const blockBottom = footerY + mm(15);
  const sectionH = (blockTop - blockBottom) / questions.length;

  for (let q = 0; q < questions.length; q++) {
    const question = questions[q];
    const word = entries[q];
    const secTop = blockTop - q * sectionH;
    const secBottom = secTop - sectionH;
    if (q > 0) {
      page.drawLine({
        start: { x: left, y: secTop },
        end: { x: right, y: secTop },
        thickness: 0.3,
        color: BLACK,
      });
    }

    const qBaseline = secTop - mm(5.6);
    const qLabel = String(q + 1);
    page.drawText(qLabel, {
      x: left,
      y: qBaseline,
      size: 11,
      font: fonts.display,
      color: BLACK,
    });
    const numW = fonts.display.widthOfTextAtSize(qLabel, 11);
    const qX = left + numW + 7;
    if (fonts.serif.widthOfTextAtSize(question, 11) > right - qX) {
      throw new Error(`Frage ${q + 1} ist zu lang für die Zeile.`);
    }
    page.drawText(question, {
      x: qX,
      y: qBaseline,
      size: 11,
      font: fonts.serif,
      color: BLACK,
    });

    const lineTop = qBaseline - mm(8.2);
    const lineBottom = secBottom + mm(4.2);
    const cx = chipCenter(left, right, fonts.serifBold, word, ANCHORS[q]);
    const bounds = drawChip(page, fonts, cx, lineTop, word);
    drawWritingLine(page, left, right, lineTop, bounds);
    drawWritingLine(page, left, right, lineBottom, null);
  }

  const sign = name.trim();
  page.drawText(sign, {
    x: center - fonts.script.widthOfTextAtSize(sign, 15) / 2,
    y: footerY + mm(8),
    size: 15,
    font: fonts.script,
    color: BLACK,
  });
  const footer = `Bogen ${sheetIndex + 1} von ${sheetCount}`;
  page.drawText(footer, {
    x: center - fonts.serif.widthOfTextAtSize(footer, 8) / 2,
    y: footerY,
    size: 8,
    font: fonts.serif,
    color: BLACK,
  });
}

/**
 * @param {{ name: string, sheetCount: number, questions: string[], words: string[] }} config
 * @returns {Promise<Uint8Array>}
 */
export async function generatePdf(config) {
  const { name, sheetCount, questions, words } = config;
  const expected = sheetCount * questions.length;
  if (questions.length !== 5) {
    throw new Error("Es müssen genau fünf Fragen sein.");
  }
  if (words.length !== expected) {
    throw new Error(
      `Die Laudatio hat ${words.length} Wörter, gebraucht werden ${expected} ` +
        `(${sheetCount} Bögen × ${questions.length} Fragen).`,
    );
  }
  if (!name.trim()) {
    throw new Error("Bitte einen Namen angeben.");
  }

  const pdfDoc = await PDFDocument.create();
  pdfDoc.registerFontkit(fontkit);
  pdfDoc.setTitle(`Für ${name.trim()} — Kennlernbögen`);
  pdfDoc.setAuthor(`Geburtstagsspiel für ${name.trim()}`);
  const fonts = await loadFonts(pdfDoc);

  for (let sheet = 0; sheet < sheetCount; sheet++) {
    const entries = [];
    for (let q = 0; q < questions.length; q++) {
      // Round-robin: word 1 → sheet 1, word 2 → sheet 2, … then wrap.
      const index = sheet + q * sheetCount;
      entries.push(words[index]);
    }
    const page = pdfDoc.addPage([PAGE_W, PAGE_H]);
    drawSheet(page, fonts, config, sheet, entries);
  }

  return pdfDoc.save();
}
