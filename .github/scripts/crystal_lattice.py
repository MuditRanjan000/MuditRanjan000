import urllib.request
import json
import math
import random
import os

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-crystal.svg"

WIDTH = 800
HEIGHT = 200

# Grid parameters
COLS = 52
ROWS = 7
CELL_SIZE = 12
START_X = (WIDTH - (COLS * CELL_SIZE)) / 2 + (CELL_SIZE / 2)
START_Y = (HEIGHT - (ROWS * CELL_SIZE)) / 2 + (CELL_SIZE / 2)

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

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - math.pow(-2 * t + 2, 3) / 2

def main():
    print(f"Fetching data for {USERNAME}...")
    contribs = fetch_contributions(USERNAME)
    if not contribs:
        print("No contributions found.")
        return
        
    conts = sorted(contribs, key=lambda x: x["date"])[-(COLS*ROWS):]
    
    # We need exactly COLS*ROWS elements
    while len(conts) < COLS*ROWS:
        conts.insert(0, {"intensity": 0})
        
    atoms = []
    
    for i, c in enumerate(conts):
        col = i // ROWS
        row = i % ROWS
        
        # Target position in the crystal lattice
        tx = START_X + col * CELL_SIZE
        ty = START_Y + row * CELL_SIZE
        
        # Random scattered start position (dissolved state)
        angle = random.uniform(0, math.pi * 2)
        dist = random.uniform(200, 800)
        sx = tx + math.cos(angle) * dist
        sy = ty + math.sin(angle) * dist
        
        intensity = int(c.get("intensity", 0))
        
        # Physics params based on commit intensity
        k = 0.03 + (intensity * 0.015) # Spring stiffness
        mass = 1.0 - (intensity * 0.1) # Mass
        mass = max(0.1, mass)
        damp = 0.88 # Friction
        
        atoms.append({
            "sx": sx, "sy": sy,
            "tx": tx, "ty": ty,
            "intensity": intensity,
            "k": k, "mass": mass, "damp": damp
        })
        
    FRAMES_RELAX = 120
    FRAMES_HOLD = 30
    FRAMES_DISSOLVE = 60
    TOTAL_FRAMES = FRAMES_RELAX + FRAMES_HOLD + FRAMES_DISSOLVE
    
    # Precompute molecular dynamics paths
    paths_x = [[] for _ in range(len(atoms))]
    paths_y = [[] for _ in range(len(atoms))]
    
    for i, atom in enumerate(atoms):
        x, y = atom["sx"], atom["sy"]
        vx, vy = 0.0, 0.0
        
        for f in range(TOTAL_FRAMES):
            if f < FRAMES_RELAX:
                # Physics relaxation (Verlet-ish integration with damping)
                fx = (atom["tx"] - x) * atom["k"]
                fy = (atom["ty"] - y) * atom["k"]
                vx = (vx + (fx / atom["mass"])) * atom["damp"]
                vy = (vy + (fy / atom["mass"])) * atom["damp"]
                x += vx
                y += vy
            elif f < FRAMES_RELAX + FRAMES_HOLD:
                # Hold equilibrium perfectly
                x = atom["tx"]
                y = atom["ty"]
            else:
                # Dissolve back to scattered start for a perfect infinite loop
                t = (f - (FRAMES_RELAX + FRAMES_HOLD)) / FRAMES_DISSOLVE
                e = ease_in_out_cubic(t)
                x = atom["tx"] + (atom["sx"] - atom["tx"]) * e
                y = atom["ty"] + (atom["sy"] - atom["ty"]) * e
                
            # Formatting to 1 decimal place to save SVG file size
            paths_x[i].append(f"{x:.1f}")
            paths_y[i].append(f"{y:.1f}")
            
    # Generate SVG
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # standard github contribution colors
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    
    for i, atom in enumerate(atoms):
        c_idx = min(4, atom["intensity"])
        color = colors[c_idx]
        
        val_x = ";".join(paths_x[i])
        val_y = ";".join(paths_y[i])
        
        r = 3.5 if atom["intensity"] > 0 else 2.5
        
        svg.append(f'<circle r="{r}" fill="{color}">')
        svg.append(f'  <animate attributeName="cx" values="{val_x}" dur="12s" repeatCount="indefinite" />')
        svg.append(f'  <animate attributeName="cy" values="{val_y}" dur="12s" repeatCount="indefinite" />')
        svg.append(f'</circle>')
        
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
