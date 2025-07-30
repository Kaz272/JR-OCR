import json
from fpdf import FPDF
import unicodedata
import os
from PIL import Image

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

def add_image_to_pdf(pdf, image_path, max_width=180, max_height=240):
    """Add an image to the PDF, scaling it to fit within the specified dimensions"""
    if not os.path.exists(image_path):
        print(f"Warning: Image not found: {image_path}")
        return False
    
    try:
        # Get image dimensions
        with Image.open(image_path) as img:
            img_width, img_height = img.size
        
        # Calculate scaling to fit within max dimensions while maintaining aspect ratio
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale_ratio = min(width_ratio, height_ratio)
        
        # Calculate final dimensions
        final_width = img_width * scale_ratio
        final_height = img_height * scale_ratio
        
        # Center the image on the page
        x_pos = (pdf.w - final_width) / 2
        y_pos = pdf.get_y()
        
        # Check if image fits on current page, if not add new page
        if y_pos + final_height > pdf.h - pdf.b_margin:
            pdf.add_page()
            y_pos = pdf.t_margin
        
        # Add the image
        pdf.image(image_path, x=x_pos, y=y_pos, w=final_width, h=final_height)
        
        # Move cursor below the image
        pdf.set_y(y_pos + final_height + 10)
        
        return True
    except Exception as e:
        print(f"Error adding image {image_path}: {e}")
        return False

# Load saved OCR results
with open("ocr_output.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Sort poems by lowest filename number
def get_lowest_filename_number(poem):
    """Extract the lowest number from the poem's filenames"""
    filenames = poem.get("pages", [poem.get("filename", "999.jpg")])
    numbers = []
    for filename in filenames:
        # Extract number from filename (e.g., "07.JPG" -> 7)
        import re
        match = re.search(r'(\d+)', filename)
        if match:
            numbers.append(int(match.group(1)))
    return min(numbers) if numbers else 999

pages.sort(key=get_lowest_filename_number)

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
    current_page = pdf.page_no()

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

    # Record for TOC (use current page number, not the calculated one)
    toc_entries.append((cleaned_title, current_page))
    
    # Add scanned images after the poem text
    # Get list of image files for this poem
    image_files = []
    if "pages" in page and page["pages"]:
        # Multiple pages case
        image_files = page["pages"]
    elif "filename" in page:
        # Single page case
        image_files = [page["filename"]]
    
    # Add each scanned image
    for image_file in image_files:
        if image_file:  # Make sure filename is not empty
            # Add some space before the image
            pdf.ln(15)
            
            # Add a small label for the scanned image
            pdf.set_font("Arial", "I", 10)
            label_text = f"Original scan: {image_file}"
            label_width = pdf.get_string_width(label_text)
            pdf.set_x((pdf.w - label_width) / 2)
            pdf.cell(0, 5, label_text, ln=True, align="C")
            pdf.ln(5)
            
            # Add the image from the img folder
            image_path = os.path.join("img", image_file)
            success = add_image_to_pdf(pdf, image_path)
            
            if not success:
                # If image couldn't be added, add a placeholder text
                pdf.set_font("Arial", "I", 10)
                error_text = f"[Image not found: {image_file}]"
                error_width = pdf.get_string_width(error_text)
                pdf.set_x((pdf.w - error_width) / 2)
                pdf.cell(0, 10, error_text, ln=True, align="C")
                pdf.ln(10)

# --- Finalize TOC (return to page 1) ---
# Save current state
current_page_num = pdf.page_no()
current_y = pdf.get_y()

# Go to TOC page
pdf.page = 1
pdf.set_font("Arial", size=12)
for (title, page_num), y in zip(toc_entries, toc_y_positions):
    pdf.set_xy(10, y)
    dots = "." * max(1, 70 - len(title))  # Ensure at least one dot
    pdf.cell(0, 10, f"{title} {dots} {page_num}")

# Restore state - this prevents extra blank pages
pdf.page = current_page_num
pdf.set_y(current_y)

# --- Output ---
pdf.output("juniors_poems.pdf")
print("PDF generated successfully with scanned images!")