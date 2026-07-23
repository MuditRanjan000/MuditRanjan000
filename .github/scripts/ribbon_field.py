import os
import json
import math
import urllib.request
from datetime import datetime

# In GitHub Actions, it reads from ${{ secrets.GH_CONTRIB_PAT }}
token = os.environ.get("GH_CONTRIB_PAT")
if not token:
    raise ValueError("GH_CONTRIB_PAT environment variable not set")

query = """
query {
  user(login: "MuditRanjan000") {
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
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Python'
    }
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
except Exception as e:
    print(f"Failed to fetch data: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())
    exit(1)

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
weeks = calendar["weeks"]

if len(weeks) == 53:
    weeks = weeks[1:]

rows_data = [[] for _ in range(7)]

col = 0
for w in weeks:
    for day in w["contributionDays"]:
        date_str = day["date"]
        count = day["contributionCount"]
        
        d = datetime.strptime(date_str, "%Y-%m-%d")
        row = (d.weekday() + 1) % 7
        rows_data[row].append((col, count))
    col += 1

def generate_bezier_path(points):
    if len(points) < 2:
        return ""
    pts = [points[0]] + points + [points[-1]]
    path = []
    path.append(f"M {points[0][0]:.2f},{points[0][1]:.2f}")
    for i in range(1, len(pts) - 2):
        p0 = pts[i-1]
        p1 = pts[i]
        p2 = pts[i+1]
        p3 = pts[i+2]
        tension = 1/6
        c1x = p1[0] + (p2[0] - p0[0]) * tension
        c1y = p1[1] + (p2[1] - p0[1]) * tension
        c2x = p2[0] - (p3[0] - p1[0]) * tension
        c2y = p2[1] - (p3[1] - p1[1]) * tension
        path.append(f"C {c1x:.2f},{c1y:.2f} {c2x:.2f},{c2y:.2f} {p2[0]:.2f},{p2[1]:.2f}")
    return " ".join(path)

WIDTH = 872
HEIGHT = 200
PITCH_X = 16
PITCH_Y = 20

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
svg.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117" rx="8" />')

svg.append('<defs>')
colors = [
    ("#39d353", "#26a641"),
    ("#26a641", "#006d32"),
    ("#006d32", "#0e4429"),
    ("#39d353", "#0e4429"),
    ("#26a641", "#39d353"),
    ("#006d32", "#26a641"),
    ("#0e4429", "#39d353")
]
for i, (c1, c2) in enumerate(colors):
    svg.append(f'  <linearGradient id="ribbon-{i}" x1="0%" y1="0%" x2="100%" y2="0%">')
    svg.append(f'    <stop offset="0%" stop-color="{c1}" />')
    svg.append(f'    <stop offset="100%" stop-color="{c2}" />')
    svg.append(f'  </linearGradient>')

svg.append('  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">')
svg.append('    <feGaussianBlur stdDeviation="2" result="blur" />')
svg.append('    <feMerge>')
svg.append('      <feMergeNode in="blur" />')
svg.append('      <feMergeNode in="SourceGraphic" />')
svg.append('    </feMerge>')
svg.append('  </filter>')
svg.append('</defs>')

off_x = 20
off_y = 40
max_amplitude = 18.0
max_capped_count = 15

# Precalculate the point characteristics for each row
for r in range(7):
    row_points_data = []
    for col, count in rows_data[r]:
        x = off_x + col * PITCH_X
        if count == 0:
            amp = 0
        else:
            ratio = min(count / max_capped_count, 1.0)
            amp = (ratio ** 0.6) * max_amplitude
        base_y = off_y + r * PITCH_Y
        row_points_data.append((col, count, x, base_y, amp))
        
    # Generate exactly 5 identical structural phases (0 to 1 full phase)
    phases = []
    for p in range(5):
        t = p / 4.0  # 0.0, 0.25, 0.5, 0.75, 1.0
        phase_offset = t * 2 * math.pi
        
        # Apply sinusoidal wave vertically
        phased_pts = []
        for (col, count, x, base_y, amp) in row_points_data:
            if amp == 0:
                y = base_y
            else:
                # Travel wave: 1 full wave across 52 columns
                wave = math.sin(phase_offset + (col / 52.0) * math.pi * 2)
                # Modulate amplitude by ±20%
                current_amp = amp * (1.0 + wave * 0.20)
                y = base_y - current_amp
            phased_pts.append((x, y))
            
        phases.append(generate_bezier_path(phased_pts))
        
    opacity = 0.8 + (r % 2) * 0.2
    stroke_width = 2.5
    
    val_str = "; ".join(phases)
    
    svg.append(f'  <path d="{phases[0]}" fill="none" stroke="url(#ribbon-{r})" stroke-width="{stroke_width}" opacity="{opacity}" filter="url(#glow)" stroke-linecap="round">')
    svg.append(f'    <animate attributeName="d" values="{val_str}" dur="30s" repeatCount="indefinite" />')
    svg.append('  </path>')
    
svg.append('</svg>')

with open("ribbon_field.svg", "w", encoding="utf-8") as f:
    f.write('\n'.join(svg))
print(f"Saved ribbon_field.svg")
