import os
import json
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import torch

# Load model & processor
processor = AutoProcessor.from_pretrained("JackChew/Qwen2-VL-2B-OCR")
model = AutoModelForImageTextToText.from_pretrained("JackChew/Qwen2-VL-2B-OCR").to(
    torch.device("cuda" if torch.cuda.is_available() else "cpu")
)

# OCR function
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

# Process all images
image_folder = "img"
ocr_results = []

for filename in sorted(os.listdir(image_folder)):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        path = os.path.join(image_folder, filename)
        img = Image.open(path)
        width, height = img.size

        # Crop top 20% for title
        title_img = img.crop((0, 0, width, int(height * 0.2)))
        title = ocr_image(title_img, "Extract the title of this poem only, no extra text.")
        title = title.split("\n")[0].title()

        # Full OCR
        poem_text = ocr_image(img, "Transcribe this poem exactly as written.")

        ocr_results.append({
            "filename": filename,
            "title": title if title else "Untitled",
            "text": poem_text.strip()
        })

# Save to disk
with open("ocr_output.json", "w", encoding="utf-8") as f:
    json.dump(ocr_results, f, ensure_ascii=False, indent=2)

print("OCR complete. Saved to ocr_output.json")
