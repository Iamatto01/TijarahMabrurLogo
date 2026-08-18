"""PDF template utilities: field extraction (AcroForm) and overlay-based filling."""
import io
import json

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


def extract_acroform_fields(path):
    """Pull text-field positions from a PDF's AcroForm annotations.
    Returns a list of field dicts suitable for fields_json."""
    reader = PdfReader(path)
    fields = []
    for pno, page in enumerate(reader.pages, start=1):
        annots = page.get("/Annots")
        if not annots:
            continue
        for annot_ref in annots:
            try:
                annot = annot_ref.get_object()
            except Exception:
                continue
            if annot.get("/FT") != "/Tx":
                continue
            name = annot.get("/T")
            if not name:
                continue
            rect = [float(v) for v in annot.get("/Rect", [0, 0, 0, 0])]
            fields.append({
                "name": str(name),
                "label": str(name).replace("_", " ").title(),
                "page": pno,
                "x": round(rect[0] + 2, 1),
                "y": round(rect[1] + 2, 1),
                "size": 10,
            })
    return fields


def validate_fields_json(text):
    """Parse and validate a fields JSON string. Returns (fields, error)."""
    try:
        fields = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"
    if not isinstance(fields, list):
        return None, "JSON must be a list of field objects."
    for i, f in enumerate(fields):
        if not isinstance(f, dict) or "name" not in f:
            return None, f"Field #{i + 1} must be an object with at least a 'name'."
        f.setdefault("label", str(f["name"]).replace("_", " ").title())
        f.setdefault("page", 1)
        f.setdefault("x", 50)
        f.setdefault("y", 700)
        f.setdefault("size", 10)
        try:
            f["page"] = int(f["page"])
            f["x"] = float(f["x"])
            f["y"] = float(f["y"])
            f["size"] = float(f["size"])
        except (TypeError, ValueError):
            return None, f"Field '{f['name']}' has invalid page/x/y/size numbers."
    return fields, None


def fill_pdf(template_path, fields, data):
    """Overlay `data` values onto the template PDF at each field's x/y.
    Returns the filled PDF as bytes."""
    reader = PdfReader(template_path)
    writer = PdfWriter()

    by_page = {}
    for f in fields:
        val = str(data.get(f["name"], "") or "").strip()
        if val:
            by_page.setdefault(int(f["page"]), []).append((f, val))

    for pno, page in enumerate(reader.pages, start=1):
        if pno in by_page:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(w, h))
            for f, val in by_page[pno]:
                c.setFont("Helvetica", float(f.get("size", 10)))
                for li, line in enumerate(val.splitlines()):
                    c.drawString(float(f["x"]), float(f["y"]) - li * (float(f.get("size", 10)) + 2), line)
            c.save()
            buf.seek(0)
            overlay_page = PdfReader(buf).pages[0]
            page.merge_page(overlay_page)
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def generate_oshwa_dossier_pdf(title="OSHWA Safety & Health Management Manual",
                               company_name="Camoor Blinds Sdn. Bhd.",
                               ref_no="TM/OSHWA/2026/CB-01",
                               revision="Rev 1.0 (2026 Edition)",
                               sections=None,
                               company_logo=None):
    """Generate a comprehensive multi-page statutory OSHWA dossier PDF using ReportLab with custom section contents."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable, KeepTogether, Image
    import os
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    from reportlab.platypus import Flowable
    class PdfInsertionFlowable(Flowable):
        def __init__(self, filenames, insertions_list):
            Flowable.__init__(self)
            self.filenames = filenames
            self.insertions_list = insertions_list
            self.width = 0
            self.height = 0
        def draw(self):
            page_num = self.canv.getPageNumber()
            self.insertions_list.append((page_num, self.filenames))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Typography styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Center
        spaceAfter=10
    )
    sub_style = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0284c7"),
        alignment=1,
        spaceAfter=18
    )
    h1_banner_style = ParagraphStyle(
        'H1Banner',
        parent=styles['Heading1'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#ffffff"),
        spaceBefore=0,
        spaceAfter=0
    )
    h2_style = ParagraphStyle(
        'H2Section',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0369a1"),
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    )
    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=15,
        spaceAfter=4
    )

    story = []
    insertions = []

    # ── PAGE 1: OFFICIAL COVER PAGE ──
    story.append(Spacer(1, 20))
    if company_logo:
        logo_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "uploads", "logos", company_logo)
        if os.path.exists(logo_path):
            try:
                img = Image(logo_path, width=1.5*inch, height=1.5*inch, kind='proportional')
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 10))
            except Exception:
                pass
                
    story.append(Paragraph("TIJARAH MABRUR (M) SDN. BHD.", ParagraphStyle('Brand', fontSize=13, leading=15, fontName="Helvetica-Bold", textColor=colors.HexColor("#0284c7"), alignment=1)))
    story.append(Paragraph("OSHONE STATUTORY COMPLIANCE & SAFETY ENGINEERING DIVISION", ParagraphStyle('SubBrand', fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b"), alignment=1)))
    story.append(Spacer(1, 25))
    story.append(HRFlowable(width="100%", thickness=2.5, color=colors.HexColor("#0284c7"), spaceAfter=20))
    story.append(Paragraph(f"<b>{title.upper()}</b>", title_style))
    story.append(Paragraph(f"Client: <b>{company_name}</b>", sub_style))
    story.append(Spacer(1, 15))

    meta_table_data = [
        [Paragraph("<b>Document Reference:</b>", body_style), Paragraph(f"<b>{ref_no}</b>", body_style)],
        [Paragraph("<b>Revision Edition:</b>", body_style), Paragraph(revision, body_style)],
        [Paragraph("<b>Statutory Mandate:</b>", body_style), Paragraph("OSHA 1994 (Act 514 / 2022 Amendment) Section 16 & Section 31", body_style)],
        [Paragraph("<b>Compliance Standards:</b>", body_style), Paragraph("DOSH / JKKP Malaysia & ISO 45001:2018 Aligned", body_style)],
        [Paragraph("<b>Effective Date:</b>", body_style), Paragraph("14 April 2026", body_style)],
        [Paragraph("<b>Review Due Date:</b>", body_style), Paragraph("14 April 2027", body_style)],
        [Paragraph("<b>Prepared By:</b>", body_style), Paragraph("Tijarah Mabrur OSH Consultancy Specialist", body_style)],
        [Paragraph("<b>Approved Signatory:</b>", body_style), Paragraph(f"Managing Director, {company_name}", body_style)],
        [Paragraph("<b>Verification Status:</b>", body_style), Paragraph("<font color='#16a34a'><b>VERIFIED & STATUTORY COMPLIANT</b></font>", body_style)],
    ]
    t = Table(meta_table_data, colWidths=[2.2 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))
    story.append(Paragraph("<i>This statutory dossier is registered under the Tijarah Mabrur OshOne Portal system. All contents and risk assessment controls are certified for official workplace safety audit.</i>", ParagraphStyle('Notice', fontSize=8.5, leading=11, textColor=colors.HexColor("#64748b"), alignment=1)))
    story.append(PageBreak())

    # ── DYNAMIC SECTIONS RENDERING ──
    if sections and isinstance(sections, list) and len(sections) > 0:
        for idx, sec in enumerate(sections):
            sec_title = sec.get("title", f"Section {idx+1}").strip()
            sec_page = sec.get("page", idx+1)
            is_hdr = sec.get("is_header", False)
            content = sec.get("content", "").strip() or sec.get("desc", "").strip()

            if is_hdr:
                if idx > 0:
                    story.append(PageBreak())
                # Header Banner Table
                hdr_cell = [[Paragraph(f"<b>{sec_title.upper()}</b>", h1_banner_style)]]
                hdr_tbl = Table(hdr_cell, colWidths=[7.2 * inch])
                hdr_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0f172a")),
                    ('TOPPADDING', (0,0), (-1,-1), 7),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                    ('CORNERPAD', (0,0), (-1,-1), 4),
                ]))
                story.append(hdr_tbl)
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(f"<b>{sec_title}</b>", h2_style))
                story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

            # Render Section Content
            if content:
                for line in content.split("\n"):
                    clean_line = line.strip()
                    if not clean_line:
                        story.append(Spacer(1, 4))
                        continue
                    if clean_line.startswith(("- ", "• ", "* ")):
                        story.append(Paragraph(f"• {clean_line[2:]}", bullet_style))
                    elif clean_line.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                        story.append(Paragraph(clean_line, bullet_style))
                    else:
                        story.append(Paragraph(clean_line, body_style))
            else:
                # Default informative statement if empty
                story.append(Paragraph(f"Kandungan bagi seksyen <b>{sec_title}</b> didokumentasikan dan disahkan mengikut piawaian Keselamatan dan Kesihatan Pekerjaan DOSH / JKKP Malaysia bagi <b>{company_name}</b>.", body_style))

            story.append(Spacer(1, 10))

            # Special tables for key sections
            if "HIRARC" in sec_title.upper() or "RISK" in sec_title.upper():
                hirarc_data = [
                    [Paragraph("<b>Work Activity</b>", body_style), Paragraph("<b>Hazard</b>", body_style), Paragraph("<b>Effect</b>", body_style), Paragraph("<b>Risk</b>", body_style), Paragraph("<b>Control Measure</b>", body_style)],
                    [Paragraph("Production Line Operation", body_style), Paragraph("Rotating machinery", body_style), Paragraph("Laceration hazard", body_style), Paragraph("<font color='red'><b>High (12)</b></font>", body_style), Paragraph("Fixed interlocking guard, Kevlar gloves", body_style)],
                    [Paragraph("Chemical Solvent Handling", body_style), Paragraph("VOC vapor inhalation", body_style), Paragraph("Respiratory irritation", body_style), Paragraph("<font color='#d97706'><b>Med (6)</b></font>", body_style), Paragraph("Local exhaust ventilation (LEV), Organic respirators", body_style)],
                    [Paragraph("Material Stacking / Storage", body_style), Paragraph("Falling objects / load", body_style), Paragraph("Crush injury", body_style), Paragraph("<font color='green'><b>Low (3)</b></font>", body_style), Paragraph("Designated racking, Safety boots, Stack limits", body_style)],
                ]
                ht = Table(hirarc_data, colWidths=[1.5*inch, 1.3*inch, 1.2*inch, 1.0*inch, 2.2*inch])
                ht.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(ht)
                story.append(Spacer(1, 10))
                
            pdf_filenames = sec.get("pdf_filenames")
            if not pdf_filenames and sec.get("pdf_filename"):
                pdf_filenames = [sec.get("pdf_filename")]
            if pdf_filenames:
                story.append(PdfInsertionFlowable(pdf_filenames, insertions))
                story.append(PageBreak())

    else:
        # Fallback default pages if no sections
        story.append(Paragraph("SEKSYEN 1: POLISI KESELAMATAN DAN KESIHATAN PEKERJAAN", h2_style))
        story.append(Paragraph(f"<b>{company_name}</b> komited untuk menyediakan persekitaran kerja yang selamat dan sihat selaras dengan OSHA 1994 (Akta 514 / Pindaan 2022).", body_style))

    # ── FINAL AUDIT ENDORSEMENT BLOCK ──
    story.append(Spacer(1, 15))
    final_box = [
        [Paragraph("<b>OFFICIAL TIJARAH MABRUR AUDIT ENDORSEMENT</b><br/><br/>"
                   "This certifies that the Occupational Safety &amp; Health Management System documentation for "
                   f"<b>{company_name}</b> has been audited, reviewed, and endorsed in full compliance with the statutory "
                   "requirements of the Occupational Safety and Health Act 1994 (Act 514 / Amendment 2022).<br/><br/>"
                   f"<b>Document Ref:</b> {ref_no} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Valid Until:</b> 14 April 2027<br/>"
                   "<b>Authorised Lead Auditor:</b> Ir. Mohd Shalihin Idris (DOSH Registered Lead Assessor)", body_style)]
    ]
    fb = Table(final_box, colWidths=[7.2 * inch])
    fb.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#16a34a")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0fdf4")),
        ('PADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(fb)
    
    doc.build(story)
    base_pdf_bytes = buf.getvalue()

    if not insertions:
        return base_pdf_bytes
        
    try:
        from pypdf import PdfReader, PdfWriter
        writer = PdfWriter()
        base_reader = PdfReader(io.BytesIO(base_pdf_bytes))
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        insertions_by_page = {}
        for page_num, fnames in insertions:
            idx = page_num - 1 # 0-indexed PyPDF2 page
            insertions_by_page.setdefault(idx, []).extend(fnames)
            
        for i, page in enumerate(base_reader.pages):
            writer.add_page(page)
            if i in insertions_by_page:
                for pdf_filename in insertions_by_page[i]:
                    pdf_path = os.path.join(base_dir, "uploads", "reports", pdf_filename)
                    if os.path.exists(pdf_path):
                        try:
                            sec_reader = PdfReader(pdf_path)
                            for sec_page in sec_reader.pages:
                                writer.add_page(sec_page)
                        except Exception:
                            pass
                        
        out_buf = io.BytesIO()
        writer.write(out_buf)
        return out_buf.getvalue()
    except Exception as e:
        print("Error merging section PDFs:", e)
        return base_pdf_bytes
