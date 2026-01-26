#!/usr/bin/env python3
"""
Favicon Generator Script for NeuroLens
Generates multi-size favicon assets from the main logo.
"""

from PIL import Image
import os

# Define paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, "assets")
FAVICON_DIR = os.path.join(ASSETS_DIR, "favicon")

# Source logo
SOURCE_LOGO = os.path.join(ASSETS_DIR, "logo.png")

# Favicon sizes to generate
FAVICON_SIZES = [
    (16, 16, "favicon-16x16.png"),
    (32, 32, "favicon-32x32.png"),
    (48, 48, "favicon-48x48.png"),
    (64, 64, "favicon-64x64.png"),
    (180, 180, "apple-touch-icon.png"),
    (192, 192, "android-chrome-192x192.png"),
    (512, 512, "android-chrome-512x512.png"),
]


def generate_favicons():
    """Generate favicon assets in multiple sizes."""

    # Create favicon directory if it doesn't exist
    os.makedirs(FAVICON_DIR, exist_ok=True)

    # Open source logo
    try:
        logo = Image.open(SOURCE_LOGO)
        print(f"✅ Loaded source logo: {SOURCE_LOGO}")
        print(f"   Original size: {logo.size}")
        print(f"   Mode: {logo.mode}")
    except Exception as e:
        print(f"❌ Error loading logo: {e}")
        return

    # Convert to RGBA if needed for transparency support
    if logo.mode != "RGBA":
        logo = logo.convert("RGBA")
        print(f"   Converted to RGBA mode")

    # Generate each size
    for width, height, filename in FAVICON_SIZES:
        try:
            # Use high-quality resampling
            resized = logo.resize((width, height), Image.Resampling.LANCZOS)

            output_path = os.path.join(FAVICON_DIR, filename)
            resized.save(output_path, "PNG", optimize=True)

            print(f"✅ Generated: {filename} ({width}x{height})")
        except Exception as e:
            print(f"❌ Error generating {filename}: {e}")

    # Generate ICO file (multi-size icon for browsers)
    try:
        ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64)]
        ico_images = []

        for size in ico_sizes:
            resized = logo.resize(size, Image.Resampling.LANCZOS)
            ico_images.append(resized)

        ico_path = os.path.join(FAVICON_DIR, "favicon.ico")
        ico_images[0].save(
            ico_path,
            format="ICO",
            sizes=ico_sizes,
            append_images=ico_images[1:]
        )
        print(f"✅ Generated: favicon.ico (multi-size)")
    except Exception as e:
        print(f"❌ Error generating favicon.ico: {e}")

    # Copy main logo to favicon directory as well
    try:
        logo_copy_path = os.path.join(FAVICON_DIR, "logo.png")
        logo.save(logo_copy_path, "PNG", optimize=True)
        print(f"✅ Copied: logo.png (original)")
    except Exception as e:
        print(f"❌ Error copying logo: {e}")

    print(f"\n🎉 Favicon generation complete!")
    print(f"   Output directory: {FAVICON_DIR}")


if __name__ == "__main__":
    generate_favicons()
