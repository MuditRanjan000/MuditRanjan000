import urllib.request
import json
import os
import random

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-lava.svg"

WIDTH = 800
HEIGHT = 400

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
        
    conts = sorted(contribs, key=lambda x: x["date"])[-364:]
    
    # Aggregate into 52 weeks
    weeks = [0] * 52
    for i, c in enumerate(conts):
        week = i // 7
        if week < 52:
            weeks[week] += int(c.get("intensity", 0))
            
    max_val = max(weeks) if max(weeks) > 0 else 1
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    svg.append('<defs>')
    # The magical Gooey filter (Metaballs)
    svg.append('  <filter id="goo">')
    svg.append('    <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur" />')
    svg.append('    <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9" result="goo" />')
    svg.append('    <feComposite in="SourceGraphic" in2="goo" operator="atop"/>')
    svg.append('  </filter>')
    
    # Multiple gradients based on intensity to look like beautiful neon lava
    colors = [
        ("#43e97b", "#38f9d7"), # Low - Green
        ("#00f2fe", "#4facfe"), # Med - Cyan
        ("#fa709a", "#fee140"), # High - Pink/Yellow
        ("#f83600", "#f9d423")  # Max - Red/Orange
    ]
    
    for i, (c1, c2) in enumerate(colors):
        svg.append(f'  <linearGradient id="grad_{i}" x1="0%" y1="0%" x2="100%" y2="100%">')
        svg.append(f'    <stop offset="0%" stop-color="{c1}" />')
        svg.append(f'    <stop offset="100%" stop-color="{c2}" />')
        svg.append(f'  </linearGradient>')
        
    svg.append('</defs>')
    
    # Background
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0a0a0f" rx="8" />')
    
    # The container that applies the filter to all elements inside it
    svg.append('<g filter="url(#goo)">')
    
    # Add a massive base blob at the bottom that everything merges seamlessly into
    svg.append(f'<rect x="-20" y="{HEIGHT - 40}" width="{WIDTH + 40}" height="100" fill="url(#grad_0)" />')
    
    # Create the floating blobs
    spacing = WIDTH / 53
    for i in range(52):
        val = weeks[i]
        if val == 0: continue
        
        normalized = val / max_val
        radius = 15 + (normalized * 25)
        
        x = spacing + (i * spacing)
        # Start at the bottom so they merge with the base rect
        base_y = HEIGHT - 20
        
        # Pick gradient based on intensity
        c_idx = min(3, int(normalized * 4))
        
        # Float up between 50px and 250px based on commits
        float_dist = 50 + (normalized * 200)
        
        dur = 3.0 + random.uniform(1.0, 4.0)
        delay = random.uniform(0, dur)
        
        # Use CSS keyframes for perfectly smooth hardware-accelerated floating
        svg.append(f'<style>')
        svg.append(f'@keyframes float_{i} {{')
        svg.append(f'  0%, 100% {{ transform: translate(0, 0); }}')
        svg.append(f'  50% {{ transform: translate({random.uniform(-20, 20)}px, -{float_dist}px); }}')
        svg.append(f'}}')
        svg.append(f'</style>')
        
        svg.append(f'<circle cx="{x}" cy="{base_y}" r="{radius}" fill="url(#grad_{c_idx})" ')
        svg.append(f'style="animation: float_{i} {dur}s ease-in-out infinite {delay}s;" />')
        
    svg.append('</g>')
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
