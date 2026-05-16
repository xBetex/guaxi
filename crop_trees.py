from PIL import Image
import os

# =====================================================================
# EDIT YOUR CROP COORDINATES HERE
# Format: (left_x, top_y, right_x, bottom_y)
# Example for a 1024x1024 image cut perfectly in 4 squares:
# =====================================================================
CROP_BOXES = {
    "spring": (0, 0, 512, 512),       # Top-Left
    "summer": (512, 0, 1024, 512),    # Top-Right
    "autumn": (0, 512, 512, 1024),    # Bottom-Left
    "winter": (512, 512, 1024, 1024), # Bottom-Right
}

# The grid image
INPUT_IMAGE = r"ässets\spring-summer-fall-winter.png"

# Where to save the cropped images (these match what the simulation loads by default)
OUTPUT_FILES = {
    "spring": r"ässets\spring_small.png",
    "summer": r"ässets\summer_small.png",
    "autumn": r"ässets\autum_small.png",
    "winter": r"ässets\winter_small.png",
}

def main():
    if not os.path.exists(INPUT_IMAGE):
        print(f"Error: Could not find '{INPUT_IMAGE}'")
        return

    print(f"Opening {INPUT_IMAGE}...")
    try:
        with Image.open(INPUT_IMAGE) as img:
            print(f"Image loaded. Size: {img.size[0]}x{img.size[1]}")

            for season, box in CROP_BOXES.items():
                print(f"Cropping {season.upper()} tree with coordinates {box}...")
                
                # Crop the image using the box
                cropped_img = img.crop(box)
                
                # Save to the specific output file
                out_path = OUTPUT_FILES[season]
                cropped_img.save(out_path)
                print(f"  -> Saved to {out_path}")
                
        print("\nAll done! The simulation will automatically use these new images when you refresh the page.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
