import urllib.request
import json
import math
import random
import os
from PIL import Image, ImageDraw

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-flow.gif"
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

def build_commit_grid(contributions):
    if not contributions:
        return [[0]*52 for _ in range(7)]
    conts = sorted(contributions, key=lambda x: x["date"])[-364:]
    grid = [[0 for _ in range(52)] for _ in range(7)]
    for i, c in enumerate(conts):
        col = i // 7
        row = i % 7
        grid[row][col] = int(c.get("intensity", 0))
    return grid

# Beautiful cyberpunk / synthwave colors driven by commit intensity
COLORS = {
    0: (20, 20, 40),      # Very dark blue-grey for empty
    1: (0, 150, 255),     # Cyan
    2: (0, 255, 150),     # Mint Green
    3: (255, 200, 0),     # Golden Yellow
    4: (255, 50, 100)     # Neon Pink
}

class Particle:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)
        self.speed = random.uniform(1.5, 3.5)
        # Random initial angle to avoid clumping
        self.angle_offset = random.uniform(0, math.pi * 2)

def main():
    print(f"Fetching data for {USERNAME}...")
    contribs = fetch_contributions(USERNAME)
    grid = build_commit_grid(contribs)
    
    print("Initializing particles...")
    # Dense particle field for a lush, fluid look
    particles = [Particle() for _ in range(3000)]
    
    canvas = Image.new('RGB', (WIDTH, HEIGHT), (10, 10, 15))
    fade_img = Image.new('RGB', (WIDTH, HEIGHT), (10, 10, 15))
    
    frames = []
    
    print("Simulating physics flow field...")
    # Pre-warm the simulation so trails are already flowing
    for _ in range(30):
        for p in particles:
            col = min(51, max(0, int((p.x / WIDTH) * 52)))
            row = min(6, max(0, int((p.y / HEIGHT) * 7)))
            intensity = grid[row][col]
            
            time_factor = 30 * 0.03
            noise1 = math.sin(p.x * 0.01 + time_factor) + math.cos(p.y * 0.01 - time_factor)
            noise2 = math.sin(p.y * 0.02) * math.cos(p.x * 0.02)
            angle = noise1 + noise2 + (intensity * 0.6) + p.angle_offset
            
            current_speed = p.speed * (1.0 + intensity * 0.4)
            p.x += math.cos(angle) * current_speed
            p.y += math.sin(angle) * current_speed
            
            if p.x < 0: p.x += WIDTH
            if p.x > WIDTH: p.x -= WIDTH
            if p.y < 0: p.y += HEIGHT
            if p.y > HEIGHT: p.y -= HEIGHT
            
    # Record frames
    for frame_idx in range(60): # 60 frames for a smooth 3s loop
        # Buttery smooth fading trail effect (motion blur)
        canvas = Image.blend(canvas, fade_img, alpha=0.15)
        draw = ImageDraw.Draw(canvas)
        
        for p in particles:
            # Map position to commit grid
            col = min(51, max(0, int((p.x / WIDTH) * 52)))
            row = min(6, max(0, int((p.y / HEIGHT) * 7)))
            intensity = grid[row][col]
            
            time_factor = (frame_idx + 30) * 0.03
            
            # Pure math pseudo-noise for absolute cross-platform stability
            noise1 = math.sin(p.x * 0.01 + time_factor) + math.cos(p.y * 0.01 - time_factor)
            noise2 = math.sin(p.y * 0.02) * math.cos(p.x * 0.02)
            
            angle = noise1 + noise2 + (intensity * 0.6) + p.angle_offset
            current_speed = p.speed * (1.0 + intensity * 0.4)
            
            vx = math.cos(angle) * current_speed
            vy = math.sin(angle) * current_speed
            
            old_x, old_y = p.x, p.y
            p.x += vx
            p.y += vy
            
            # Wrap around smoothly without drawing a long line across the screen
            wrapped = False
            if p.x < 0: p.x += WIDTH; wrapped = True
            if p.x > WIDTH: p.x -= WIDTH; wrapped = True
            if p.y < 0: p.y += HEIGHT; wrapped = True
            if p.y > HEIGHT: p.y -= HEIGHT; wrapped = True
            
            color = COLORS.get(intensity, COLORS[0])
            if not wrapped:
                draw.line([(old_x, old_y), (p.x, p.y)], fill=color, width=2)
            
        frames.append(canvas.copy())
        
    print(f"Saving GIF to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        optimize=False, # preserve smooth alpha blend trails
        duration=50, # 20fps for buttery smoothness
        loop=0
    )
    print("Done!")

if __name__ == "__main__":
    main()
