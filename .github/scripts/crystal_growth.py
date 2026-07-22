import urllib.request
import json
import math
import os
import random

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-crystal.svg"

WIDTH = 900
HEIGHT = 200

# Grid parameters
COLS = 52
ROWS = 7
PITCH = 16

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
        
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    # CSS Animation for the crystal growth
    svg.append('<style>')
    svg.append('  .atom {')
    svg.append('    mix-blend-mode: screen;')
    svg.append('    animation: settle 12s infinite;')
    svg.append('  }')
    svg.append('  @keyframes settle {')
    # Use the requested overshoot spring ease for the "snap into place" phase
    svg.append('    0%, 15% { transform: translate(var(--dx), var(--dy)); animation-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1); }')
    # Use a smooth ease-in-out for the "drift apart" phase
    svg.append('    45%, 65% { transform: translate(0, 0); animation-timing-function: ease-in-out; }')
    svg.append('    85%, 100% { transform: translate(var(--dx), var(--dy)); }')
    svg.append('  }')
    svg.append('</style>')
    
    # Deep dark background
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # Defs: Radial Gradients
    svg.append('<defs>')
    gradients = [
        ("#161b22", "#0d1117"), # Intensity 0
        ("#196c42", "#0e4429"), # Intensity 1
        ("#009946", "#006d32"), # Intensity 2
        ("#73f590", "#26a641"), # Intensity 3
        ("#e8ffe0", "#39d353"), # Intensity 4 (almost white core for true white-hot additive blend)
    ]
    
    for i, (core, edge) in enumerate(gradients):
        svg.append(f'  <radialGradient id="grad-{i}">')
        svg.append(f'    <stop offset="0%" stop-color="{core}" />')
        svg.append(f'    <stop offset="100%" stop-color="{edge}" />')
        svg.append(f'  </radialGradient>')
    svg.append('</defs>')
    
    # Calculate starting offsets to perfectly center the 52x7 grid
    grid_w = (COLS - 1) * PITCH
    grid_h = (ROWS - 1) * PITCH
    off_x = (WIDTH - grid_w) / 2
    off_y = (HEIGHT - grid_h) / 2
    
    # Isolation group for the blend mode
    svg.append('<g style="isolation: isolate;">')
    
    # Radii for each intensity level
    radii = [2.0, 3.0, 4.0, 4.8, 5.5]
    
    for i, c in enumerate(conts):
        col = i // ROWS
        row = i % ROWS
        
        cx = off_x + col * PITCH
        cy = off_y + row * PITCH
            
        intensity = int(c.get("intensity", 0))
        r = radii[min(4, intensity)]
        
        # Max displacement is 8px.
        base_disp = 5 + intensity
        
        # Random angle, random distance up to base_disp
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(base_disp * 0.4, base_disp)
        dx = math.cos(angle) * dist
        dy = math.sin(angle) * dist
        
        # Delay creates a subtle wave or just organic randomness
        delay = random.uniform(0, -2.0) 
        
        svg.append(f'  <circle class="atom" cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#grad-{intensity})" ')
        svg.append(f'style="--dx: {dx:.1f}px; --dy: {dy:.1f}px; animation-delay: {delay:.2f}s;" />')
        
    svg.append('</g>')
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
