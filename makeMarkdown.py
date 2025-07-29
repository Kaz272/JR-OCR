import json
from html_to_markdown import convert_to_markdown

# Load saved OCR results
with open("Qari_ocr_output.json", "r", encoding="utf-8") as f:
    pages = json.load(f)

# --- Poem Pages ---
for i, page in enumerate(pages):
   result = convert_to_markdown(page['text'], parser="lxml")
   print(result)
