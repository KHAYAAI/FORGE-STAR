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
            Table([[""]], colWidths=[28*mm], rowHeights=[2.2],
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
    c.drawString(M, 86*mm, "Africa's sovereign satellite data network")
    c.setFont("Sans", 9.5); c.setFillColor(colors.HexColor("#8A8F98"))
    c.drawString(M, 74*mm, "Business model  ·  Build strategy  ·  Stages  ·  Capital  ·  Potential")
    c.setFillColor(EMBER); c.setFont("Sans-Bold", 8)
    c.drawString(M, 30*mm, "MYFORGE PTY LTD  ·  FORGE ECOSYSTEM")
    c.setFillColor(colors.HexColor("#8A8F98")); c.setFont("Sans", 8)
    c.drawString(M, 24*mm, "Strategy document  ·  October 2026  ·  Confidential")
    c.restoreState()

def page(c, d):
    c.saveState()
    c.setFillColor(INK); c.rect(0, H - 11*mm, W, 11*mm, fill=1, stroke=0)
    c.setFillColor(EMBER); c.rect(0, H - 11*mm, 4*mm, 11*mm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Cond-Bold", 9)
    c.drawString(M, H - 7*mm, "FORGE STAR")
    c.setFillColor(colors.HexColor("#8A8F98")); c.setFont("Sans", 7.5)
    c.drawRightString(W - M, H - 7*mm, "Sovereign satellite data for Africa")
    c.setStrokeColor(RULE); c.setLineWidth(0.5); c.line(M, 13*mm, W - M, 13*mm)
    c.setFillColor(MUTED); c.setFont("Sans", 7)
    c.drawString(M, 9*mm, "MYFORGE PTY LTD  ·  Confidential")
    c.setFillColor(EMBER); c.setFont("Sans-Bold", 7.5)
    c.drawRightString(W - M, 9*mm, f"{d.page:02d}")
    c.restoreState()

OUT = Path(__file__).resolve().parent.parent / "output"
OUT.mkdir(exist_ok=True)
SRC = Path(__file__).resolve().parent.parent / "docs" / "strategy.md"
doc = BaseDocTemplate(str(OUT / "FORGE_STAR_Strategy.pdf"), pagesize=A4,
                      leftMargin=M, rightMargin=M, topMargin=20*mm, bottomMargin=18*mm,
                      title="FORGE STAR — Strategy Document", author="MYFORGE PTY LTD")
fr = Frame(M, 18*mm, W - 2*M, H - 38*mm, id="f")
doc.addPageTemplates([PageTemplate("cover", frames=[fr], onPage=cover),
                      PageTemplate("main", frames=[fr], onPage=page)])


# ---------- markdown → flowables ----------
# Supported syntax (keep strategy.md within it):
#   ## NN · Kicker      section start (new page) — next line "### Title" is the section title
#   #### Heading        sub-heading
#   > text              callout box (top-of-file tagline is skipped)
#   - item              bullet
#   | a | b |           table (first row header; a "**Total**" first cell styles the last row)
#   *text*              whole-paragraph italics → small muted note
#   **bold**, *italic*  inline
#   ---                 ignored (section breaks are implicit)

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
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
print(f"ok: {OUT / 'FORGE_STAR_Strategy.pdf'} from {SRC.name}")
