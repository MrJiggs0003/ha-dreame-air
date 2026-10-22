"""Social preview for the GitHub repo: 1280x640, icon on the left, name on the right."""

import sys

from PIL import Image, ImageDraw, ImageFont

# Arguments: brand/icon@2x.png, a folder with inter-700.ttf and inter-400.ttf (Inter, OFL), output path.
icon_path, fonts, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1280, 640
img = Image.new("RGBA", (W, H), (244, 250, 250, 255))
d = ImageDraw.Draw(img)
# Soft teal band on the left behind the icon.
d.rounded_rectangle((64, 64, 576, 576), radius=64, fill=(214, 237, 238, 255))
icon = Image.open(icon_path).convert("RGBA").resize((400, 400), Image.LANCZOS)
img.alpha_composite(icon, (120, 120))

bold = ImageFont.truetype(f"{fonts}/inter-700.ttf", 96)
reg = ImageFont.truetype(f"{fonts}/inter-400.ttf", 38)
small = ImageFont.truetype(f"{fonts}/inter-400.ttf", 30)
x = 640
d.text((x, 190), "Dreame Air", font=bold, fill=(15, 40, 45, 255))
d.text((x, 318), "Home Assistant integration", font=reg, fill=(40, 70, 75, 255))
d.text((x, 368), "for Dreame air purifiers", font=reg, fill=(40, 70, 75, 255))
d.text((x, 452), "Unofficial  ·  Open source  ·  HACS", font=small, fill=(10, 112, 122, 255))
img.convert("RGB").save(out, optimize=True)
