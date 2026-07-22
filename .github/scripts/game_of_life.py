import urllib.request
import json
from datetime import datetime, timedelta
import os
from PIL import Image, ImageDraw

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-game-of-life.gif"

def fetch_contributions(username):
    url = f"https://github-contributions.vercel.app/api/v1/{username}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    return data["contributions"]

def build_grid(contributions):
    # Sort contributions by date ascending
    conts = sorted(contributions, key=lambda x: x["date"])
    # Get last 364 days (52 weeks)
    conts = conts[-364:]
    
    # 52 columns, 7 rows
    grid = [[0 for _ in range(52)] for _ in range(7)]
    
    for i, c in enumerate(conts):
        col = i // 7
        row = i % 7
        intensity = int(c.get("intensity", 0))
        grid[row][col] = 1 if intensity > 0 else 0
        
    return grid

def step_game_of_life(grid):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [[0 for _ in range(cols)] for _ in range(rows)]
    
    for r in range(rows):
        for c in range(cols):
            alive_neighbors = 0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        alive_neighbors += grid[nr][nc]
            
            if grid[r][c] == 1:
                if alive_neighbors in [2, 3]:
                    new_grid[r][c] = 1
            else:
                if alive_neighbors == 3:
                    new_grid[r][c] = 1
                    
    return new_grid

def render_frame(grid, cell_size=12, padding=2):
    rows = len(grid)
    cols = len(grid[0])
    
    width = cols * (cell_size + padding) + padding
    height = rows * (cell_size + padding) + padding
    
    # Dark mode background
    img = Image.new('RGB', (width, height), color='#0d1117')
    draw = ImageDraw.Draw(img)
    
    for r in range(rows):
        for c in range(cols):
            x = padding + c * (cell_size + padding)
            y = padding + r * (cell_size + padding)
            
            # Draw cell
            color = '#39d353' if grid[r][c] == 1 else '#161b22'
            
            # Pillow doesn't have native rounded rectangles in old versions, but we can draw a normal rect
            draw.rectangle([x, y, x + cell_size - 1, y + cell_size - 1], fill=color, outline='#0d1117')
            
    return img

def main():
    print(f"Fetching contributions for {USERNAME}...")
    contributions = fetch_contributions(USERNAME)
    
    print("Building grid...")
    grid = build_grid(contributions)
    
    frames = []
    print("Simulating Game of Life...")
    for i in range(60): # 60 frames of animation
        img = render_frame(grid)
        frames.append(img)
        grid = step_game_of_life(grid)
        
    print(f"Saving GIF to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=150, # 150ms per frame
        loop=0
    )
    print("Done!")

if __name__ == "__main__":
    main()
