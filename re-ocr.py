import os
import json
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch
import re

# Load model & processor (same as before)
processor = AutoProcessor.from_pretrained("JackChew/Qwen2-VL-2B-OCR")
model = AutoModelForImageTextToText.from_pretrained("JackChew/Qwen2-VL-2B-OCR").to(
    torch.device("cuda" if torch.cuda.is_available() else "cpu")
)

# OCR function (same as before)
def ocr_image(image, prompt_text):
    conversation = [{
        "role": "user",
        "content": [{"type": "image"}, {"type": "text", "text": prompt_text}]
    }]
    prompt = processor.apply_chat_template(conversation, add_generation_prompt=True)
    inputs = processor(text=[prompt], images=[image], padding=True, return_tensors="pt").to(model.device)
    output_ids = model.generate(**inputs, max_new_tokens=2048)
    generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, output_ids)]
    return processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

def extract_title_from_text(full_text, debug_filename=""):
    """Extract title from full OCR text using smart heuristics"""
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    if debug_filename:
        print(f"\nDebug - Re-analyzing {debug_filename}:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i}: '{line}'")
    
    # Look for title in first several lines
    for i, line in enumerate(lines[:10]):
        # Skip page numbers and very short lines
        if line.isdigit() or len(line) < 2:
            continue
            
        # Skip common non-title elements
        skip_phrases = [
            "frederick thayer", "oakland", "maryland", "published", "forum",
            "to a. s. d.", "your face", "word of god", "when i would"
        ]
        if any(phrase in line.lower() for phrase in skip_phrases):
            continue
            
        # Check for continuation markers
        if "(continued)" in line.lower() or "(cont" in line.lower():
            continue
            
        # Skip parenthetical subtitles for now (we'll add them back later)
        if line.startswith("(") and line.endswith(")"):
            subtitle = line
            continue
            
        # Look for title characteristics
        is_likely_title = False
        
        # All caps or mostly caps (allowing for some lowercase)
        if line.isupper() or (sum(1 for c in line if c.isupper()) > len(line) * 0.6):
            is_likely_title = True
            
        # Title case and reasonable length
        elif line.istitle() and 2 <= len(line) <= 40:
            is_likely_title = True
            
        # Check if it's a short line that's not clearly poem content
        elif (len(line.split()) <= 4 and 
              not line.lower().startswith(("when", "the", "and", "but", "or", "in", "on", "at", "to", "from")) and
              not any(char in line for char in ".,!?;:")):
            is_likely_title = True
            
        if is_likely_title:
            title = line.strip()
            
            # Check if next line is a subtitle in parentheses
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("(") and next_line.endswith(")"):
                    title += f" {next_line}"
                    
            # Clean up spacing (fix OCR issues like "L E G E R D E M A I N")
            if len(title.split()) > 3 and all(len(word) <= 2 for word in title.split() if word.isalpha()):
                title = ''.join(title.split())
                
            if debug_filename:
                print(f"  -> Found title: '{title}'")
            return title
    
    if debug_filename:
        print(f"  -> No title found, using 'Untitled'")
    return "Untitled"

def clean_poem_text(text, title):
    """Remove title and other metadata from poem text"""
    lines = text.split('\n')
    cleaned_lines = []
    
    # Remove title lines from the beginning
    title_words = set(title.lower().replace('(', '').replace(')', '').split())
    skip_count = 0
    
    for i, line in enumerate(lines):
        line_words = set(line.lower().replace('(', '').replace(')', '').split())
        
        # Skip lines that are primarily the title
        if i < 5 and title_words and len(title_words.intersection(line_words)) > len(title_words) * 0.6:
            skip_count += 1
            continue
            
        # Skip metadata lines
        if any(phrase in line.lower() for phrase in ["frederick thayer", "oakland", "maryland", "published"]):
            continue
            
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines).strip()

# Load existing results
with open("ocr_output.json", "r", encoding="utf-8") as f:
    ocr_results = json.load(f)

# Find untitled poems
untitled_poems = [poem for poem in ocr_results if poem["title"].lower() == "untitled"]

if not untitled_poems:
    print("No untitled poems found to reprocess!")
    exit()

print(f"Found {len(untitled_poems)} untitled poems to reprocess:")
for poem in untitled_poems:
    if "pages" in poem:
        print(f"  - {poem['pages']}")
    else:
        print(f"  - {poem['filename']}")

# Ask user for confirmation
response = input(f"\nReprocess these {len(untitled_poems)} poems? (y/n): ")
if response.lower() != 'y':
    print("Cancelled.")
    exit()

# Reprocess untitled poems
image_folder = "img"
updated_count = 0

for i, poem in enumerate(untitled_poems):
    # Get the filename(s) for this poem
    if "pages" in poem:
        filenames = poem["pages"]
    else:
        filenames = [poem["filename"]]
    
    print(f"\nReprocessing poem {i+1}/{len(untitled_poems)}: {filenames}")
    
    # Process each page of this poem
    combined_text = ""
    for filename in filenames:
        path = os.path.join(image_folder, filename)
        if os.path.exists(path):
            img = Image.open(path)
            
            # Try with different prompts for better results
            prompts = [
                "Transcribe all text from this document exactly as written, preserving line breaks and spacing.",
                "Read all the text in this image carefully, including the title at the top.",
                "Extract all visible text from this page, maintaining the original formatting."
            ]
            
            best_text = ""
            for prompt in prompts:
                try:
                    text = ocr_image(img, prompt)
                    if len(text) > len(best_text):  # Use the longest result
                        best_text = text
                except Exception as e:
                    print(f"    Error with prompt: {e}")
                    continue
            
            if best_text:
                combined_text += best_text + "\n\n"
            else:
                print(f"    Failed to OCR {filename}")
    
    if combined_text.strip():
        # Extract new title
        new_title = extract_title_from_text(combined_text, filenames[0])
        
        if new_title != "Untitled":
            # Update the poem in our results
            poem["title"] = new_title
            poem["text"] = clean_poem_text(combined_text, new_title)
            updated_count += 1
            print(f"    ✓ Updated title to: '{new_title}'")
        else:
            print(f"    ✗ Still couldn't extract title")
    else:
        print(f"    ✗ No text extracted")

# Save updated results
if updated_count > 0:
    with open("ocr_output.json", "w", encoding="utf-8") as f:
        json.dump(ocr_results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Successfully updated {updated_count} poems!")
    print("Updated ocr_output.json with new titles.")
else:
    print("\n✗ No poems were successfully updated.")

print(f"\nSummary:")
print(f"  - Attempted to reprocess: {len(untitled_poems)}")
print(f"  - Successfully updated: {updated_count}")
print(f"  - Still untitled: {len(untitled_poems) - updated_count}")