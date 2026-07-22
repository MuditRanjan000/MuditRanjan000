import urllib.request
import json
from datetime import datetime
import os
import random
from PIL import Image, ImageDraw, ImageFont

USERNAME = os.environ.get("GITHUB_USERNAME", "MuditRanjan000")
OUTPUT_FILE = "dist/github-contribution-matrix.gif"

def fetch_contributions(username):
    url = f"https://github-contributions.vercel.app/api/v1/{username}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    return data["contributions"]

def build_commit_grid(contributions):
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
        self.rows = 28
        # Using Katakana and some symbols to simulate the Matrix effect
        self.chars = [chr(i) for i in range(0x30A0, 0x30FF)] + list("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*")
        
        # Expand commit grid to 104x14
        self.mask = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        for r in range(7):
            for c in range(52):
                intensity = commit_grid[r][c]
                # place in middle vertically
                mr = r * 2 + 7
                mc = c * 2
                self.mask[mr][mc] = intensity
                self.mask[mr+1][mc] = intensity
                self.mask[mr][mc+1] = intensity
                self.mask[mr+1][mc+1] = intensity
                
        self.grid_chars = [[random.choice(self.chars) for _ in range(self.cols)] for _ in range(self.rows)]
        self.grid_bright = [[0.0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        self.droplets = []
        for c in range(self.cols):
            if random.random() < 0.6:
                self.droplets.append({'c': c, 'y': random.uniform(-20, self.rows), 'speed': random.uniform(0.5, 1.5)})

    def step(self):
        # randomly change some chars
        for _ in range(100):
            r = random.randint(0, self.rows-1)
            c = random.randint(0, self.cols-1)
            self.grid_chars[r][c] = random.choice(self.chars)
            
        # decay brightness
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid_bright[r][c] *= 0.85
                
        # move droplets
        for d in self.droplets:
            d['y'] += d['speed']
            head = int(d['y'])
            if 0 <= head < self.rows:
                self.grid_bright[head][d['c']] = 1.0
            
            if d['y'] > self.rows + 10:
                d['y'] = random.uniform(-10, -1)
                d['speed'] = random.uniform(0.5, 1.5)

    def render(self):
        cell_w, cell_h = 10, 14
        img = Image.new('RGB', (self.cols * cell_w, self.rows * cell_h), color='#0d1117')
        draw = ImageDraw.Draw(img)
        
        # Load a default font for Ubuntu runners, since they usually have standard fonts
        try:
            # For linux runner
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 12)
        except:
            font = ImageFont.load_default()
            
        for r in range(self.rows):
            for c in range(self.cols):
                intensity = self.mask[r][c]
                base_b = intensity * 0.15 # Baseline glow for commits
                
                b = max(self.grid_bright[r][c], base_b)
                if b <= 0.05:
                    continue
                
                if self.grid_bright[r][c] > 0.9:
                    color = (255, 255, 255)
                else:
                    g = int(255 * min(1.0, b * 1.5))
                    color = (0, g, 0)
                
                char = self.grid_chars[r][c]
                # Filter out katakana if we are using the default PIL font which can't render it
                if font.getname()[0] == 'Default' and ord(char) > 127:
                    char = random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*")
                
                # If inside a commit block, tint it slightly brighter and greener
                if intensity > 0 and self.grid_bright[r][c] < 0.3:
                    color = (0, int(150 + 25*intensity), 0)
                
                draw.text((c * cell_w, r * cell_h), char, font=font, fill=color)
                
        return img

def main():
    print(f"Fetching contributions for {USERNAME}...")
    contribs = fetch_contributions(USERNAME)
    grid = build_commit_grid(contribs)
    
    matrix = MatrixRain(grid)
    
    # Pre-simulate a bit to fill the screen
    for _ in range(40):
        matrix.step()
        
    frames = []
    print("Rendering frames...")
    for i in range(60): # 60 frames
        frames.append(matrix.render())
        matrix.step()
        
    print(f"Saving GIF to {OUTPUT_FILE}...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        duration=100,
        loop=0
    )
    print("Done")

if __name__ == "__main__":
    main()
