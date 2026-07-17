#!/usr/bin/env python3
"""Paradiem / FCI Market Commentary PDF — 2026-07-17"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate,
                                Paragraph, Spacer, NextPageTemplate, KeepTogether)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.flowables import HRFlowable, Flowable
import os, glob

INK      = HexColor("#1A1A1A")
MGRAY    = HexColor("#8A8A84")
LRULE    = HexColor("#BCBCB4")
DG       = HexColor("#2D3A1E")
CLR_DIV  = HexColor("#8C6239")
CLR_GRW  = HexColor("#5A7A3A")
CLR_DIG  = HexColor("#C47A2A")
CLR_HL   = HexColor("#5A7A3A")

W, H = letter
M = 0.65 * inch
GUTTER = 0.24 * inch
COL_W = (W - 2*M - GUTTER) / 2
PAGE1_TOP = 0.78 * inch
LATER_TOP = 0.88 * inch
LOGO = "/tmp/iown_logo.png"
LOGO_AR = 820/225  # Paradiem logo aspect

# ═══ DAY CONFIG ═══
DATE_STR = "JULY 17, 2026"
DATE_DOW = "FRIDAY"
HEADLINE = "Rotation,<br/>Not Retreat"
SUBHEAD = ("S&amp;P \u22121.01% as the semiconductor complex slid into bear-market territory on a new "
           "Chinese AI model and fresh capital-spending doubts \u2014 but energy and defensives absorbed the "
           "capital. The two sleeves split by design: Dividend Strategy \u22120.55%, Growth Portfolio \u22121.09%.")
MARKET_UP = False
CLR_HEAD = CLR_GRW if MARKET_UP else HexColor("#8B3A3A")
out = "/mnt/user-data/outputs/Paradiem_FCI_Market_Commentary_2026-07-17.pdf"
# ══════════════════

def find(p):
    for d in ["/usr/share/fonts", "/usr/local/share/fonts"]:
        for f in glob.glob(os.path.join(d, "**", p), recursive=True): return f
    return None

for name, pat in [("LS","LiberationSerif-Regular.ttf"),("LSB","LiberationSerif-Bold.ttf"),
    ("LSI","LiberationSerif-Italic.ttf"),("LSBI","LiberationSerif-BoldItalic.ttf"),("DVB","DejaVuSerif-Bold.ttf")]:
    f = find(pat)
    if f: pdfmetrics.registerFont(TTFont(name, f))

BF="LS"; BB="LSB"; BI="LSI"; BBI="LSBI"; DF="DVB"

body = ParagraphStyle("body", fontName=BF, fontSize=9, leading=13.5, textColor=INK, alignment=TA_JUSTIFY, spaceAfter=7)
lead = ParagraphStyle("lead", parent=body, fontName=BB)
pull = ParagraphStyle("pull", fontName=BBI, fontSize=9, leading=13, textColor=INK, spaceAfter=7, spaceBefore=4)

class SectionHeader(Flowable):
    def __init__(s, text):
        Flowable.__init__(s); s.text = text.upper(); s.height = 24
    def wrap(s, aw, ah): s.width = aw; return s.width, s.height
    def draw(s):
        c = s.canv
        c.setFont("Helvetica-Bold", 10.5); c.setFillColor(INK)
        c.drawString(0, 8, s.text)
        c.setStrokeColor(INK); c.setLineWidth(1); c.line(0, 4, s.width, 4)

class PerfDashboard(Flowable):
    def __init__(s, width, div_pct, div_beat, dvy, spy, grw_pct, grw_beat, iusg,
                 div_ytd, dvy_ytd, spy_ytd, grw_ytd, iusg_ytd):
        Flowable.__init__(s); s._width = width; s.height = 178
        s.div_pct=div_pct; s.div_beat=div_beat; s.dvy=dvy; s.spy=spy
        s.grw_pct=grw_pct; s.grw_beat=grw_beat; s.iusg=iusg
        s.div_ytd=div_ytd; s.dvy_ytd=dvy_ytd; s.spy_ytd=spy_ytd
        s.grw_ytd=grw_ytd; s.iusg_ytd=iusg_ytd
    def wrap(s, aw, ah): s._width = min(s._width, aw); return s._width, s.height
    def draw(s):
        c = s.canv; cw = s._width; ch = 58
        y1 = s.height - ch
        c.setFillColor(HexColor("#F7F6F1")); c.roundRect(0, y1, cw, ch, 3, fill=1, stroke=0)
        c.setFillColor(CLR_DIV); c.rect(0, y1, 3, ch, fill=1, stroke=0)
        c.setFont("Helvetica", 6.5); c.setFillColor(MGRAY); c.drawString(10, y1+ch-13, "DIVIDEND STRATEGY")
        bt = "\u2713 BEAT BOTH" if s.div_beat==2 else ("\u2713 BEAT ONE" if s.div_beat==1 else "\u2717 TRAIL")
        c.setFont("Helvetica-Bold", 6.5); c.setFillColor(CLR_DIV); c.drawRightString(cw-8, y1+ch-13, bt)
        c.setFont("Helvetica-Bold", 17); c.setFillColor(INK); c.drawString(10, y1+ch-33, s.div_pct)
        c.setFont("Helvetica", 7); c.setFillColor(HexColor("#666660")); c.drawString(10, y1+8, f"vs. DVY {s.dvy}  |  SPY {s.spy}")
        y2 = y1 - ch - 6
        c.setFillColor(HexColor("#F7F6F1")); c.roundRect(0, y2, cw, ch, 3, fill=1, stroke=0)
        c.setFillColor(CLR_GRW); c.rect(0, y2, 3, ch, fill=1, stroke=0)
        c.setFont("Helvetica", 6.5); c.setFillColor(MGRAY); c.drawString(10, y2+ch-13, "GROWTH PORTFOLIO")
        bt2 = "\u2713 BEAT" if s.grw_beat else "\u2717 TRAIL"
        c.setFont("Helvetica-Bold", 6.5); c.setFillColor(CLR_GRW); c.drawRightString(cw-8, y2+ch-13, bt2)
        c.setFont("Helvetica-Bold", 17); c.setFillColor(INK); c.drawString(10, y2+ch-33, s.grw_pct)
        c.setFont("Helvetica", 7); c.setFillColor(HexColor("#666660")); c.drawString(10, y2+8, f"vs. IUSG {s.iusg}")
        y3 = y2 - 46
        c.setFillColor(DG); c.roundRect(0, y3, cw, 40, 3, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 6.5); c.setFillColor(white); c.drawString(8, y3+28, "YEAR-TO-DATE")
        c.setFont("Helvetica", 7.5); c.setFillColor(HexColor("#D4E5C0"))
        c.drawString(8, y3+16, f"Dividend {s.div_ytd}  vs  DVY {s.dvy_ytd}  /  SPY {s.spy_ytd}")
        c.drawString(8, y3+5, f"Growth {s.grw_ytd}  vs  IUSG {s.iusg_ytd}")

class MoversEntry(Flowable):
    def __init__(s, ticker, pct, strategy, catalyst, width=None, is_winner=True):
        Flowable.__init__(s); s.ticker=ticker; s.pct=pct; s.strategy=strategy
        s.catalyst=catalyst; s._width=width or 200; s.is_winner=is_winner; s.height=0
    def wrap(s, aw, ah):
        s._width = min(s._width, aw)
        sty = ParagraphStyle("mc", fontName=BF, fontSize=8.5, leading=11.5, textColor=HexColor("#444440"), alignment=TA_JUSTIFY)
        s._para = Paragraph(s.catalyst, sty)
        pw, ph = s._para.wrap(s._width - 8, ah); s.height = ph + 18; return s._width, s.height
    def draw(s):
        c = s.canv; yt = s.height - 10
        c.setFont("Helvetica-Bold", 9); c.setFillColor(INK); c.drawString(0, yt, s.ticker)
        pc = CLR_GRW if s.is_winner else HexColor("#A04030")
        c.setFillColor(pc); tw = c.stringWidth(s.ticker, "Helvetica-Bold", 9); c.drawString(tw+6, yt, s.pct)
        tm = {"Dividend Strategy": CLR_DIV, "Growth Portfolio": CLR_GRW, "Digital Asset ETF": CLR_DIG}
        c.setFont("Helvetica", 6); c.setFillColor(tm.get(s.strategy, CLR_GRW))
        c.drawRightString(s._width, yt+1, s.strategy.upper())
        c.setStrokeColor(HexColor("#E8E6DE")); c.setLineWidth(0.3); c.line(0, yt-4, s._width, yt-4)
        s._para.drawOn(c, 0, 0)

def page1_bg(canvas, doc):
    c = canvas
    lh = 0.42*inch; lw = lh*LOGO_AR
    c.drawImage(LOGO, M, H-0.16*inch-lh, width=lw, height=lh, mask='auto')
    c.setFont("Helvetica", 8); c.setFillColor(MGRAY)
    c.drawRightString(W-M, H-0.28*inch, f"{DATE_STR}  |  {DATE_DOW}")
    c.setFont("Helvetica", 7.5)
    c.drawRightString(W-M, H-0.40*inch, "INVESTMENT COMMITTEE")
    yr = H-0.58*inch
    c.setStrokeColor(INK); c.setLineWidth(2); c.line(M, yr, W-M, yr)
    c.setLineWidth(0.5); c.line(M, yr-4, W-M, yr-4)
    cx = M+COL_W+GUTTER/2; c.setStrokeColor(LRULE); c.setLineWidth(0.4)
    c.line(cx, M+0.3*inch, cx, H-PAGE1_TOP)
    _footer(c)

def later_bg(canvas, doc):
    c = canvas
    lh2 = 0.24*inch; lw2 = lh2*LOGO_AR
    c.drawImage(LOGO, M, H-0.52*inch, width=lw2, height=lh2, mask='auto')
    c.setFont("Helvetica", 6.5); c.setFillColor(MGRAY)
    c.drawRightString(W-M, H-0.44*inch, f"PARADIEM FCI MARKET COMMENTARY  \u2022  {DATE_STR}  \u2022  INVESTMENT COMMITTEE")
    c.setStrokeColor(INK); c.setLineWidth(0.75); c.line(M, H-0.60*inch, W-M, H-0.60*inch)
    cx = M+COL_W+GUTTER/2; c.setStrokeColor(LRULE); c.setLineWidth(0.4)
    c.line(cx, M+0.3*inch, cx, H-LATER_TOP)
    _footer(c)

def _footer(c):
    y = M-0.08*inch
    c.setStrokeColor(LRULE); c.setLineWidth(0.5); c.line(M, y+12, W-M, y+12)
    c.setFont("Helvetica", 6); c.setFillColor(MGRAY)
    c.drawString(M, y, "CONFIDENTIAL  |  Family Capital Investments (FCI)  |  RIA  |  Paradiem")
    c.drawRightString(W-M, y, str(c.getPageNumber()))

f1l = Frame(M, M+0.2*inch, COL_W, H-PAGE1_TOP-M-0.2*inch, id="p1l")
f1r = Frame(M+COL_W+GUTTER, M+0.2*inch, COL_W, H-PAGE1_TOP-M-0.2*inch, id="p1r")
fLl = Frame(M, M+0.2*inch, COL_W, H-LATER_TOP-M-0.2*inch, id="pLl")
fLr = Frame(M+COL_W+GUTTER, M+0.2*inch, COL_W, H-LATER_TOP-M-0.2*inch, id="pLr")
doc = BaseDocTemplate(out, pagesize=letter, leftMargin=M, rightMargin=M, topMargin=PAGE1_TOP, bottomMargin=M)
doc.addPageTemplates([PageTemplate(id="first", frames=[f1l, f1r], onPage=page1_bg),
                      PageTemplate(id="later", frames=[fLl, fLr], onPage=later_bg)])

S = []
hl = ParagraphStyle("hl", fontName=DF, fontSize=42, leading=46, textColor=CLR_HEAD, spaceAfter=2)
sub = ParagraphStyle("sub", fontName=BI, fontSize=10.5, leading=14, textColor=INK, spaceAfter=8)
S.append(Paragraph(HEADLINE, hl))
S.append(Paragraph(SUBHEAD, sub))
S.append(NextPageTemplate("later"))

# ═══ THE SESSION ═══
S.append(SectionHeader("THE SESSION"))
S.append(Paragraph(
    "<b>The week&#8217;s chip anxiety resolved on Friday into a genuine rotation rather than a retreat.</b> "
    "The S&amp;P 500 closed \u22121.01% at 7,457.78 and the Nasdaq \u22121.44%, yet beneath the index the "
    "money did not leave the market so much as change addresses. Semiconductors did the damage; energy, "
    "utilities, insurers and staples caught the bid. The Dow held better at \u22120.77%, and the VIX rose "
    "roughly 10% to 18.4 \u2014 elevated, but well short of panic.", lead))
S.append(Paragraph(
    "The fresh catalyst crystallized a question the tape has been circling all week. Chinese startup "
    "Moonshot released Kimi K3, a powerful open model competitive with leading U.S. systems, and the "
    "market read it not as a demand story but as a cost one: if capable models can be built for less, "
    "the return on the industry&#8217;s enormous AI capital-spending plans becomes the debate. That reframing, "
    "layered on the week&#8217;s earlier reaction to a record TSMC quarter, pushed the semiconductor complex "
    "into bear-market territory \u2014 down roughly 20% from its peak, per Bloomberg. Nvidia slipped about "
    "2% and briefly ceded the world&#8217;s-most-valuable-company title to Apple intraday. Netflix, which we "
    "do not own, added to the mood with a near 11% drop on soft third-quarter guidance.", body))
S.append(Paragraph(
    "The other side of that trade belonged in part to us. Renewed U.S.\u2013Iran hostilities and fresh Strait "
    "of Hormuz tension lifted Brent \u2014 up roughly 16% from its July 1 low \u2014 and energy has been the "
    "strongest sector of the past week. Chevron (+1.91%) and Vistra (+1.89%) led the Growth Portfolio&#8217;s "
    "gainers even as the sleeve&#8217;s semiconductor and digital-asset weighting absorbed the day&#8217;s pressure, "
    "closing \u22121.09% against IUSG&#8217;s \u22121.34%. The Dividend Strategy \u2014 anchored in healthcare, "
    "staples, financials and insurance \u2014 nearly held flat at \u22120.55%, edging past SPY (\u22121.01%) "
    "while trailing a resilient DVY (\u22120.39%).", body))
S.append(Paragraph(
    "<i>FCI Tactical: A bear market in one sector is not a bear market in a portfolio. Owning durable cash "
    "flows alongside secular growth is precisely what lets a \u22121% tape land as \u22120.55% in the sleeve "
    "built to defend it. We own businesses, not the ticker \u2014 and a rotation that pays our value names "
    "while our growth names catch their breath is the barbell working as designed. The tactical framework "
    "operates at the index level, and the S&amp;P remains far above the \u221220% first-tranche trigger.</i>", pull))

# ═══ NOTABLE MOVERS ═══
S.append(SectionHeader("FCI HOLDINGS: NOTABLE MOVERS"))
S.append(Paragraph("<font color='#5A7A3A'><b>WINNERS</b></font>",
    ParagraphStyle("wh", fontName="Helvetica-Bold", fontSize=7, textColor=CLR_GRW, spaceAfter=4)))
for t,p,st,cat in [
    ("CVX","+1.91%","Growth Portfolio","Chevron led the energy bid as renewed U.S.\u2013Iran hostilities and Strait of Hormuz tension lifted crude, with the company moving to insulate its operations from Iran-related supply risk."),
    ("VST","+1.89%","Growth Portfolio","Vistra advanced as capital rotated toward power and hard assets, the independent power producer drawing both the energy bid and steady electricity-demand flows."),
    ("ABT","+1.87%","Dividend Strategy","Abbott extended Thursday&#8217;s post-earnings strength as healthcare remained the market&#8217;s preferred defensive following its Q2 beat and raised full-year guide."),
    ("ORI","+1.83%","Dividend Strategy","Old Republic gained as insurers and value financials drew defensive flows leaving high-beta technology."),
    ("KEYS","+1.00%","Growth Portfolio","Keysight held green as test-and-measurement stayed relatively insulated from the AI-hardware de-rating."),
    ("QCOM","+0.69%","Dividend Strategy","Qualcomm bucked the semiconductor selling, its handset-and-licensing profile shielding it from the AI capital-spending doubts pressuring the data-center names."),
]: S.append(MoversEntry(t,p,st,cat,COL_W,is_winner=True))

S.append(Spacer(1,4))
S.append(Paragraph("<font color='#A04030'><b>DECLINERS</b></font>",
    ParagraphStyle("lh", fontName="Helvetica-Bold", fontSize=7, textColor=HexColor("#A04030"), spaceAfter=4)))
for t,p,st,cat in [
    ("MARA","\u22126.39%","Growth Portfolio","Marathon led the miners lower in a high-beta de-risking driven by rotation rather than bitcoin, which held near $64,000."),
    ("HOOD","\u22125.72%","Growth Portfolio","Robinhood fell on profit-taking after roughly a 10% monthly run \u2014 no company-specific shock, but a stretched high-beta name meeting a broad de-risking bid, with ARK trimming and a reported credit-card-backed bond sale in the frame."),
    ("SYK","\u22123.42%","Dividend Strategy","Stryker gave back Thursday&#8217;s gain as medical-technology names saw profit-taking, even as it launched its Mako RPS robotic knee platform."),
    ("TOL","\u22123.24%","Growth Portfolio","Toll Brothers slid as rate-sensitive homebuilders came under pressure with Treasury yields held up by the oil-driven inflation impulse."),
    ("TSM","\u22122.77%","Growth Portfolio","Taiwan Semiconductor extended its post-earnings slide as the epicenter of the capex-absorption debate, the Kimi K3 launch sharpening competitive concerns."),
    ("CRDO","\u22122.54%","Growth Portfolio","Credo dropped with the AI-connectivity cohort as the semiconductor index moved into bear-market territory."),
    ("NVDA","\u22122.21%","Growth Portfolio","Nvidia slipped with the complex and briefly ceded the world&#8217;s-most-valuable-company title to Apple during the session."),
]: S.append(MoversEntry(t,p,st,cat,COL_W,is_winner=False))

# ═══ HOLDINGS NEWS ═══
S.append(SectionHeader("HOLDINGS NEWS"))
S.append(Paragraph(
    "<b>Lockheed Martin (LMT) \u2014 $10.5B special-operations logistics award.</b> The Department of War named "
    "Lockheed prime contractor on the Special Operations Forces Global Logistics Support Services II (GLSS2) "
    "program \u2014 a $10.5 billion, 12-year contract and USSOCOM&#8217;s largest service-contract vehicle, a "
    "competitive follow-on to work Lockheed has run since 2010. Separately, the company took a $1.6 billion "
    "Navy order for F-35 spares and committed $100 million to a European venture allocation alongside a new "
    "London office. Shares eased \u22120.93% with the broad tape despite the news.", body))
S.append(Paragraph(
    "<b>Stryker (SYK) \u2014 Mako RPS launch.</b> Stryker introduced Mako RPS, extending its flagship robotic-"
    "surgery platform further into knee procedures. The launch broadens the Mako franchise&#8217;s addressable "
    "base, though the stock traded lower with the medical-technology group on the day.", body))

# ═══ PORTFOLIO PERFORMANCE ═══
S.append(KeepTogether([SectionHeader("PORTFOLIO PERFORMANCE"), Spacer(1,4),
    PerfDashboard(COL_W, div_pct="\u22120.55%", div_beat=1, dvy="\u22120.39%", spy="\u22121.01%",
        grw_pct="\u22121.09%", grw_beat=True, iusg="\u22121.34%",
        div_ytd="+17.22%", dvy_ytd="+16.45%", spy_ytd="+9.58%",
        grw_ytd="+13.04%", iusg_ytd="+9.67%")]))

doc.build(S)
print(f"PDF saved: {out}")
print(f"Size: {os.path.getsize(out):,} bytes")
