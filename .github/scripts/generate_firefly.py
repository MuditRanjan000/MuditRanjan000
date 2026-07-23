import os
import json
import math
import urllib.request
from datetime import datetime

# GitHub GraphQL API Setup
pat = os.environ.get("GH_CONTRIB_PAT") or os.environ.get("GITHUB_TOKEN")
if not pat:
    raise ValueError("GH_CONTRIB_PAT or GITHUB_TOKEN environment variable is required")

query = """
query {
  viewer {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""

req = urllib.request.Request(
    'https://api.github.com/graphql',
    data=json.dumps({'query': query}).encode('utf-8'),
    headers={
        'Authorization': f'Bearer {pat}',
        'Content-Type': 'application/json',
        'User-Agent': 'Python'
    }
)

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode())

if "errors" in result:
    raise ValueError(f"GraphQL Error: {result['errors']}")

calendar = result["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]

# Only take the last 52 weeks to form a clean grid
if len(weeks) == 53:
    weeks = weeks[1:]

rows_data = [[] for _ in range(7)]
all_counts = []
col = 0
for w in weeks:
    for day in w["contributionDays"]:
        date_str = day["date"]
        count = day["contributionCount"]
        if count > 0:
            all_counts.append(count)
        d = datetime.strptime(date_str, "%Y-%m-%d")
        row = (d.weekday() + 1) % 7
        rows_data[row].append({"col": col, "count": count, "date": date_str})
    col += 1

all_counts.sort()
if not all_counts:
    quartiles = [1, 2, 3, 4]
else:
    q1 = all_counts[len(all_counts) // 4]
    q2 = all_counts[len(all_counts) // 2]
    q3 = all_counts[(len(all_counts) * 3) // 4]
    quartiles = [
        max(1, q1),
        max(2, q2),
        max(3, q3),
        all_counts[-1]
    ]

def get_color(count):
    if count == 0: return "#161b22"
    elif count <= quartiles[0]: return "#0e4429"
    elif count <= quartiles[1]: return "#006d32"
    elif count <= quartiles[2]: return "#26a641"
    else: return "#39d353"

# SVG generation logic
WIDTH = 52 * 16 + 40
HEIGHT = 7 * 16 + 40
PITCH = 16
off_x = 20
off_y = 20

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">']
svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')

# Flatten rows into a chronological 1D list of cells
cells = []
for c in range(52):
    for r in range(7):
        if c < len(rows_data[r]):
            cell = rows_data[r][c]
            cells.append({
                "col": c,
                "row": r,
                "x": off_x + c * PITCH,
                "y": off_y + r * PITCH,
                "count": cell["count"],
                "date": cell["date"]
            })

total_cells = len(cells)
hop_time = 0.05  # Faster hops for 364 cells
max_count = quartiles[-1] if quartiles[-1] > 0 else 1

current_time = 0.0
for i, cell in enumerate(cells):
    if i > 0:
        current_time += hop_time
    
    # Exaggerated Pacing: map count to pause (0s to 0.1s for 364 cells)
    c_pause = 0.0 if cell["count"] == 0 else 0.02 + (cell["count"] / max_count) * 0.08
    cell["arrival_time"] = current_time
    current_time += c_pause

total_duration = current_time + 2.0  # +2s full board pause

cell_arrival_times = []
motion_key_times = []
translate_values = []
motion_key_splines = []

current_time = 0.0

for i, cell in enumerate(cells):
    x, y = cell["x"] + 6, cell["y"] + 6
    
    if i == 0:
        motion_key_times.append(0.0)
        translate_values.append(f"{x},{y}")
        cell_arrival_times.append(0.0)
    else:
        # Hop
        px, py = cells[i-1]["x"] + 6, cells[i-1]["y"] + 6
        dx = x - px
        dy = y - py
        dist = math.hypot(dx, dy)
        if dist == 0: dist = 1
        
        mx, my = px + dx / 2, py + dy / 2
        nx, ny = -dy / dist, dx / dist
        arc_h = 10 if dx > 0 else 5  # smaller arc for short jumps down columns
        qx, qy = mx + nx * arc_h, my + ny * arc_h
        
        # Midpoint of hop
        mid_time = current_time + hop_time / 2
        motion_key_times.append(mid_time / total_duration)
        translate_values.append(f"{qx:.1f},{qy:.1f}")
        motion_key_splines.append("0.42 0.0 0.58 1.0") # ease-in-out
        
        # End of hop (Arrival)
        current_time += hop_time
        t = current_time / total_duration
        motion_key_times.append(t)
        translate_values.append(f"{x},{y}")
        cell_arrival_times.append(t)
        motion_key_splines.append("0.42 0.0 0.58 1.0")
        
    # Pause
    c_pause = 0.0 if cell["count"] == 0 else 0.02 + (cell["count"] / max_count) * 0.08
    current_time += c_pause
    t = current_time / total_duration
    motion_key_times.append(t)
    translate_values.append(f"{x},{y}")
    if len(motion_key_times) > 1:
        motion_key_splines.append("1.0 0.0 1.0 1.0")

while len(motion_key_splines) >= len(motion_key_times):
    motion_key_splines.pop()

# Final hold
motion_key_times.append(1.0)
translate_values.append(f'{cells[-1]["x"] + 6},{cells[-1]["y"] + 6}')
motion_key_splines.append("1.0 0.0 1.0 1.0")

for i, c in enumerate(cells):
    x = c["x"]
    y = c["y"]
    
    lit_color = get_color(c["count"])
    if lit_color == "#161b22":
        svg.append(f'<rect x="{x}" y="{y}" width="12" height="12" fill="#161b22" rx="2" />')
        continue
        
    svg.append(f'<rect x="{x}" y="{y}" width="12" height="12" fill="#161b22" rx="2">')
    
    arrival_t = cell_arrival_times[i]
    fade_t = (total_duration - 1.0) / total_duration
    pre_arrival = max(0.0, arrival_t - 0.001)
    
    if arrival_t == 0.0:
        kt = f"0; {fade_t:.5f}; {fade_t+0.01:.5f}; 1"
        kv_fill = f"{lit_color}; {lit_color}; #161b22; #161b22"
    else:
        kt = f"0; {pre_arrival:.5f}; {arrival_t:.5f}; {fade_t:.5f}; {fade_t+0.01:.5f}; 1"
        kv_fill = f"#161b22; #161b22; {lit_color}; {lit_color}; #161b22; #161b22"
        
    svg.append(f'  <animate attributeName="fill" values="{kv_fill}" keyTimes="{kt}" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
    
    # Tactile Cells: Pop animation
    pop_t = min(1.0, arrival_t + 0.1/total_duration)
    if arrival_t == 0.0:
        kt_pop = f"0; {pop_t:.5f}; 1"
        kv_w = f"14; 12; 12"
        kv_h = f"14; 12; 12"
        kv_x = f"{x-1}; {x}; {x}"
        kv_y = f"{y-1}; {y}; {y}"
    else:
        kt_pop = f"0; {pre_arrival:.5f}; {arrival_t:.5f}; {pop_t:.5f}; 1"
        kv_w = f"12; 12; 14; 12; 12"
        kv_h = f"12; 12; 14; 12; 12"
        kv_x = f"{x}; {x}; {x-1}; {x}; {x}"
        kv_y = f"{y}; {y}; {y-1}; {y}; {y}"
        
    svg.append(f'  <animate attributeName="width" values="{kv_w}" keyTimes="{kt_pop}" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
    svg.append(f'  <animate attributeName="height" values="{kv_h}" keyTimes="{kt_pop}" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
    svg.append(f'  <animate attributeName="x" values="{kv_x}" keyTimes="{kt_pop}" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
    svg.append(f'  <animate attributeName="y" values="{kv_y}" keyTimes="{kt_pop}" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
    
    svg.append(f'</rect>')

kt_str = ";".join(f"{kt:.5f}" for kt in motion_key_times)
trans_str = ";".join(translate_values)
splines_str = ";".join(motion_key_splines)

svg.append(f'<g>')
svg.append(f'  <animateTransform attributeName="transform" type="translate" values="{trans_str}" keyTimes="{kt_str}" keySplines="{splines_str}" calcMode="spline" dur="{total_duration:.1f}s" repeatCount="indefinite" />')
svg.append(f'  <g>')

bounce_kt = []
bounce_kv = []
for i in range(total_cells):
    arr_pct = cell_arrival_times[i]
    pre_arr = max(0.0, arr_pct - 0.001)
    
    if arr_pct > 0.0:
        bounce_kt.append(f"{pre_arr:.5f}")
        bounce_kv.append("1")
        
    bounce_kt.append(f"{arr_pct:.5f}")
    bounce_kv.append("0.5")
    
    stretch_t = min(1.0, arr_pct + 0.05/total_duration)
    bounce_kt.append(f"{stretch_t:.5f}")
    bounce_kv.append("1.5")
    
    settle_t = min(1.0, arr_pct + 0.1/total_duration)
    bounce_kt.append(f"{settle_t:.5f}")
    bounce_kv.append("1")

bounce_kt.append("1")
bounce_kv.append("1")

svg.append(f'    <animateTransform attributeName="transform" type="scale" values="{";".join(bounce_kv)}" keyTimes="{";".join(bounce_kt)}" dur="{total_duration:.1f}s" repeatCount="indefinite" additive="sum" />')
svg.append(f'    <circle cx="0" cy="0" r="6" fill="#7ee787" opacity="0.4" />')
svg.append(f'    <circle cx="0" cy="0" r="2.5" fill="#7ee787" />')
svg.append(f'  </g>')
svg.append(f'</g>')
svg.append('</svg>')

with open("github-contribution-firefly.svg", "w", encoding="utf-8") as f:
    f.write('\n'.join(svg))
print("Generated github-contribution-firefly.svg")
