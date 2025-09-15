#!/usr/bin/env python3
"""
Generate basic icons for PWA
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, filename):
    """Create a simple icon with the ERP logo"""
    # Create a new image with a blue background
    img = Image.new('RGB', (size, size), '#3b82f6')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple building icon
    building_width = size * 0.6
    building_height = size * 0.7
    x = (size - building_width) // 2
    y = (size - building_height) // 2
    
    # Main building
    draw.rectangle([x, y, x + building_width, y + building_height], fill='white')
    
    # Windows
    window_size = building_width * 0.15
    window_spacing = building_width * 0.2
    
    for row in range(3):
        for col in range(2):
            wx = x + window_spacing + col * (window_size + window_spacing)
            wy = y + window_spacing + row * (window_size + window_spacing)
            draw.rectangle([wx, wy, wx + window_size, wy + window_size], fill='#3b82f6')
    
    # Save the image
    img.save(filename, 'PNG')
    print(f"Created {filename} ({size}x{size})")

def main():
    icons_dir = '/home/runner/work/ERP_Final/ERP_Final/static/icons'
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create different icon sizes
    sizes = [192, 512, 96]
    for size in sizes:
        if size == 96:
            create_icon(size, os.path.join(icons_dir, f'crm-{size}x{size}.png'))
            create_icon(size, os.path.join(icons_dir, f'finance-{size}x{size}.png'))
        else:
            create_icon(size, os.path.join(icons_dir, f'icon-{size}x{size}.png'))

if __name__ == '__main__':
    main()