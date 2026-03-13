import os
import glob
from PIL import Image

def generate_sprites():
    images_dir = os.path.join(os.path.dirname(__file__), '..', 'images')
    output_png = os.path.join(images_dir, 'spritesheet.png')
    output_css = os.path.join(images_dir, 'sprites.css')
    
    # Sprite configuration
    display_size = 64
    quality_factor = 4 # 4x resolution (256px)
    sprite_size = display_size * quality_factor 
    columns = 10
    
    # Get all PNG files except the output sheet itself
    png_files = sorted(glob.glob(os.path.join(images_dir, '*.png')))
    png_files = [f for f in png_files if os.path.basename(f) != 'spritesheet.png']
    
    num_images = len(png_files)
    rows = (num_images + columns - 1) // columns
    
    # Create the sprite sheet image
    sheet_width = columns * sprite_size
    sheet_height = rows * sprite_size
    sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    css_lines = [
        "/* Auto-generated Spitesheet CSS (Retina Optimized) */",
        ".team-sprite {",
        "  display: inline-block;",
        "  width: " + str(display_size) + "px;",
        "  height: " + str(display_size) + "px;",
        "  background-image: url('spritesheet.png');",
        "  background-repeat: no-repeat;",
        "  background-size: " + str(sheet_width // quality_factor) + "px " + str(sheet_height // quality_factor) + "px;",
        "  vertical-align: middle;",
        "}",
        ""
    ]
    
    for i, file_path in enumerate(png_files):
        img = Image.open(file_path).convert('RGBA')
        img.thumbnail((sprite_size, sprite_size), Image.Resampling.LANCZOS)
        
        # Center the image in the high-res cell if it's smaller
        temp_img = Image.new('RGBA', (sprite_size, sprite_size), (0, 0, 0, 0))
        offset_x = (sprite_size - img.width) // 2
        offset_y = (sprite_size - img.height) // 2
        temp_img.paste(img, (offset_x, offset_y), img)
        
        col = i % columns
        row = i // columns
        pos_x = col * sprite_size
        pos_y = row * sprite_size
        
        sprite_sheet.paste(temp_img, (pos_x, pos_y), temp_img)
        
        # Generate CSS class (positions divided by quality factor for CSS)
        css_pos_x = pos_x // quality_factor
        css_pos_y = pos_y // quality_factor
        
        team_name = os.path.splitext(os.path.basename(file_path))[0]
        class_name = team_name.replace(' ', '-')
        css_lines.append(f".sprite-{class_name} {{ background-position: -{css_pos_x}px -{css_pos_y}px; }}")
    
    # Save files
    sprite_sheet.save(output_png)
    with open(output_css, 'w') as f:
        f.write("\n".join(css_lines))
    
    print(f"Generated sprite sheet: {output_png} ({num_images} images)")
    print(f"Generated CSS: {output_css}")

if __name__ == "__main__":
    generate_sprites()
