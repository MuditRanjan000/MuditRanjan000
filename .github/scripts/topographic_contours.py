import urllib.request
import json
import math
import os
import numpy as np
from scipy.ndimage import zoom, gaussian_filter
from skimage import measure

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-topography.svg"

WIDTH = 800
HEIGHT = 200

# Grid parameters
COLS = 52
ROWS = 7
CELL_SIZE = 12

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
        
    # Build 2D elevation grid
    grid = np.zeros((ROWS, COLS))
    for i, c in enumerate(conts):
        col = i // ROWS
        row = i % ROWS
        grid[row, col] = float(c.get("intensity", 0))
        
    # We apply a slight gaussian blur to the base grid to eliminate jagged 1-pixel spikes,
    # then upscale using cubic interpolation to make a perfectly smooth continuous scalar field.
    grid = gaussian_filter(grid, sigma=0.8)
    
    # Upscale by a factor of 8 for extremely smooth contour lines
    scale_factor = 8
    smooth_grid = zoom(grid, scale_factor, order=3)
    
    max_val = np.max(smooth_grid)
    if max_val <= 0: max_val = 1.0
    
    # 50 elevation slices
    NUM_SLICES = 50
    # Start slightly above 0 to avoid marching along the literal flat borders
    thresholds = np.linspace(0.1, max_val, NUM_SLICES)
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    # Deep dark background
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # Glow filter for the contour lines
    svg.append('<defs>')
    svg.append('  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">')
    svg.append('    <feGaussianBlur stdDeviation="1.5" result="blur" />')
    svg.append('    <feMerge>')
    svg.append('      <feMergeNode in="blur" />')
    svg.append('      <feMergeNode in="SourceGraphic" />')
    svg.append('    </feMerge>')
    svg.append('  </filter>')
    svg.append('</defs>')
    
    # Calculate rendering offsets to perfectly center the map
    map_w = COLS * scale_factor
    map_h = ROWS * scale_factor
    
    vis_scale = 1.7
    off_x = (WIDTH - (map_w * vis_scale)) / 2
    off_y = (HEIGHT - (map_h * vis_scale)) / 2
    
    svg.append(f'<g transform="translate({off_x}, {off_y}) scale({vis_scale})" filter="url(#glow)">')
    
    # CSS Animation for the temporal slicing (wave effect)
    svg.append('<style>')
    for i in range(NUM_SLICES):
        # We sweep a wave of visibility.
        # Opacity peaks when the wave passes the slice's index.
        svg.append(f'@keyframes wave_{i} {{')
        svg.append(f'  0%, 100% {{ opacity: 0.1; stroke-width: 0.3; }}')
        
        peak = (i / NUM_SLICES) * 100
        
        # At peak, the line is fully visible, thick, and bright
        svg.append(f'  {peak}% {{ opacity: 1.0; stroke-width: 1.2; }}')
        svg.append(f'}}')
    svg.append('</style>')
    
    for i, t in enumerate(thresholds):
        # Run the Marching Squares algorithm to extract contour paths
        contours = measure.find_contours(smooth_grid, t)
        
        if not contours:
            continue
            
        path_data = []
        for contour in contours:
            # SVG uses (x, y) = (col, row)
            pts = []
            for pt in contour:
                pts.append(f"{pt[1]:.1f},{pt[0]:.1f}")
            path_data.append("M " + " L ".join(pts))
            
        d = " ".join(path_data)
        
        # Color mapping (green scale) based on elevation
        # Low = dark green, High = bright glowing green
        ratio = i / NUM_SLICES
        r = int(14 + ratio * 45)
        g = int(68 + ratio * 145)
        b = int(41 + ratio * 42)
        color = f"rgb({r},{g},{b})"
        
        svg.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="0.3" opacity="0.1" ')
        # The wave sweeps back and forth perfectly smoothly
        svg.append(f'style="animation: wave_{i} 6s ease-in-out infinite alternate;" />')
        
    svg.append('</g>')
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
