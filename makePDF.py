import json
from fpdf import FPDF
import unicodedata

def clean_text(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

def write_centered_multiline(pdf: FPDF, text: str, font_size=12):
    pdf.set_font("Arial", size=font_size)
    lines = text.split("\n")
    line_height = 6  # Adjust line spacing as needed
    
    # Calculate the center X position based on the longest line
    max_width = 0
    cleaned_lines = []
    for line in lines:
        cleaned = clean_text(line.strip())
        cleaned_lines.append(cleaned)
        if cleaned:
            string_width = pdf.get_string_width(cleaned)
            max_width = max(max_width, string_width)
    
    # Set consistent X position based on centering the longest line
    page_width = pdf.w - 2 * pdf.l_margin
    x_pos = (pdf.w - max_width) / 2 if max_width < page_width else pdf.l_margin
    
    for cleaned in cleaned_lines:
        if cleaned:
            pdf.set_x(x_pos)
            pdf.cell(0, line_height, cleaned, ln=True)
        else:
            # Handle blank lines
            pdf.ln(line_height)

# Load saved OCR results
with open("ocr_output.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Create single PDF with everything
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=20)

# --- Table of Contents Page ---
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(0, 10, "Table of Contents", ln=True, align="C")
pdf.ln(5)
pdf.set_font("Arial", size=12)

toc_entries = []
toc_y_positions = []

# Reserve lines in TOC (we'll fill in the page numbers later)
for page in pages:
    toc_y_positions.append(pdf.get_y())
    cleaned_title = clean_text(page["title"])
    pdf.cell(0, 10, f"{cleaned_title} ........................................", ln=True)

# --- Poem Pages ---
for i, page in enumerate(pages):
    pdf.add_page()
    page_num = pdf.page_no()

    # Title centered
    cleaned_title = clean_text(page["title"])
    pdf.set_font("Arial", "B", 14)
    title_width = pdf.get_string_width(cleaned_title)
    pdf.set_x((pdf.w - title_width) / 2)
    pdf.cell(0, 10, cleaned_title, ln=True)

    # Add some space after title
    pdf.ln(8)
    
    # Poem body centered
    write_centered_multiline(pdf, page["text"])

    # Footer with page number - use absolute positioning
    current_y = pdf.get_y()  # Save current position
    pdf.set_y(-15)  # Position footer
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f"Page {page_num}", align="C")
    
    # Reset to content area (this prevents the blank page issue)
    pdf.set_y(current_y)

    # Record for TOC
    toc_entries.append((cleaned_title, page_num))

# --- Finalize TOC (return to page 1) ---
pdf.page = 1
pdf.set_font("Arial", size=12)
for (title, page_num), y in zip(toc_entries, toc_y_positions):
    pdf.set_xy(10, y)
    dots = "." * max(1, 70 - len(title))  # Ensure at least one dot
    pdf.cell(0, 10, f"{title} {dots} {page_num}")

# --- Output ---
pdf.output("juniors_poems.pdf")
print("PDF generated successfully - no blank pages!")