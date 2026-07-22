import urllib.request
import json
import math
import random
import os

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-shooter.svg"

WIDTH = 800
HEIGHT = 250

COLS = 53
ROWS = 7
SIZE = 10
GAP = 3

GRID_W = COLS * (SIZE + GAP) - GAP
GRID_H = ROWS * (SIZE + GAP) - GAP

START_X = (WIDTH - GRID_W) / 2
START_Y = (HEIGHT - GRID_H) / 2 - 20 

def fetch_contributions(username, token):
    url = "https://api.github.com/graphql"
    query = """
    query($userName:String!) {
      user(login: $userName){
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                weekday
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    data = json.dumps({"query": query, "variables": {"userName": username}}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0'
    })
    try:
        with urllib.request.urlopen(req) as response:
            resp_data = json.loads(response.read().decode())
            
        weeks = resp_data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
        level_map = {
            "NONE": 0,
            "FIRST_QUARTILE": 1,
            "SECOND_QUARTILE": 2,
            "THIRD_QUARTILE": 3,
            "FOURTH_QUARTILE": 4
        }
        
        grid = {}
        # Take up to the last 53 weeks
        recent_weeks = weeks[-COLS:] if len(weeks) >= COLS else weeks
        for c, w in enumerate(recent_weeks):
            for d in w['contributionDays']:
                r = d['weekday']
                grid[(c, r)] = level_map.get(d["contributionLevel"], 0)
        return grid
    except Exception as e:
        print(f"Error fetching data from GraphQL: {e}")
        return {}

def main():
    print(f"Fetching data for {USERNAME}...")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN missing!")
        return
        
    grid = fetch_contributions(USERNAME, token)
    if not grid:
        return
        
    # Setup timeline
    T = 0.0
    ship_keyframes = []
    laser_elements = []
    target_animations = {}
    
    # Ship starting position
    ship_y = START_Y + GRID_H + 40
    ship_start_x = -50
    
    ship_keyframes.append((0.0, ship_start_x))
    
    for c in range(COLS):
        # find targets in this col (bottom up, row 6 to 0)
        col_targets = []
        for r in range(ROWS-1, -1, -1):
            intensity = grid.get((c, r), 0)
            if intensity > 0:
                col_targets.append((r, intensity))
                
        target_x = START_X + c * (SIZE + GAP)
        
        if not col_targets:
            # just fly past
            T += 0.1
            continue
            
        ship_keyframes.append((T, ship_keyframes[-1][1]))
        T += 0.2
        ship_keyframes.append((T, target_x))
        
        # Shoot targets
        for (r, intensity) in col_targets:
            target_y = START_Y + r * (SIZE + GAP)
            
            for hit in range(1, intensity + 1):
                # fire laser
                fire_time = T
                travel_time = 0.25 + (ROWS - r) * 0.02
                hit_time = fire_time + travel_time
                
                # Register laser
                laser_elements.append({
                    "x": target_x + SIZE/2 - 1,
                    "y_start": ship_y,
                    "y_end": target_y + SIZE/2,
                    "fire_time": fire_time,
                    "travel_time": travel_time
                })
                
                # Register hit on target
                if (c, r) not in target_animations:
                    target_animations[(c, r)] = []
                
                if hit < intensity:
                    target_animations[(c, r)].append({"time": hit_time, "type": "shield"})
                else:
                    target_animations[(c, r)].append({"time": hit_time, "type": "explode"})
                    
                T += 0.15 
                
        T += 0.2 
        
    # Fly off screen right
    ship_keyframes.append((T, ship_keyframes[-1][1]))
    T += 0.5
    ship_keyframes.append((T, WIDTH + 50))
    T += 2.0 
    
    T_TOTAL = T
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')
    
    # Parallax Stars
    svg.append('<defs>')
    svg.append('  <pattern id="stars1" width="200" height="200" patternUnits="userSpaceOnUse">')
    for _ in range(20):
        svg.append(f'    <circle cx="{math.floor(random.random()*200)}" cy="{math.floor(random.random()*200)}" r="0.5" fill="#fff" opacity="0.5"/>')
    svg.append('  </pattern>')
    svg.append('  <pattern id="stars2" width="300" height="300" patternUnits="userSpaceOnUse">')
    for _ in range(15):
        svg.append(f'    <circle cx="{math.floor(random.random()*300)}" cy="{math.floor(random.random()*300)}" r="1" fill="#fff" opacity="0.8"/>')
    svg.append('  </pattern>')
    svg.append('</defs>')
    
    svg.append('<style>')
    svg.append(f'@keyframes star_move {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-200px); }} }}')
    svg.append(f'@keyframes star_move2 {{ 0% {{ transform: translateX(0); }} 100% {{ transform: translateX(-300px); }} }}')
    svg.append('</style>')
    
    svg.append('<g style="animation: star_move 20s linear infinite;">')
    svg.append(f'  <rect x="0" y="0" width="{WIDTH+200}" height="{HEIGHT}" fill="url(#stars1)" />')
    svg.append('</g>')
    svg.append('<g style="animation: star_move2 15s linear infinite;">')
    svg.append(f'  <rect x="0" y="0" width="{WIDTH+300}" height="{HEIGHT}" fill="url(#stars2)" />')
    svg.append('</g>')
    
    svg.append('<style>')
    # Ship movement
    svg.append(f'@keyframes ship_move {{')
    for (t, x) in ship_keyframes:
        pct = (t / T_TOTAL) * 100
        svg.append(f'  {pct:.2f}% {{ transform: translateX({x}px); }}')
    svg.append(f'  99.99% {{ transform: translateX({ship_keyframes[-1][1]}px); }}')
    svg.append(f'  100% {{ transform: translateX({ship_start_x}px); }}')
    svg.append('}')
    
    # Target Animations
    for (c, r), events in target_animations.items():
        svg.append(f'@keyframes target_{c}_{r} {{')
        svg.append(f'  0% {{ transform: scale(1); filter: brightness(1); opacity: 1; }}')
        
        for ev in events:
            t = ev["time"]
            pct = (t / T_TOTAL) * 100
            if ev["type"] == "shield":
                svg.append(f'  {pct-0.1:.2f}% {{ transform: scale(1); filter: brightness(1); }}')
                svg.append(f'  {pct:.2f}% {{ transform: scale(1.3); filter: drop-shadow(0 0 5px #58a6ff) brightness(2); }}')
                svg.append(f'  {pct+1.5:.2f}% {{ transform: scale(1); filter: brightness(1); }}')
            elif ev["type"] == "explode":
                svg.append(f'  {pct-0.1:.2f}% {{ transform: scale(1); filter: brightness(1); opacity: 1; }}')
                svg.append(f'  {pct:.2f}% {{ transform: scale(1.8); filter: brightness(3); opacity: 1; fill: #ff7b72; }}')
                svg.append(f'  {pct+1.0:.2f}% {{ transform: scale(0); opacity: 0; }}')
                svg.append(f'  99.9% {{ transform: scale(0); opacity: 0; }}')
        
        svg.append(f'  100% {{ transform: scale(1); filter: brightness(1); opacity: 1; }}')
        svg.append('}')
    svg.append('</style>')
    
    colors = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    
    # Draw Targets
    for c in range(COLS):
        for r in range(ROWS):
            intensity = grid.get((c, r), 0)
            color = colors[min(4, intensity)]
            x = START_X + c * (SIZE + GAP)
            y = START_Y + r * (SIZE + GAP)
            
            if intensity > 0:
                svg.append(f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" fill="{color}" rx="2" style="animation: target_{c}_{r} {T_TOTAL}s linear infinite; transform-origin: {x+SIZE/2}px {y+SIZE/2}px;" />')
            else:
                svg.append(f'<rect x="{x}" y="{y}" width="{SIZE}" height="{SIZE}" fill="{color}" rx="2" />')
                
    # Draw Lasers
    svg.append('<style>')
    for i, l in enumerate(laser_elements):
        svg.append(f'@keyframes fly_{i} {{')
        start_pct = (l["fire_time"] / T_TOTAL) * 100
        end_pct = ((l["fire_time"] + l["travel_time"]) / T_TOTAL) * 100
        svg.append(f'  0%, {start_pct-0.01:.3f}% {{ transform: translateY(0); opacity: 0; }}')
        svg.append(f'  {start_pct:.3f}% {{ transform: translateY(0); opacity: 1; }}')
        svg.append(f'  {end_pct:.3f}% {{ transform: translateY({l["y_end"] - l["y_start"]}px); opacity: 1; }}')
        svg.append(f'  {end_pct+0.01:.3f}%, 100% {{ transform: translateY({l["y_end"] - l["y_start"]}px); opacity: 0; }}')
        svg.append('}')
    svg.append('</style>')
    
    for i, l in enumerate(laser_elements):
        svg.append(f'<rect x="{l["x"]}" y="{l["y_start"]}" width="2" height="8" fill="#f2cc60" rx="1" style="animation: fly_{i} {T_TOTAL}s linear infinite;" />')
        
    # Draw Ship
    ship_path = "M 0 -10 L 10 10 L 0 5 L -10 10 Z"
    svg.append(f'<g style="animation: ship_move {T_TOTAL}s linear infinite;">')
    svg.append(f'  <path d="{ship_path}" fill="#58a6ff" stroke="#1f6feb" stroke-width="1" transform="translate(0, {ship_y})" />')
    svg.append(f'  <circle cx="0" cy="{ship_y + 10}" r="3" fill="#39d353" filter="blur(2px)" />')
    svg.append('</g>')
    
    svg.append('</svg>')
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Saved {OUTPUT_FILE}, T_TOTAL={T_TOTAL:.2f}s, LASERS={len(laser_elements)}")

if __name__ == "__main__":
    main()
