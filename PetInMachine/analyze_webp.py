import os
from PIL import Image

files = ['cat_lick.webp', 'cat_meow.webp']

print(f"{'Filename':<20} | {'Size (MB)':<10} | {'Dimensions':<15} | {'Frames':<6} | {'Mode':<10}")
print("-" * 70)

for f in files:
    if not os.path.exists(f):
        print(f"{f:<20} | Not Found")
        continue
        
    size_mb = os.path.getsize(f) / (1024 * 1024)
    
    try:
        with Image.open(f) as img:
            width, height = img.size
            frames = getattr(img, 'n_frames', 1)
            mode = img.mode
            
            # Check info for more details if available
            info = img.info
            
            print(f"{f:<20} | {size_mb:<10.2f} | {width}x{height:<9} | {frames:<6} | {mode:<10}")
            
            # Additional check for loop count
            loop = info.get('loop', 'N/A')
            duration = info.get('duration', 'N/A')
            
            # Simple heuristic for compression type based on size/pixels
            # (Real detection requires parsing chunks, which is complex in pure python without extra libs)
            compression = "Unknown"
            
            print(f"{f:<20} | {size_mb:<10.2f} | {width}x{height:<9} | {frames:<6} | {mode:<10}")
            print(f"  > Loop: {loop}, Duration: {duration}")

    except Exception as e:
        print(f"{f:<20} | {size_mb:<10.2f} | Error: {e}")

