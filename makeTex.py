import json
import unicodedata
import os
import re

def clean_text_for_latex(text):
    """Clean text and escape LaTeX special characters"""
    # First normalize unicode
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    
    # Escape LaTeX special characters
    latex_special_chars = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '^': r'\textasciicircum{}',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '\\': r'\textbackslash{}'
    }
    
    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)
    
    return text

def format_poem_text(text):
    """Format poem text with proper line breaks for LaTeX"""
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        cleaned_line = clean_text_for_latex(line.strip())
        if cleaned_line:
            formatted_lines.append(cleaned_line + r' \\')
        else:
            formatted_lines.append(r'\\')  # Empty line
    
    return '\n'.join(formatted_lines)

def generate_latex_document(pages):
    """Generate the complete LaTeX document"""
    
    latex_content = []
    
    # Document header
    latex_content.append(r'\documentclass[12pt,letterpaper]{book}')
    latex_content.append(r'\usepackage[utf8]{inputenc}')
    latex_content.append(r'\usepackage[T1]{fontenc}')
    latex_content.append(r'\usepackage{graphicx}')
    latex_content.append(r'\usepackage{geometry}')
    latex_content.append(r'\usepackage{fancyhdr}')
    latex_content.append(r'\usepackage{titletoc}')
    latex_content.append(r'\usepackage{center}')
    latex_content.append('')
    latex_content.append(r'% Page geometry')
    latex_content.append(r'\geometry{margin=1in}')
    latex_content.append('')
    latex_content.append(r'% Graphics path')
    latex_content.append(r'\graphicspath{{img/}}')
    latex_content.append('')
    latex_content.append(r'% Custom commands for centering poems')
    latex_content.append(r'\newenvironment{poemcenter}')
    latex_content.append(r'  {\begin{center}\begin{minipage}{0.8\textwidth}\centering}')
    latex_content.append(r'  {\end{minipage}\end{center}}')
    latex_content.append('')
    latex_content.append(r'% Custom command for poem titles')
    latex_content.append(r'\newcommand{\poemtitle}[1]{\begin{center}\textbf{\large #1}\end{center}\vspace{0.5cm}}')
    latex_content.append('')
    latex_content.append(r'% Custom command for image labels')
    latex_content.append(r'\newcommand{\imagelabel}[1]{\begin{center}\textit{\small Original scan: #1}\end{center}\vspace{0.3cm}}')
    latex_content.append('')
    latex_content.append(r'\begin{document}')
    latex_content.append('')
    
    # Title page (optional - you can customize this)
    latex_content.append(r'\title{Junior''s Poems}')
    latex_content.append(r'\author{}')
    latex_content.append(r'\date{}')
    latex_content.append(r'\maketitle')
    latex_content.append('')
    
    # Table of contents
    latex_content.append(r'\tableofcontents')
    latex_content.append(r'\newpage')
    latex_content.append('')
    
    # Generate poems
    for i, page in enumerate(pages):
        # Handle different data structures
        if isinstance(page, dict):
            # Dictionary format
            cleaned_title = clean_text_for_latex(page.get("title", f"Poem {i+1}"))
            poem_text = page.get("text", "")
            
            # Get image files
            image_files = []
            if "pages" in page and page["pages"]:
                image_files = page["pages"]
            elif "filename" in page:
                image_files = [page["filename"]]
        else:
            # Handle other formats - you may need to adjust this based on your actual data structure
            print(f"Warning: Unexpected page format at index {i}: {type(page)}")
            cleaned_title = f"Poem {i+1}"
            poem_text = str(page) if page else ""
            image_files = []
        
        # Start new chapter for each poem
        latex_content.append(f'\\chapter{{{cleaned_title}}}')
        latex_content.append('')
        
        # Poem text in centered environment
        latex_content.append(r'\begin{poemcenter}')
        formatted_text = format_poem_text(poem_text)
        latex_content.append(formatted_text)
        latex_content.append(r'\end{poemcenter}')
        latex_content.append('')
        latex_content.append(r'\vspace{1cm}')
        latex_content.append('')
        
        # Add scanned images
        for image_file in image_files:
            if image_file:
                # Clean filename for LaTeX
                safe_filename = clean_text_for_latex(image_file)
                
                latex_content.append(f'\\imagelabel{{{safe_filename}}}')
                latex_content.append('')
                latex_content.append(r'\begin{center}')
                # Remove file extension for includegraphics (LaTeX will find the right format)
                image_name_no_ext = os.path.splitext(image_file)[0]
                latex_content.append(f'\\includegraphics[width=0.8\\textwidth,height=0.7\\textheight,keepaspectratio]{{{image_name_no_ext}}}')
                latex_content.append(r'\end{center}')
                latex_content.append('')
                latex_content.append(r'\vspace{1cm}')
                latex_content.append('')
        
        # Add page break between poems (except for the last one)
        if i < len(pages) - 1:
            latex_content.append(r'\newpage')
            latex_content.append('')
    
    # End document
    latex_content.append(r'\end{document}')
    
    return '\n'.join(latex_content)

# Load saved OCR results
with open("ocr_output.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# Debug: Check the structure of the data
print("Data structure check:")
print(f"Type of pages: {type(pages)}")
if pages:
    print(f"Type of first item: {type(pages[0])}")
    print(f"First item: {pages[0]}")

# Sort poems by lowest filename number
def get_lowest_filename_number(poem):
    """Extract the lowest number from the poem's filenames"""
    # Handle different data structures
    if isinstance(poem, dict):
        # Dictionary format
        filenames = poem.get("pages", [poem.get("filename", "999.jpg")])
    elif isinstance(poem, list):
        # List format - assume it contains filename info
        filenames = poem if poem else ["999.jpg"]
    else:
        # Unknown format
        print(f"Warning: Unknown poem format: {type(poem)}")
        return 999
    
    numbers = []
    for filename in filenames:
        if isinstance(filename, str):
            # Extract number from filename (e.g., "07.JPG" -> 7)
            match = re.search(r'(\d+)', filename)
            if match:
                numbers.append(int(match.group(1)))
    return min(numbers) if numbers else 999

pages.sort(key=get_lowest_filename_number)

# Generate LaTeX content
latex_document = generate_latex_document(pages)

# Write to file
with open("juniors_poems.tex", "w", encoding="utf-8") as f:
    f.write(latex_document)

print("LaTeX file generated successfully: juniors_poems.tex")
print("\nTo compile to PDF, run:")
print("pdflatex juniors_poems.tex")
print("(You may need to run it twice for proper table of contents)")

# Optional: Also save a compilation script
compilation_script = """#!/bin/bash
# Compilation script for juniors_poems.tex
echo "Compiling LaTeX document..."
pdflatex juniors_poems.tex
pdflatex juniors_poems.tex  # Run twice for TOC
echo "Done! Check juniors_poems.pdf"
"""

with open("compile.sh", "w") as f:
    f.write(compilation_script)

# Make the script executable (on Unix-like systems)
try:
    os.chmod("compile.sh", 0o755)
    print("\nCompilation script created: compile.sh")
except:
    print("\nCompilation script created: compile.sh (you may need to make it executable)")

print("\nCustomization tips:")
print("- Edit the document class and packages at the top")
print("- Modify the \\poemcenter environment for different poem formatting")
print("- Adjust image sizing with the width/height parameters in \\includegraphics")
print("- Change margins, fonts, and spacing as needed")
print("- The images are referenced from the img/ folder")