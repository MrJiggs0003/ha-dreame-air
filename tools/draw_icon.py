"""Draw the Dreame Air icon: a tower air purifier with a round fan grille."""

import math
import sys

from PIL import Image, ImageDraw

out = sys.argv[1]  # for example custom_components/dreame_air/brand
N = 2048
img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
TEAL = (14, 150, 160, 255)
DEEP = (10, 112, 122, 255)
LIGHT = (255, 255, 255, 255)
AIR = (125, 211, 252, 255)
CLEAR = (0, 0, 0, 0)
cx = N // 2

# Body.
d.rounded_rectangle((424, 120, 1624, 1928), radius=260, fill=TEAL)
# Fan: a ring with curved blades around a hub, top of the body.
fy = 640
d.ellipse((cx - 430, fy - 430, cx + 430, fy + 430), fill=LIGHT)
d.ellipse((cx - 370, fy - 370, cx + 370, fy + 370), fill=DEEP)
for k in range(5):
    a = 2 * math.pi * k / 5
    pts = []
    # Each blade: a teardrop swept from the hub toward the rim.
    for j in range(41):
        t = j / 40
        r = 70 + 270 * t
        sweep = 0.9 * t
        width = 0.55 * math.sin(math.pi * t) + 0.06
        pts.append((r, a + sweep + width / 2))
    for j in range(40, -1, -1):
        t = j / 40
        r = 70 + 270 * t
        sweep = 0.9 * t
        width = 0.55 * math.sin(math.pi * t) + 0.06
        pts.append((r, a + sweep - width / 2 * 0.3))
    d.polygon([(cx + r * math.cos(th), fy + r * math.sin(th)) for r, th in pts], fill=AIR)
d.ellipse((cx - 95, fy - 95, cx + 95, fy + 95), fill=LIGHT)
# Vent slots, lower body.
for i in range(5):
    y = 1240 + i * 130
    d.rounded_rectangle((cx - 420, y, cx + 420, y + 64), radius=32, fill=DEEP)
# Base.
d.rounded_rectangle((424, 1860, 1624, 1928), radius=34, fill=DEEP)

box = img.getbbox()
img = img.crop(box)
side = int(max(img.size) * 1.04)
sq = Image.new("RGBA", (side, side), CLEAR)
sq.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
for size, name in ((256, "icon.png"), (512, "icon@2x.png")):
    sq.resize((size, size), Image.LANCZOS).save(f"{out}/{name}", optimize=True)
