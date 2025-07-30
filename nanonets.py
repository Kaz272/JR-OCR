import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from PIL import Image

# Load model and processor
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-2B-Instruct",
    torch_dtype="auto",
    device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-2B-Instruct")

# Load the image
image = Image.open("img/03.jpg")

# Simple OCR prompt
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": image},
            {"type": "text", "text": "Read all the text in this image."}
        ]
    }
]

# Build prompt
prompt = processor.apply_chat_template(messages, add_generation_prompt=True)

# Process inputs
inputs = processor(prompt, return_tensors="pt").to(model.device)

# Generate output
generated_ids = model.generate(**inputs, max_new_tokens=512)

# Decode and print
output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(output)
