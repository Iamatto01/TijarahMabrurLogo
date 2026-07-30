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
