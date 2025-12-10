import os
from PIL import Image
import pillow_heif

base_dir = os.path.dirname(os.path.abspath(__file__))

input_folder = os.path.join(base_dir, "converter", "HEIC")
output_folder = os.path.join(base_dir, "converter", "JPG")

os.makedirs(output_folder, exist_ok=True)

for file in os.listdir(input_folder):
    if file.lower().endswith(".heic"):
        heic_path = os.path.join(input_folder, file)
        jpg_filename = file.rsplit(".", 1)[0] + ".jpg"
        jpg_path = os.path.join(output_folder, jpg_filename)

        # Skip if JPG already exists
        if os.path.exists(jpg_path):
            continue
        
        # Convert HEIC to JPG
        heif_file = pillow_heif.read_heif(heic_path)
        image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
        image.save(jpg_path, "JPEG")

        print(f"Converted {file} → {jpg_filename}")

print("Conversion process complete.")
