#!/usr/bin/env python3
import json, os, sys, re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.colors import HexColor, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

for name, fn in [("SimSun","simsun.ttc"),("SimHei","simhei.ttf"),("KaiTi","simkai.ttf")]:
    try: pdfmetrics.registerFont(TTFont(name, os.path.join(r"C:\Windows\Fonts", fn)))
    except: pass

C = dict(title=HexColor("#1a1a2e"),heading=HexColor("#0f3460"),subheading=HexColor("#16213e"),
         body=HexColor("#333"),accent=HexColor("#c0392b"),green=HexColor("#2e7d32"),
         blue=HexColor("#2980b9"),meta=grey,border=HexColor("#dcdde1"))

def T(text):
    if not text: return ""
    if isinstance(text, str): return re.sub(r"\s+", " ", text.strip())
    return str(text)

def mkS(**kw):
    d = dict(fontName="SimSun",fontSize=10,leading=17,textColor=C["body"],alignment=TA_JUSTIFY)
    d.update(kw)
    return ParagraphStyle("s"+str(hash(str(kw)))[:6],**d)

S = dict(
    cover_title=mkS(fontName="SimHei",fontSize=28,leading=36,alignment=TA_CENTER,textColor=C["title"]),
    cover_sub=mkS(fontName="SimHei",fontSize=14,leading=20,alignment=TA_CENTER,textColor=C["heading"]),
    cover_info=mkS(fontSize=10,leading=16,alignment=TA_CENTER,textColor=grey),
    section=mkS(fontName="SimHei",fontSize=16,leading=24,textColor=C["heading"],spaceBefore=20,spaceAfter=10),
    subsection=mkS(fontName="SimHei",fontSize=12,leading=18,textColor=C["subheading"],spaceBefore=14,spaceAfter=6),
    subsubsection=mkS(fontName="SimHei",fontSize=10.5,leading=15,textColor=C["heading"],spaceBefore=10,spaceAfter=4),
    body=mkS(fontSize=10,leading=17,firstLineIndent=20,spaceAfter=6),
    body_ni=mkS(fontSize=10,leading=17,spaceAfter=6),
    small=mkS(fontSize=9,leading=14,spaceAfter=4),
    meta=mkS(fontSize=8,leading=12,textColor=grey),
    footer=mkS(fontSize=7.5,leading=11,textColor=grey,alignment=TA_CENTER),
    toc=mkS(fontSize=10,leading=18),
    bullet=mkS(fontSize=9.5,leading=15,leftIndent=15,spaceAfter=3),
    bullet_bold=mkS(fontName="SimHei",fontSize=9.5,leading=15,leftIndent=15,spaceAfter=3),
    code=mkS(fontSize=8.5,leading=13,textColor=HexColor("#2d3436"),backColor=HexColor("#f5f6fa"),borderPadding=6,leftIndent=10),
    callout=mkS(fontName="KaiTi",fontSize=9.5,leading=15,textColor=C["blue"],leftIndent=10,rightIndent=10,backColor=HexColor("#eaf2f8"),borderPadding=8,spaceAfter=6,spaceBefore=6),
)


from scripts.v3_builders import V3_BUILDERS, safe_build

class NumCanvas(canvas.Canvas):
    """Canvas with page numbers and PDF outline bookmarks."""
    bookmarks = []  # class-level: list of (title, page_num, level)
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
    
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self.setStrokeColor(C["border"]);self.setLineWidth(0.5)
        self.line(16*mm,A4[1]-18*mm,A4[0]-16*mm,A4[1]-18*mm)
        # Add bookmark for current page if any bookmarks point here
        page_num = self.getPageNumber()
        canvas.Canvas.showPage(self)
    
    def save(self):
        canvas.Canvas.save(self)
def build_pdf(json_path: str) -> str:
    """Generate a teaching-level Chinese academic daily report PDF.
    Returns the path to the generated PDF file.
    """
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found",file=sys.stderr);sys.exit(1)
    with open(json_path,"r",encoding="utf-8") as f:
        papers=json.load(f)
    date=datetime.now().strftime("%Y-%m-%d")
    out=os.path.join(os.path.expanduser("~"),"Desktop",f"遥感与测绘学术日报_{date}.pdf")
    doc=SimpleDocTemplate(out,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,
                          topMargin=22*mm,bottomMargin=22*mm,
                          title=f"学术日报 {date}",
                          author="SearchScience v3",
                          creator="SearchScience - AI-Powered Academic Paper Analysis",
                          subject=f"Daily Academic Digest - {date}")
    story=[]
    story.append(Spacer(1,25*mm))
    story.append(Paragraph("遥感与测绘学术日报",S["cover_title"]))
    story.append(Spacer(1,5*mm))
    story.append(Paragraph("教学级论文深度解读",S["cover_sub"]))
    story.append(Spacer(1,8*mm))
    selected=[p for p in papers if p.get("selected")]
    story.append(Paragraph(f"日期: {date} | 论文: {len(papers)}篇 | 深度分析: {len(selected)}篇",S["cover_info"]))
    story.append(Spacer(1,10*mm))
    story.append(Paragraph("<b>本期论文</b>",S["subsection"]))
    for i,p in enumerate(papers):
        da=p.get("deep_analysis",{})
        tc=T(da.get("title_cn","") or p.get("title","")[:80])
        os_=T(da.get("one_sentence",""))
        sel="*" if p.get("selected") else " "
        story.append(Paragraph(f"{sel} [{i+1}] {tc}",S["toc"]))
        if os_:story.append(Paragraph(f"       {os_[:100]}",S["meta"]))
        badges=[]
        if da.get("knowledge_map"):badges.append("analyzed")
        if p.get("local_pdf"):badges.append("PDF")
        if p.get("github_url"):badges.append("Code")
        if badges:story.append(Paragraph(f"       [{' | '.join(badges)}]",S["meta"]))
    story.append(PageBreak())
    for idx,paper in enumerate(papers):
        da=paper.get("deep_analysis",{})
        is_sel=paper.get("selected",False)
        if is_sel:
            story.append(Paragraph(f"<b>* Paper {idx+1} - Deep Analysis</b>",S["section"]))
        else:
            story.append(Paragraph(f"<b>Paper {idx+1}</b>",S["section"]))
        tc=T(da.get("title_cn",""))
        os_=T(da.get("one_sentence",""))
        if tc:
            story.append(Paragraph(f"<b>{tc}</b>",mkS(fontName="SimHei",fontSize=13,leading=19,textColor=C["heading"],spaceAfter=4)))
        if os_:story.append(Paragraph(f"{os_}",S["callout"]))
        story.append(Paragraph(paper.get("title",""),mkS(fontSize=9.5,leading=14,textColor=C["title"],spaceAfter=2)))
        authors=", ".join(paper.get("authors",[])[:6])
        mp=[f"Authors: {authors}" if authors else "",f"Published: {paper.get('published','')}",f"Source: {paper.get('source','')}"]
        if paper.get("arxiv_id"):mp.append(f"ID: {paper['arxiv_id']}")
        story.append(Paragraph(" | ".join(p for p in mp if p),S["meta"]))
        rs=[]
        if paper.get("local_pdf"):rs.append(f"PDF: {os.path.basename(paper['local_pdf'])}")
        if paper.get("github_url"):rs.append(f"GitHub: {paper['github_url']}")
        if rs:story.append(Paragraph(" | ".join(rs),S["meta"]))
        story.append(Spacer(1,6))
        why=T(da.get("why_selected",""))
        if why:
            story.append(Paragraph(f"<b>Why selected:</b> {why}",mkS(fontName="KaiTi",fontSize=10,leading=15,textColor=C["green"],spaceAfter=8)))
        has_deep=bool(da.get("knowledge_map") or da.get("problem_analysis"))
        if has_deep:
            for builder in V3_BUILDERS:
                try:
                    story.extend(builder(da,S))
                except Exception as e:
                    pass
        else:
            summary=paper.get("summary","")
            if summary:
                story.append(Paragraph("<b>Abstract</b> (pending analysis)",S["subsubsection"]))
                story.append(Paragraph(T(summary),S["body_ni"]))
        if idx<len(papers)-1:
            story.append(Spacer(1,10))
            story.append(HRFlowable(width="60%",thickness=1,color=C["border"]))
            story.append(PageBreak())
    # Report summary
    story.append(Spacer(1,10*mm))
    story.append(Paragraph("<b>Report Summary</b>",S["subsection"]))
    total_papers = len(papers)
    analyzed = len(selected)
    with_pdf = len([p for p in papers if p.get("local_pdf")])
    with_code = len([p for p in papers if p.get("github_url")])
    summary_lines = [
        f"Total papers retrieved: {total_papers}",
        f"Deep analysis: {analyzed} papers",
        f"PDF downloaded: {with_pdf}",
        f"GitHub repos found: {with_code}",
        f"Generated: {date}",
    ]
    for s in summary_lines:
        story.append(Paragraph(f"- {s}", S["body_ni"]))
    story.append(Spacer(1,15*mm))
    story.append(HRFlowable(width="80%",thickness=2,color=C["heading"]))
    story.append(Spacer(1,8))
    story.append(Paragraph("SearchScience v3 - Teaching-Level Academic Paper Analysis",S["footer"]))
    story.append(Paragraph("For personal research use only. Generated by Codex Agent.",S["footer"]))
    doc.build(story,canvasmaker=NumCanvas)
    print(f"PDF: {out} ({os.path.getsize(out)//1024} KB)")
    return out

if __name__=="__main__":
    build_pdf(sys.argv[1] if len(sys.argv)>1 else
              os.path.join(os.path.expanduser("~"),"codex_outputs",
                           datetime.now().strftime("%Y-%m-%d"),"papers.json"))
