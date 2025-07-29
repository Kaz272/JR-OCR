import os
import json
from PIL import Image
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch
from qwen_vl_utils import process_vision_info

# Load model & processor
model_name = "NAMAA-Space/Qari-OCR-v0.3-VL-2B-Instruct"
model = Qwen2VLForConditionalGeneration.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)
processor = AutoProcessor.from_pretrained(model_name)

# OCR function
def ocr_image(image, prompt_text, temp_filename="temp_image.png"):
    # Save image temporarily
    image.save(temp_filename)
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": f"file://{temp_filename}"},
                {"type": "text", "text": prompt_text},
            ],
        }
    ]
    
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("cuda" if torch.cuda.is_available() else "cpu")
    
    generated_ids = model.generate(**inputs, max_new_tokens=2000)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    # Clean up temp file
    os.remove(temp_filename)
    
    return output_text.strip()

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
        title_prompt = "Extract only the title of this poem. Return just the title text with no additional commentary."
        title = ocr_image(title_img, title_prompt, f"temp_title_{filename}")
        title = title.split("\n")[0].strip().title()

        # Full OCR with formatting preservation
        poem_prompt = "Below is the image of one page of a document. Return the plain text representation of this document as if you were reading it naturally, preserving the original formatting and line breaks. Do not hallucinate or add extra content."
        poem_text = ocr_image(img, poem_prompt, f"temp_poem_{filename}")

        ocr_results.append({
            "filename": filename,
            "title": title if title else "Untitled",
            "text": poem_text.strip()
        })
        
        print(f"Processed {filename}: {title}")

# Save to disk
with open("Qari_ocr_output.json", "w", encoding="utf-8") as f:
    json.dump(ocr_results, f, ensure_ascii=False, indent=2)

print("OCR complete. Saved to ocr_output.json")