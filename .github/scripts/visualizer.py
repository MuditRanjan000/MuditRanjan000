import urllib.request
import json
import os
import random

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-visualizer.svg"

WIDTH = 800
HEIGHT = 200
BAR_WIDTH = 10
BAR_GAP = 5

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
            
    # Normalize week heights (max possible per week is 7*4 = 28)
    max_val = max(weeks) if max(weeks) > 0 else 1
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    
    # CSS Styles for animations
    svg.append('<style>')
    svg.append('.bar { transform-origin: bottom; }')
    svg.append('</style>')
    
    # Background
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    total_width = (BAR_WIDTH + BAR_GAP) * 52 - BAR_GAP
    start_x = (WIDTH - total_width) / 2
    
    for i in range(52):
        val = weeks[i]
        # Base height is between 10% and 80% of max height based on commits
        normalized = val / max_val
        base_h = 20 + (normalized * (HEIGHT - 60))
        
        x = start_x + i * (BAR_WIDTH + BAR_GAP)
        y = HEIGHT - base_h - 10 # 10px padding from bottom
        
        # Color gradient from left to right (Cyan to Purple)
        r = int(0 + (i / 51) * 150)
        g = int(200 - (i / 51) * 100)
        b = 255
        color = f"rgb({r}, {g}, {b})"
        
        # Give higher commit weeks faster/more intense animations
        duration = 1.0 + random.uniform(0.5, 1.5)
        delay = random.uniform(0, 2)
        
        # Animate the height using a custom keyframe for organic randomness
        # We inject a specific keyframe for every bar to give it unique bounce height
        bounce_scale = 1.0 + (normalized * 0.8) + random.uniform(0.1, 0.4)
        
        svg.append(f'<style>')
        svg.append(f'@keyframes bounce_{i} {{')
        svg.append(f'  0% {{ transform: scaleY(1); filter: brightness(1); }}')
        svg.append(f'  50% {{ transform: scaleY({bounce_scale}); filter: brightness(1.5) drop-shadow(0px 0px 5px {color}); }}')
        svg.append(f'  100% {{ transform: scaleY(1); filter: brightness(1); }}')
        svg.append(f'}}')
        svg.append(f'</style>')
        
        svg.append(f'<rect class="bar" x="{x}" y="{y}" width="{BAR_WIDTH}" height="{base_h}" fill="{color}" rx="3" ')
        svg.append(f'style="animation: bounce_{i} {duration}s ease-in-out infinite {delay}s; transform-origin: center bottom;" />')
        
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
        
    print(f"Saved {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
