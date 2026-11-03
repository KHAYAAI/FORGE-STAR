import re
import sys
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, PageBreak, NextPageTemplate, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
_cond = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf")
if not _cond.exists():  # condensed face not installed everywhere; fall back to regular bold
    _cond = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
pdfmetrics.registerFont(TTFont("Cond-Bold", str(_cond)))
from reportlab.lib.fonts import addMapping
addMapping("Sans", 0, 0, "Sans"); addMapping("Sans", 1, 0, "Sans-Bold")
addMapping("Sans", 0, 1, "Sans"); addMapping("Sans", 1, 1, "Sans-Bold")

INK = colors.HexColor("#0E0F12")
STEEL = colors.HexColor("#1B1E24")
EMBER = colors.HexColor("#FF5A1F")
GOLD = colors.HexColor("#F2A33A")
TEXT = colors.HexColor("#22252B")
MUTED = colors.HexColor("#6B7079")
RULE = colors.HexColor("#E2E4E8")
TINT = colors.HexColor("#FFF3EC")
ROWALT = colors.HexColor("#F6F7F9")

W, H = A4
M = 18 * mm

ss = {
    "h1": ParagraphStyle("h1", fontName="Cond-Bold", fontSize=22, leading=26, textColor=INK, spaceAfter=4),
    "kicker": ParagraphStyle("k", fontName="Sans-Bold", fontSize=8, leading=10, textColor=EMBER, spaceAfter=2),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=12.5, leading=16, textColor=INK, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="Sans", fontSize=9.4, leading=14, textColor=TEXT, spaceAfter=6),
    "bul": ParagraphStyle("bul", fontName="Sans", fontSize=9.4, leading=14, textColor=TEXT, leftIndent=12, bulletIndent=2, bulletFontName="Sans-Bold", bulletColor=EMBER, spaceAfter=2),
    "cell": ParagraphStyle("c", fontName="Sans", fontSize=8, leading=10.5, textColor=TEXT),
    "cellb": ParagraphStyle("cb", fontName="Sans-Bold", fontSize=8, leading=10.5, textColor=TEXT),
    "head": ParagraphStyle("hd", fontName="Sans-Bold", fontSize=8, leading=10.5, textColor=colors.white),
    "call": ParagraphStyle("call", fontName="Sans", fontSize=10, leading=15, textColor=INK),
    "small": ParagraphStyle("s", fontName="Sans", fontSize=7.5, leading=10, textColor=MUTED),
}

def P(t, s="body"): return Paragraph(t, ss[s])
def B(items): return [Paragraph(i, ss["bul"], bulletText="▸") for i in items]

def section(kicker, title):
    return [P(kicker.upper(), "kicker"), P(title, "h1"),
            Table([[""]], colWidths=[28*mm], rowHeights=[2.2], hAlign="LEFT",
                  style=[("BACKGROUND", (0,0), (-1,-1), EMBER)]), Spacer(1, 8)]

def T(rows, widths, bold_first=False, total=False):
    data = []
    for i, r in enumerate(rows):
        if i == 0:
            data.append([Paragraph(c, ss["head"]) for c in r])
        else:
            data.append([Paragraph(c, ss["cellb"] if (bold_first and j == 0) else ss["cell"]) for j, c in enumerate(r)])
    tw = W - 2*M
    cw = [tw * w for w in widths]
    t = Table(data, colWidths=cw, repeatRows=1)
    st = [("BACKGROUND", (0,0), (-1,0), STEEL),
          ("VALIGN", (0,0), (-1,-1), "TOP"),
          ("TOPPADDING", (0,0), (-1,-1), 4.5), ("BOTTOMPADDING", (0,0), (-1,-1), 4.5),
          ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5),
          ("LINEBELOW", (0,0), (-1,-1), 0.4, RULE)]
    for i in range(1, len(data)):
        if i % 2 == 0: st.append(("BACKGROUND", (0,i), (-1,i), ROWALT))
    if total:
        st += [("BACKGROUND", (0,len(data)-1), (-1,len(data)-1), TINT),
               ("LINEABOVE", (0,len(data)-1), (-1,len(data)-1), 1, EMBER)]
    t.setStyle(TableStyle(st))
    return [t, Spacer(1, 8)]

def callout(text):
    t = Table([[Paragraph(text, ss["call"])]], colWidths=[W-2*M])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), TINT),
                           ("LINEBEFORE", (0,0), (0,-1), 3, EMBER),
                           ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 10),
                           ("TOPPADDING", (0,0), (-1,-1), 9), ("BOTTOMPADDING", (0,0), (-1,-1), 9)]))
    return [t, Spacer(1, 10)]

# ---------- page decorations ----------
def cover(c, d):
    c.saveState()
    c.setFillColor(INK); c.rect(0, 0, W, H, fill=1, stroke=0)
    # orbital arcs
    c.setStrokeColor(colors.HexColor("#2A2E36")); c.setLineWidth(0.8)
    for r in (120, 170, 220, 270, 320):
        c.circle(W - 40*mm, H - 60*mm, r, fill=0, stroke=1)
    c.setFillColor(EMBER); c.circle(W - 40*mm, H - 60*mm, 46, fill=1, stroke=0)
    c.setFillColor(INK); c.circle(W - 40*mm + 10, H - 60*mm + 8, 40, fill=1, stroke=0)
    c.setFillColor(GOLD)
    for (dx, dy) in [(-150, 90), (60, -210), (-260, -80), (200, 40)]:
        c.circle(W - 40*mm + dx, H - 60*mm + dy, 3.2, fill=1, stroke=0)
    c.setFillColor(EMBER); c.rect(M, 120*mm, 34*mm, 2.4, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Cond-Bold", 50)
    c.drawString(M, 98*mm, "FORGE STAR")
    c.setFillColor(colors.HexColor("#C9CCD2")); c.setFont("Sans", 13)
    c.drawString(M, 86*mm, COVER["subtitle"])
    c.setFont("Sans", 9.5); c.setFillColor(colors.HexColor("#8A8F98"))
    c.drawString(M, 74*mm, COVER["tagline"])
    c.setFillColor(EMBER); c.setFont("Sans-Bold", 8)
    c.drawString(M, 30*mm, "MYFORGE PTY LTD  ·  FORGE ECOSYSTEM")
    c.setFillColor(colors.HexColor("#8A8F98")); c.setFont("Sans", 8)
    c.drawString(M, 24*mm, COVER["label"])
    c.restoreState()

def page(c, d):
    c.saveState()
    c.setFillColor(INK); c.rect(0, H - 11*mm, W, 11*mm, fill=1, stroke=0)
    c.setFillColor(EMBER); c.rect(0, H - 11*mm, 4*mm, 11*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Cond-Bold", 9)
    c.drawString(M, H - 7*mm, "FORGE STAR")
    c.setFillColor(colors.HexColor("#8A8F98")); c.setFont("Sans", 7.5)
    c.drawRightString(W - M, H - 7*mm, COVER["header"])
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 13*mm, W - M, 13*mm)
    c.setFillColor(MUTED); c.setFont("Sans", 7)
    c.drawString(M, 9*mm, "MYFORGE PTY LTD  ·  Confidential")
    c.setFillColor(EMBER); c.setFont("Sans-Bold", 7.5)
    c.drawRightString(W - M, 9*mm, f"{d.page:02d}")
    c.restoreState()

import argparse
_ap = argparse.ArgumentParser(description="Render a FORGE STAR markdown document to the FORGE-style PDF")
_ap.add_argument("--src", default="docs/strategy.md")
_ap.add_argument("--out", default="output/FORGE_STAR_Strategy.pdf")
_ap.add_argument("--subtitle", default="Africa's sovereign satellite data network")
_ap.add_argument("--tagline", default="Business model  ·  Build strategy  ·  Stages  ·  Capital  ·  Potential")
_ap.add_argument("--label", default="Strategy document  ·  October 2026  ·  Confidential")
_ap.add_argument("--header", default="Sovereign satellite data for Africa")
_ap.add_argument("--title", default="FORGE STAR — Strategy Document")
ARGS = _ap.parse_args()
COVER = {"subtitle": ARGS.subtitle, "tagline": ARGS.tagline, "label": ARGS.label, "header": ARGS.header}
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ARGS.src
OUT_FILE = ROOT / ARGS.out
OUT_FILE.parent.mkdir(exist_ok=True)
OUT = OUT_FILE.parent
doc = BaseDocTemplate(str(OUT_FILE), pagesize=A4,
                      leftMargin=M, rightMargin=M, topMargin=20*mm, bottomMargin=18*mm,
                      title=ARGS.title, author="MYFORGE PTY LTD")
fr = Frame(M, 18*mm, W - 2*M, H - 38*mm, id="f")
doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=cover),
                      PageTemplate("main", frames=[fr], onPage=page)])


# ---------- figures ----------
from reportlab.platypus import Image as RLImage
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

ss["reader"] = ParagraphStyle("rd", fontName="Sans-Bold", fontSize=7.6, leading=10, textColor=GOLD, spaceAfter=6)
ss["caption"] = ParagraphStyle("cap", fontName="Sans", fontSize=7.4, leading=9.5, textColor=MUTED, spaceAfter=8)


def image(path, caption):
    from reportlab.lib.utils import ImageReader
    full = ROOT / path
    iw, ih = ImageReader(str(full)).getSize()
    w = W - 2*M
    h = w * ih / iw
    if h > 95*mm:
        h = 95*mm; w = h * iw / ih
    out = [RLImage(str(full), width=w, height=h)]
    if caption:
        out.append(P(inline(caption), "caption"))
    return out


def _box(d, x, y, w, h, title, sub, fill):
    d.add(Rect(x, y, w, h, rx=4, ry=4, fillColor=fill, strokeColor=STEEL, strokeWidth=0.6))
    d.add(String(x + w / 2, y + h - 13, title, fontName="Sans-Bold", fontSize=8, fillColor=INK, textAnchor="middle"))
    for k, line in enumerate(sub):
        d.add(String(x + w / 2, y + h - 25 - 9 * k, line, fontName="Sans", fontSize=6.4, fillColor=TEXT, textAnchor="middle"))


def _arrow(d, x1, y1, x2, y2, label="", dashed=False, color=None):
    color = color or STEEL
    ln = Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=1)
    if dashed:
        ln.strokeDashArray = [3, 2]
    d.add(ln)
    import math
    a = math.atan2(y2 - y1, x2 - x1); s_ = 5
    d.add(Polygon([x2, y2, x2 - s_ * math.cos(a - 0.4), y2 - s_ * math.sin(a - 0.4),
                   x2 - s_ * math.cos(a + 0.4), y2 - s_ * math.sin(a + 0.4)], fillColor=color, strokeColor=color))
    if label:
        d.add(String((x1 + x2) / 2, (y1 + y2) / 2 + 4, label, fontName="Sans", fontSize=6, fillColor=MUTED, textAnchor="middle"))


def diagram(name):
    w = W - 2*M
    if name == "architecture":
        d = Drawing(w, 215)
        lt, sat, gnd, cust = colors.HexColor("#F6F7F9"), colors.HexColor("#FFF3EC"), colors.HexColor("#EEF3FB"), colors.HexColor("#EFF8F1")
        gap = 40
        bw = (w - 3 * gap) / 4
        xs = [k * (bw + gap) for k in range(4)]
        top, bh = 128, 66
        _box(d, xs[0], top, bw, bh, "Field devices", ["pumps · sensors · collars", "vessels · trackers", "device SDK (C)"], lt)
        _box(d, xs[1], top, bw, bh, "Satellites", ["F´ flight software", "store-and-forward", "secured commands"], sat)
        _box(d, xs[2], top, bw, bh, "Gateways", ["SA ×2 + 4 partners", "modem · RS + conv FEC", "dedupe · ACK uplink"], gnd)
        _box(d, xs[3], top, bw, bh, "Data platform (SA)", ["Kafka → TimescaleDB", "billing · retention", "POPIA · backups"], gnd)
        _box(d, xs[3], 22, bw, 70, "Customers", ["ThingsBoard dashboards", "API: devices · SLA", "usage · invoices"], cust)
        _box(d, xs[1], 22, 2 * bw + gap, 54, "Operations", ["mission ops tool · pass predictor · safe mode", "readiness · verification · CI"], lt)
        _box(d, xs[0], 22, bw, 54, "Resale partner", ["Stage 0 traffic", "before our satellites"], lt)
        y1, y2 = top + 46, top + 22
        _arrow(d, xs[0] + bw + 2, y1, xs[1] - 2, y1, "NB-IoT")
        _arrow(d, xs[1] + bw + 2, y1, xs[2] - 2, y1, "X-band")
        _arrow(d, xs[2] + bw + 2, y1, xs[3] - 2, y1, "Kafka")
        _arrow(d, xs[2] - 2, y2, xs[1] + bw + 2, y2, "ACKs", color=EMBER)
        _arrow(d, xs[1] - 2, y2, xs[0] + bw + 2, y2, "ACKs", dashed=True, color=EMBER)
        _arrow(d, xs[3] + bw / 2, top - 2, xs[3] + bw / 2, 94)
        _arrow(d, xs[1] + bw / 2, 78, xs[1] + bw / 2, top - 2, "commands")
        ln = Line(xs[0] + bw / 2, 22, xs[0] + bw / 2, 10, strokeColor=STEEL, strokeWidth=1); ln.strokeDashArray = [3, 2]; d.add(ln)
        ln = Line(xs[0] + bw / 2, 10, xs[3] + bw / 2, 10, strokeColor=STEEL, strokeWidth=1); ln.strokeDashArray = [3, 2]; d.add(ln)
        _arrow(d, xs[3] + bw / 2, 10, xs[3] + bw / 2, 20, dashed=True)
        d.add(String(xs[1] + bw, 2, "Stage 0: partner network traffic reaches the same platform", fontName="Sans", fontSize=6,
                     fillColor=MUTED, textAnchor="middle"))
        return [d, Spacer(1, 4),
                P("Orange: acknowledgements (ground → satellites → devices, so devices stop re-sending). "
                  "Dashed: Stage 0 resale traffic, before our satellites fly.", "caption")]
    raise ValueError(f"unknown diagram {name}")


# ---------- markdown → flowables ----------
# Supported syntax (keep strategy.md within it):
#   ## NN · Kicker      section start (new page) — next line "### Title" is the section title
#   #### Heading        sub-heading
#   > text              callout box (top-of-file tagline is skipped)
#   - item              bullet
#   | a | b |           table (first row header; a "**Total**" first cell styles the last row)
#   *text*              whole-paragraph italics → small muted note
#   **bold**, *italic*, `code`  inline
#   ---                 ignored (section breaks are implicit)
#   @reader text        "who this section is for" tag under a section title
#   ![caption](path)    image (path relative to the repo root)
#   <!-- diagram:name -->  vector diagram drawn by diagram()

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font name="Mono" size="7.6">\1</font>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    return t

def col_widths(rows):
    """Each column gets at least the measured width of its longest word (+padding);
    the rest of the page width is shared by text length."""
    plain = [[re.sub(r"<[^>]+>|\*", "", c) for c in r] for r in rows]
    n, tw = len(rows[0]), W - 2*M
    mins, weights = [], []
    for j in range(n):
        col = [r[j] for r in plain if j < len(r)]
        word_w = max((pdfmetrics.stringWidth(x, "Sans-Bold", 8) for c in col for x in c.split()), default=20)
        mins.append(word_w + 12)
        weights.append(min(max(len(c) for c in col), 70) + 4)
    spare = max(tw - sum(mins), 0)
    widths = [mn + spare * wt / sum(weights) for mn, wt in zip(mins, weights)]
    return [x / sum(widths) for x in widths]

def table(rows):
    rows = [[inline(c) for c in r] for r in rows]
    first_bold = all(r[0].startswith("<b>") or r[0] == "" for r in rows[1:])
    rows = [rows[0]] + [[re.sub(r"^<b>(.*)</b>$", r"\1", r[0]) if first_bold else r[0]] + r[1:] for r in rows[1:]]
    total = rows[-1][0].lower().startswith("<b>total") or rows[-1][0].lower() == "total"
    return T(rows, col_widths(rows), bold_first=first_bold, total=total)

def parse(md):
    lines = md.splitlines()
    out, para, items, rows = [], [], [], []
    first_section = True
    def flush():
        nonlocal para, items, rows
        if para:
            txt = " ".join(para).strip()
            m = re.fullmatch(r"\*(.+)\*", txt)
            out.append(P(inline(m.group(1)), "small") if m and "**" not in txt else P(inline(txt)))
            if m: out.append(Spacer(1, 6))
        if items: out.extend(B([inline(i) for i in items]))
        if rows: out.extend(table(rows))
        para, items, rows = [], [], []
    i = 0
    seen_section = False
    while i < len(lines):
        ln = lines[i].rstrip(); st = ln.strip()
        if st.startswith("|"):
            if para or items: flush()
            cells = [c.strip() for c in st.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells): rows.append(cells)
        elif rows: flush(); continue
        elif st.startswith("<!-- diagram:"):
            flush(); out.extend(diagram(st[len("<!-- diagram:"):].rstrip("->").strip()))
        elif re.fullmatch(r"!\[[^\]]*\]\([^)]+\)", st):
            flush(); m = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", st); out.extend(image(m.group(2), m.group(1)))
        elif st.startswith("@reader "):
            flush(); out.append(P("FOR: " + inline(st[8:].strip()).upper(), "reader"))
        elif st.startswith("## "):
            flush()
            kicker = st[3:].strip()
            title = ""
            if i + 1 < len(lines) and lines[i+1].startswith("### "):
                title = lines[i+1][4:].strip(); i += 1
            if not first_section: out.append(PageBreak())
            first_section = False; seen_section = True
            out.extend(section(kicker, inline(title)))
        elif st.startswith("#### ") or st.startswith("### "):
            flush(); out.append(P(inline(st.lstrip("#").strip()), "h2"))
        elif st.startswith("# "):
            flush()
        elif st.startswith(">"):
            flush()
            if seen_section: out.extend(callout(inline(st.lstrip("> ").strip())))
        elif st.startswith("- "):
            if para or rows: flush()
            items.append(st[2:])
        elif st in ("", "---"):
            flush()
        elif not seen_section:
            pass  # preamble (title, disclaimer) lives on the cover
        else:
            if items: flush()
            para.append(st)
        i += 1
    flush()
    return out

s = [NextPageTemplate("main"), PageBreak()] + parse(SRC.read_text(encoding="utf-8"))
doc.build(s)
print(f"ok: {OUT_FILE} from {SRC.name}")
