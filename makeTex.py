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

def find_longest_line(text):
    """Find the longest line in the poem for verse centering"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return "Default line for centering"
    
    # Find the longest line by character count
    longest_line = max(lines, key=len)
    
    # Clean it for LaTeX (but keep original length characteristics)
    cleaned_longest = clean_text_for_latex(longest_line)
    
    return cleaned_longest

def format_poem_text_simple(text):
    """Simple poem text formatting for verse environment"""
    lines = text.split('\n')
    formatted_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line:
            cleaned_line = clean_text_for_latex(line)
            # Check if next line is empty (stanza break)
            if i + 1 < len(lines) and not lines[i + 1].strip():
                formatted_lines.append(cleaned_line + " \\\\!")  # Stanza break
            else:
                formatted_lines.append(cleaned_line + " \\\\")   # Regular line break
    
    # Clean up the last line
    if formatted_lines and formatted_lines[-1].endswith(" \\\\"):
        formatted_lines[-1] = formatted_lines[-1][:-3]
    
    return '\n'.join(formatted_lines)

def generate_advanced_latex_document(pages):
    """Generate LaTeX document with advanced poetry formatting"""
    
    latex_content = []
    
    # Document header with memoir class and reliable poetry packages
    latex_content.extend([
        r'\documentclass[16pt,letterpaper,oneside]{memoir}',
        r'\usepackage{fontspec}',   # For XeLaTeX/LuaLaTeX font handling
        r'\usepackage{verse}',      # Standard verse environment
        r'\usepackage{xcolor}',     # For colors
        r'\usepackage{microtype}',  # Better typography
        r'\usepackage{titlesec}',   # For custom section formatting
        '',
        r'\setmainfont{EB Garamond}     % Elegant serif',
       
        '',
        r'% Page geometry and styling',
        r'\settrimmedsize{11in}{8.5in}{*}',
        r'\setlength{\trimtop}{0pt}',
        r'\setlength{\trimedge}{\stockwidth}',
        r'\addtolength{\trimedge}{-\paperwidth}',
        r'\settypeblocksize{7.5in}{5.5in}{*}',
        r'\setulmargins{1.5in}{*}{*}',
        r'\setlrmargins{1.25in}{*}{*}',
        r'\setheadfoot{\onelineskip}{2\onelineskip}',
        r'\setheaderspaces{*}{2\onelineskip}{*}',
        r'\checkandfixthelayout',
        '',
        r'% Poetry-specific settings',
        r'\setlength{\vindent}{2em}',        # Verse indentation
        r'\setlength{\vleftskip}{2em}',      # Left margin for verses
        r'\setlength{\stanzaskip}{1em}',     # Space between stanzas
        '',
        r'% Custom poetry environments - altverse for alternating indentation',
        r'\newenvironment{poemblock}',
        r'  {\begin{verse}\centering}',
        r'  {\end{verse}}',
        '',
        r'% Page styles',
        r'\makepagestyle{poetry}',
        r'\makeevenhead{poetry}{\thepage}{}{\itshape The Poetry of Frederick A. Thayer Jr.}',
        r'\makeoddhead{poetry}{\itshape The Poetry of Frederick A. Thayer Jr.}{}{\thepage}',
        r'\pagestyle{poetry}',
        '',
        r'\renewcommand{\poemtitlefont}{\Huge\itshape\bfseries\centering}',
        ''
    ])
    
    # Begin document
    latex_content.extend([
        r'\begin{document}',
        '',
        r'% Title page',
        r'\begin{center}',
        r'\vspace*{2cm}',
        '{\\Huge\\bfseries The Poetry of Frederick A. Thayer Jr.}\\\\[2cm]',
        '{\\large Compiled by Frederick A. Thayer V}\\\\[1cm]',
        r'\vspace*{2cm}',
        r'\end{center}',
        r'\thispagestyle{empty}',
        r'\newpage',
        '',
        r'% Table of contents',
        r'\tableofcontents*',
        r'\newpage',
        ''
    ])
    
    # Generate poems with advanced formatting
    for i, page in enumerate(pages):
        # Handle different data structures
        if isinstance(page, dict):
            cleaned_title = clean_text_for_latex(page.get("title", f"Poem {i+1}"))
            poem_text = page.get("text", "")
        else:
            print(f"Warning: Unexpected page format at index {i}: {type(page)}")
            cleaned_title = f"Poem {i+1}"
            poem_text = str(page) if page else ""
        
        # Add poem to document - use poemtitle and poemtoc from verse package
        latex_content.append(f'% === Poem {i+1}: {cleaned_title} ===')
        
        # Format poem text with proper centering
        if poem_text.strip():
            # Find longest line for centering
            longest_line = find_longest_line(poem_text)
            formatted_text = format_poem_text_simple(poem_text)
            
            # Set verse width and add poem title
            latex_content.append(f'\\settowidth{{\\versewidth}}{{{longest_line}}}')
            latex_content.append(f'\\poemtitle{{{cleaned_title}}}')
            latex_content.append('')
            
            # Use verse with proper width
            latex_content.append(r'\begin{verse}[\versewidth]')
            latex_content.append(r'	\LARGE')
            latex_content.append(formatted_text)
            latex_content.append(r'\end{verse}')
            
            latex_content.append('')
        
        # Add spacing
        latex_content.append(r'\vspace{2cm}')
        latex_content.append('')
        
        # Page break between poems (except last)
        if i < len(pages) - 1:
            latex_content.extend([r'\newpage', ''])
    
    # End document
    latex_content.append(r'\end{document}')
    
    return '\n'.join(latex_content)

# Main execution
if __name__ == "__main__":
    # Load saved OCR results
    try:
        with open("ocr_output.json", "r", encoding="utf-8") as f:
            pages = json.load(f)
    except FileNotFoundError:
        print("Error: ocr_output.json not found. Creating sample data for testing.")
        pages = [
            {
                "title": "Sample Poem",
                "text": "Roses are red\nViolets are blue\nThis is a test\nJust for you",
                "pages": ["01.jpg"]
            }
        ]
    
    # Debug info
    print("Data structure check:")
    print(f"Type of pages: {type(pages)}")
    if pages:
        print(f"Type of first item: {type(pages[0])}")
        print(f"First item preview: {str(pages[0])[:200]}...")
    
    # Sort poems by filename number
    def get_lowest_filename_number(poem):
        if isinstance(poem, dict):
            filenames = poem.get("pages", [poem.get("filename", "999.jpg")])
        elif isinstance(poem, list):
            filenames = poem if poem else ["999.jpg"]
        else:
            return 999
        
        numbers = []
        for filename in filenames:
            if isinstance(filename, str):
                match = re.search(r'(\d+)', filename)
                if match:
                    numbers.append(int(match.group(1)))
        return min(numbers) if numbers else 999
    
    pages.sort(key=get_lowest_filename_number)
    
    # Generate main LaTeX document
    latex_document = generate_advanced_latex_document(pages)
    
    # Write main file
    with open("juniors_poems_advanced.tex", "w", encoding="utf-8") as f:
        f.write(latex_document)
    
    print("Advanced LaTeX file generated: juniors_poems_advanced.tex")