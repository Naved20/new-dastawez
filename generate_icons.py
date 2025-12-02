# use_existing_logo.py
import os
import shutil

# Create icons directory
os.makedirs('static/img/icons', exist_ok=True)

# Copy your existing logo to all icon sizes
logo_path = 'static/img/logo.png'

if os.path.exists(logo_path):
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    for size in sizes:
        # Just copy the same file with different names
        shutil.copy(logo_path, f'static/img/icons/icon-{size}x{size}.jpg')
        print(f"✅ Copied: icon-{size}x{size}.jpg")
    
    print("🎉 All icons created (using existing JPG)")
else:
    print("❌ Logo not found at:", logo_path)
    print("💡 Please check if static/img/logo.jpg exists")