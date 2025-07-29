import json
from fpdf import FPDF

# Load saved OCR results
with open("Qari_ocr_output.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

pdf = FPDF()
pdf.add_font("dejavu-sans", style="", fname="fonts/DejaVuSans.ttf")
pdf.add_font("dejavu-sans", style="b", fname="fonts/DejaVuSans-Bold.ttf")
pdf.add_font("dejavu-sans", style="i", fname="fonts/DejaVuSans-Oblique.ttf")
pdf.add_font("dejavu-sans", style="bi", fname="fonts/DejaVuSans-BoldOblique.ttf")
# Different type of the same font design.
pdf.add_font("dejavu-sans-narrow", style="", fname="fonts/DejaVuSansCondensed.ttf")
pdf.add_font("dejavu-sans-narrow", style="i", fname="fonts/DejaVuSansCondensed-Oblique.ttf")
pdf.set_font('dejavu-sans', '', 12)
# --- Poem Pages ---
for i, page in enumerate(pages):
   pdf.add_page()
   pdf.write_html(page['text'])

pdf.output("juniors_poems_formatted.pdf")