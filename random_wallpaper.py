#!/usr/bin/env python3

import sys
import subprocess
import re
import random
import tempfile
import shutil
from pathlib import Path
from PIL import Image, ImageOps

def get_monitors():
    """Get monitors with their properties."""
    try:
        output = subprocess.check_output(['xrandr', '--query'], text=True)
    except subprocess.CalledProcessError:
        print("Error: Could not run xrandr")
        sys.exit(1)
    
    monitors = []
    for line in output.split('\n'):
        if ' connected' in line:
            match = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
            if match:
                name = line.split()[0]
                width = int(match.group(1))
                height = int(match.group(2))
                orientation = 'horizontal' if width > height else 'vertical'
                monitors.append({
                    'name': name,
                    'width': width,
                    'height': height,
                    'orientation': orientation
                })
    
    return monitors

def get_image_info(image_path):
    """Get image orientation - returns tuple (width, height, orientation)."""
    try:
        with Image.open(image_path) as img:
            # Get EXIF orientation without loading full image data
            width, height = img.size

            # Check for EXIF orientation tag (274 is orientation tag)
            try:
                exif = img.getexif()
                orientation_tag = exif.get(274) if exif else None

                # Orientations 5, 6, 7, 8 swap width/height
                if orientation_tag in (5, 6, 7, 8):
                    width, height = height, width
            except:
                pass  # No EXIF data, use original dimensions

            if width > height:
                return width, height, 'horizontal'
            elif height > width:
                return width, height, 'vertical'
            else:
                return width, height, 'horizontal'  # treat square as horizontal
    except Exception as e:
        print(f"Warning: Cannot read {image_path}: {e}")
        return None, None, None

def find_images(directory):
    """Find and categorize images by orientation."""
    extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    horizontal = []
    vertical = []

    directory = Path(directory)
    if not directory.is_dir():
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)

    print(f"Scanning {directory} for images...")

    # First, collect all image paths
    image_paths = [p for p in directory.rglob('*') if p.is_file() and p.suffix.lower() in extensions]
    total = len(image_paths)
    print(f"Found {total} image files, analyzing orientations...")

    # Now process them with progress indicator
    for idx, img_path in enumerate(image_paths, 1):
        if idx % 10 == 0 or idx == total:
            print(f"  Processing {idx}/{total}...", end='\r')

        w, h, orientation = get_image_info(img_path)
        if orientation == 'horizontal':
            horizontal.append(str(img_path))
        elif orientation == 'vertical':
            vertical.append(str(img_path))

    print(f"\nFound: {len(horizontal)} horizontal, {len(vertical)} vertical\n")
    return horizontal, vertical

def prepare_image(image_path, temp_dir):
    """
    Prepare image by applying EXIF rotation and saving without EXIF.
    This prevents xwallpaper from applying rotation again.
    Returns path to prepared image.
    """
    try:
        with Image.open(image_path) as img:
            # Apply EXIF rotation to pixel data
            img = ImageOps.exif_transpose(img)

            # Save to temp file without EXIF data
            temp_path = Path(temp_dir) / f"wallpaper_{Path(image_path).name}"

            # Convert RGBA to RGB if needed (for JPEG)
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (0, 0, 0))
                rgb_img.paste(img, mask=img.split()[3])
                rgb_img.save(temp_path, 'JPEG', quality=95)
            else:
                img.save(temp_path, quality=95, exif=b'')

            return str(temp_path)
    except Exception as e:
        print(f"Warning: Could not prepare {image_path}: {e}")
        return image_path  # Fallback to original

def set_wallpapers(monitors, horizontal_images, vertical_images):
    """Set wallpapers per monitor."""
    if not monitors:
        print("Error: No monitors detected")
        sys.exit(1)

    # Check if we have images
    horizontal_needed = sum(1 for m in monitors if m['orientation'] == 'horizontal')
    vertical_needed = sum(1 for m in monitors if m['orientation'] == 'vertical')

    if horizontal_needed > 0 and not horizontal_images:
        print("ERROR: No horizontal images found!")
        sys.exit(1)

    if vertical_needed > 0 and not vertical_images:
        print("ERROR: No vertical images found!")
        sys.exit(1)

    # Shuffle
    random.shuffle(horizontal_images)
    random.shuffle(vertical_images)

    # Create temp directory for prepared images
    temp_dir = tempfile.mkdtemp(prefix='wallpaper_')

    try:
        # Build command - set each monitor individually
        h_idx = 0
        v_idx = 0

        print("Setting wallpapers:")
        for monitor in monitors:
            if monitor['orientation'] == 'horizontal':
                img = horizontal_images[h_idx % len(horizontal_images)]
                w, h, orient = get_image_info(img)
                print(f"  {monitor['name']} ({monitor['width']}x{monitor['height']}, {monitor['orientation']}) <- {Path(img).name} ({w}x{h}, {orient})")

                # Verify match
                if orient != 'horizontal':
                    print(f"    WARNING: Orientation mismatch!")

                # Prepare image (apply EXIF rotation, strip metadata)
                prepared_img = prepare_image(img, temp_dir)

                cmd = ['xwallpaper', '--output', monitor['name'], '--zoom', prepared_img]
                subprocess.run(cmd, check=True)
                h_idx += 1
            else:
                img = vertical_images[v_idx % len(vertical_images)]
                w, h, orient = get_image_info(img)
                print(f"  {monitor['name']} ({monitor['width']}x{monitor['height']}, {monitor['orientation']}) <- {Path(img).name} ({w}x{h}, {orient})")

                # Verify match
                if orient != 'vertical':
                    print(f"    WARNING: Orientation mismatch!")

                # Prepare image (apply EXIF rotation, strip metadata)
                prepared_img = prepare_image(img, temp_dir)

                cmd = ['xwallpaper', '--output', monitor['name'], '--zoom', prepared_img]
                subprocess.run(cmd, check=True)
                v_idx += 1

        print("\n✓ Wallpapers set successfully!")
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    if len(sys.argv) != 2:
        print("Usage: random-wallpaper.py <wallpaper-directory>")
        sys.exit(1)
    
    wallpaper_dir = sys.argv[1]
    
    monitors = get_monitors()
    print(f"Detected monitors:")
    for m in monitors:
        print(f"  {m['name']}: {m['width']}x{m['height']} ({m['orientation']})")
    print()
    
    horizontal, vertical = find_images(wallpaper_dir)
    
    if not horizontal and not vertical:
        print("ERROR: No images found")
        sys.exit(1)
    
    try:
        set_wallpapers(monitors, horizontal, vertical)
    except FileNotFoundError:
        print("\nERROR: xwallpaper not found!")
        print("Install it with: sudo apt install xwallpaper")
        print("            or: sudo pacman -S xwallpaper")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
