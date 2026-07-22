import urllib.request
import json
import math
import os
import base64
import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from PIL import Image
import io

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-moire.svg"

WIDTH = 800
HEIGHT = 200

# Grid parameters
COLS = 52
ROWS = 7

def fetch_contributions(username):
    url = f"https://github-contributions.vercel.app/api/v1/{username}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
        return data["contributions"]
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def main():
    print(f"Fetching data for {USERNAME}...")
    contribs = fetch_contributions(USERNAME)
    if not contribs:
        print("No contributions found.")
        return
        
    conts = sorted(contribs, key=lambda x: x["date"])[-(COLS*ROWS):]
    
    while len(conts) < COLS*ROWS:
        conts.insert(0, {"intensity": 0})
        
    # Build 2D elevation grid (0 to 4 intensity)
    grid = np.zeros((ROWS, COLS))
    for i, c in enumerate(conts):
        col = i // ROWS
        row = i % ROWS
        grid[row, col] = float(c.get("intensity", 0))
        
    # Upscale by 2x for the PNG mask (104x14)
    smooth_grid = zoom(grid, 2.0, order=3)
    smooth_grid = gaussian_filter(smooth_grid, sigma=1.0)
    
    max_val = np.max(smooth_grid)
    if max_val <= 0: max_val = 1.0
    norm_grid = (smooth_grid / max_val * 255).astype(np.uint8)
    
    # Base luminance: even with 0 commits, we want a faint visibility (e.g. 15% opacity)
    # The mask uses luminance (black = transparent, white = opaque).
    norm_grid = np.clip(norm_grid + 30, 0, 255)
    
    img = Image.fromarray(norm_grid, mode='L')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64_img = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # Math for the Moiré Fringes
    # Background pitch
    d1 = 10.0
    # Foreground pitch (1.25% mismatch)
    d2 = 10.125
    
    # The horizontal translation needed to shift the 45-degree diagonal pattern 
    # perpendicularly by exactly d2 is: dx = d2 * sqrt(2)
    dx = d2 * math.sqrt(2)
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    # CSS Animation for the seamless sweep
    svg.append('<style>')
    svg.append(f'@keyframes sweep {{')
    svg.append(f'  0% {{ transform: translateX(0); }}')
    svg.append(f'  100% {{ transform: translateX({dx:.4f}px); }}')
    svg.append(f'}}')
    svg.append('</style>')
    
    # Deep dark background
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # Defs: Patterns and Masks
    svg.append('<defs>')
    
    # Background pattern (d1)
    svg.append(f'  <pattern id="bg-pattern" width="{d1}" height="{d1}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">')
    svg.append(f'    <line x1="0" y1="0" x2="0" y2="{d1}" stroke="#0e4429" stroke-width="{d1/2}" />')
    svg.append('  </pattern>')
    
    # Foreground pattern (d2)
    svg.append(f'  <pattern id="fg-pattern" width="{d2}" height="{d2}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">')
    # Bright green for the foreground wave
    svg.append(f'    <line x1="0" y1="0" x2="0" y2="{d2}" stroke="#39d353" stroke-width="{d2/2}" />')
    svg.append('  </pattern>')
    
    # SVG Filter to further smooth the mask if needed
    svg.append('  <filter id="mask-blur">')
    svg.append('    <feGaussianBlur stdDeviation="4" />')
    svg.append('  </filter>')
    
    # Continuous Field Opacity Mask
    svg.append('  <mask id="commit-mask">')
    svg.append(f'    <image href="data:image/png;base64,{b64_img}" x="0" y="0" width="{WIDTH}" height="{HEIGHT}" preserveAspectRatio="none" filter="url(#mask-blur)" />')
    svg.append('  </mask>')
    
    svg.append('</defs>')
    
    # Draw Background Layer (static, dark green)
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="url(#bg-pattern)" />')
    
    # Draw Foreground Layer (animated, bright green, masked by commit data)
    svg.append('<g style="animation: sweep 40s linear infinite;" mask="url(#commit-mask)">')
    svg.append(f'  <rect x="-50" y="-50" width="{WIDTH + 100}" height="{HEIGHT + 100}" fill="url(#fg-pattern)" />')
    svg.append('</g>')
    
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
