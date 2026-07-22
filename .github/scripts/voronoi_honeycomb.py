import urllib.request
import json
import math
import random
import os

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-honeycomb.svg"

WIDTH = 800
HEIGHT = 200

# Hexagonal Grid parameters
COLS = 52
ROWS = 7
SIZE = 8

# Math for a flat-topped hexagon
W = 2 * SIZE
H = math.sqrt(3) * SIZE
X_SPACING = 1.5 * SIZE
Y_SPACING = H

# Center the grid
START_X = (WIDTH - (COLS * X_SPACING)) / 2 + SIZE
START_Y = (HEIGHT - (ROWS * Y_SPACING)) / 2 + (H / 2)

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
        
    # Get last 364 days
    conts = sorted(contribs, key=lambda x: x["date"])[-(COLS*ROWS):]
    
    # Pad if new account
    while len(conts) < COLS*ROWS:
        conts.insert(0, {"intensity": 0})
        
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    # Deep dark background to make the glow pop
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # Standard GitHub Contribution Colors
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    
    for i, c in enumerate(conts):
        col = i // ROWS
        row = i % ROWS
        
        # Calculate perfectly staggered honeycomb centers
        cx = START_X + col * X_SPACING
        cy = START_Y + row * Y_SPACING
        if col % 2 == 1:
            cy += H / 2
            
        intensity = int(c.get("intensity", 0))
        color = colors[min(4, intensity)]
        
        # Contribution controls Area/Scale & Border thickness
        # Higher intensity = tighter, fuller hexagons with less border gap
        scale = 0.75 + (intensity * 0.05) if intensity > 0 else 0.55
        stroke_w = 0.5 + (intensity * 0.3)
        
        # Generate vertices for both states
        perfect_pts = []
        chaos_pts = []
        
        for v in range(6):
            angle = math.radians(60 * v)
            
            # The Perfect Lloyd Relaxation state
            px = cx + math.cos(angle) * SIZE * scale
            py = cy + math.sin(angle) * SIZE * scale
            
            # The Chaotic Irregular Voronoi state
            noise_dist = random.uniform(SIZE * 0.2, SIZE * 2.8)
            noise_angle = angle + random.uniform(-0.8, 0.8)
            drift_x = random.uniform(-SIZE * 1.5, SIZE * 1.5)
            drift_y = random.uniform(-SIZE * 1.5, SIZE * 1.5)
            
            cx_x = cx + drift_x + math.cos(noise_angle) * noise_dist
            cx_y = cy + drift_y + math.sin(noise_angle) * noise_dist
            
            perfect_pts.append(f"{px:.1f},{py:.1f}")
            chaos_pts.append(f"{cx_x:.1f},{cx_y:.1f}")
            
        str_perfect = " ".join(perfect_pts)
        str_chaos = " ".join(chaos_pts)
        
        # Contribution controls relaxation speed (delay)
        # We create a cascading wave from left to right, with slight randomness
        delay = (col * 0.06) + random.uniform(0, 0.4)
        dur = 12.0
        
        svg.append(f'<polygon fill="{color}" stroke="{color}" stroke-width="{stroke_w}" opacity="0.9">')
        # We use native SVG keySplines for the smooth physics feel
        # Chaos -> Perfect (Relaxation) -> Perfect (Hold) -> Chaos (Dissolve)
        svg.append(f'  <animate attributeName="points" ')
        svg.append(f'    values="{str_chaos}; {str_perfect}; {str_perfect}; {str_chaos}" ')
        svg.append(f'    keyTimes="0; 0.4; 0.8; 1" ')
        svg.append(f'    calcMode="spline" ')
        svg.append(f'    keySplines="0.4 0 0.2 1; 0 0 1 1; 0.4 0 0.2 1" ')
        svg.append(f'    dur="{dur}s" repeatCount="indefinite" begin="{delay}s" />')
        svg.append(f'</polygon>')
        
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
