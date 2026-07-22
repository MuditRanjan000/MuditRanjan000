import urllib.request
import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-matrix.gif"

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
        return [[0]*52]*7
    conts = sorted(contributions, key=lambda x: x["date"])[-364:]
    grid = [[0 for _ in range(52)] for _ in range(7)]
    for i, c in enumerate(conts):
        col = i // 7
        row = i % 7
        grid[row][col] = int(c.get("intensity", 0))
    return grid

class MatrixRain:
    def __init__(self, commit_grid):
        self.cols = 104
        self.rows = 30
        
        # Hacker ASCII aesthetics
        self.chars = list("0123456789ABCDEF!@#$%^&*+=?|<>")
        
        # Expand commit grid to 104x14
        self.mask = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(7):
            for c in range(52):
                intensity = commit_grid[r][c]
                # place in middle vertically (offset by 8 rows to center it in 30 rows)
                mr = r * 2 + 8
                mc = c * 2
                self.mask[mr][mc] = intensity
                self.mask[mr+1][mc] = intensity
                self.mask[mr][mc+1] = intensity
                self.mask[mr+1][mc+1] = intensity
                
        self.grid_chars = [[random.choice(self.chars) for _ in range(self.cols)] for _ in range(self.rows)]
        self.grid_bright = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.droplets = []
        for c in range(self.cols):
            # More droplets, creating dense rain
            if random.random() < 0.7:
                self.droplets.append({'c': c, 'y': random.uniform(-30, self.rows), 'speed': random.uniform(0.4, 1.2)})

    def step(self):
        # randomly change some chars for flickering effect
        for _ in range(150):
            r = random.randint(0, self.rows-1)
            c = random.randint(0, self.cols-1)
            self.grid_chars[r][c] = random.choice(self.chars)
            
        # decay brightness (slower decay = longer trails)
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid_bright[r][c] *= 0.88
                
        # move droplets
        for d in self.droplets:
            d['y'] += d['speed']
            head = int(d['y'])
            if 0 <= head < self.rows:
                self.grid_bright[head][d['c']] = 1.0
            
            # Reset droplet once it's off-screen
            if d['y'] > self.rows + 15:
                d['y'] = random.uniform(-15, -1)
                d['speed'] = random.uniform(0.4, 1.2)

    def render(self):
        cell_w, cell_h = 12, 16
        img = Image.new('RGB', (self.cols * cell_w, self.rows * cell_h), color='#0d1117')
        draw = ImageDraw.Draw(img)
        
        try:
            # We will use the custom downloaded font for thick hacker aesthetic
            font = ImageFont.truetype("matrix_font.ttf", 16)
        except:
            font = ImageFont.load_default()
            
        for r in range(self.rows):
            for c in range(self.cols):
                intensity = self.mask[r][c]
                
                # Base background color for the commit graph (glowing dark green)
                if intensity > 0:
                    # Renders a subtle green block underneath the characters
                    bg_col = (0, 15 + 25 * intensity, 0)
                    draw.rectangle(
                        [c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h],
                        fill=bg_col
                    )
                
                b = self.grid_bright[r][c]
                
                # If there's no brightness from droplets, just draw dark green ghost commits
                if b <= 0.05 and intensity == 0:
                    continue
                
                # Brightness handling
                if b > 0.9:
                    color = (255, 255, 255) # White head of droplet
                elif b > 0.05:
                    # Neon green trails
                    g = int(255 * min(1.0, b * 1.5))
                    color = (0, g, 0)
                else:
                    # Very dim background green for commits without rain
                    color = (0, 60 + 20 * intensity, 0)
                
                char = self.grid_chars[r][c]
                
                # If rain hits a commit, make the character glow intensely
                if intensity > 0 and b > 0.1:
                    color = (150, 255, 150)
                
                draw.text((c * cell_w, r * cell_h - 2), char, font=font, fill=color)
                
        return img

def main():
    print(f"Fetching contributions for {USERNAME}...")
    contribs = fetch_contributions(USERNAME)
    grid = build_commit_grid(contribs)
    
    matrix = MatrixRain(grid)
    
    # Pre-simulate so the screen is already full of rain when the GIF starts
    for _ in range(60):
        matrix.step()
        
    frames = []
    print("Rendering frames...")
    # 60 frames = 3 seconds at 20fps
    for i in range(60):
        frames.append(matrix.render())
        matrix.step()
        
    print(f"Saving GIF to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=50, # faster 20fps
        loop=0
    )
    print("Done")

if __name__ == "__main__":
    main()
