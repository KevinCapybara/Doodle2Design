"""Generate 100 original procedural references, offline and reproducibly."""
import math
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ("architecture", "landscapes", "textures", "patterns")
PALETTES = [
    ("midnight", "#111726", "#38516b", "#c4def1"),
    ("terracotta", "#edd7ba", "#b26449", "#452c29"),
    ("sage", "#dbe2cd", "#788d6e", "#283c32"),
    ("electric", "#141224", "#9c6ae8", "#f2ff74"),
    ("paper", "#f4efe3", "#cac4b8", "#5a5650"),
    ("ocean", "#c6e4e8", "#428793", "#173c53"),
    ("rose", "#f5dbe0", "#b7869a", "#4e3448"),
    ("cobalt", "#e2e6ef", "#4257c9", "#171d4d"),
    ("amber", "#1e2320", "#b59458", "#eed5a0"),
    ("sunlit", "#fff1cf", "#e2ab63", "#a45838"),
]


def make_image(category, index):
    rng = random.Random(f"{category}-{index}")
    name, bg, mid, fg = PALETTES[index % len(PALETTES)]
    w, h = 800, 600
    image = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(image)
    if category == "architecture":
        # Facades, colonnades and monumental archways.
        draw.rectangle((0, 450, w, h), fill=mid)
        style = index % 3
        if style == 0:
            for n in range(5):
                x, y = 90 + n * 122, 100 + n * 26
                draw.polygon([(x, y), (x+120, y-45), (x+120, 490), (x, 530)], fill=mid if n % 2 else fg)
                draw.line((x+25, y+30, x+25, 465), fill=bg, width=3)
        elif style == 1:
            for n in range(4):
                x = 40 + n * 205
                draw.rounded_rectangle((x, 70, x+150, 540), radius=75, fill=fg)
                draw.rounded_rectangle((x+23, 105, x+127, 550), radius=52, fill=mid)
                draw.rectangle((x+23, 310, x+127, 550), fill=mid)
        else:
            draw.polygon([(80, 210), (510, 60), (740, 200), (310, 350)], fill=fg)
            draw.polygon([(80, 210), (310, 350), (310, 570), (80, 430)], fill=mid)
            draw.polygon([(310, 350), (740, 200), (740, 430), (310, 570)], fill=mid)
            for n in range(7):
                x = 340+n*52
                draw.line((x, 355-(n*18), x, 535-(n*17)), fill=bg, width=18)
    elif category == "landscapes":
        sun = (580, 160) if index % 2 else (210, 180)
        draw.ellipse((sun[0]-70, sun[1]-70, sun[0]+70, sun[1]+70), fill=fg)
        for layer in range(5):
            y = 250 + layer*70
            points = [(0, h)] + [(x, y + math.sin(x/160+layer)*45 + rng.randrange(-15, 15)) for x in range(0, 821, 40)] + [(w, h)]
            draw.polygon(points, fill=(mid if layer % 2 == 0 else fg))
        if index % 3 == 0:
            for n in range(14):
                x = rng.randrange(w)
                y = rng.randrange(330, 550)
                draw.polygon([(x, y-150), (x-45, y), (x+45, y)], fill=bg)
    elif category == "textures":
        # Low resolution seeded noise upscaled to produce tactile surfaces.
        noise = Image.new("RGB", (200, 150), bg)
        nd = ImageDraw.Draw(noise)
        for y in range(150):
            for x in range(200):
                if rng.random() < .35:
                    nd.point((x, y), fill=mid)
        noise = noise.resize((w, h)).filter(ImageFilter.GaussianBlur(1.3))
        image = Image.blend(image, noise, .55)
        draw = ImageDraw.Draw(image)
        for n in range(90):
            y = n*9
            points = [(x, y+math.sin(x/100+n/6)*20) for x in range(0, 820, 10)]
            if index % 2:
                points = [(y+math.sin(x/90+n)*15, x) for x in range(0, 620, 10)]
            draw.line(points, fill=mid, width=1 if index % 3 else 3)
        if index % 4 == 0:
            for n in range(8):
                x = rng.randrange(w)
                draw.line([(x, 0), (x+60, 200), (x-30, 420), (x+100, 600)], fill=fg, width=2)
    else:
        style = index % 5
        for y in range(-80, h+100, 100):
            for x in range(-80, w+100, 100):
                if style == 0 and (x+y)//100 % 2:
                    draw.rectangle((x, y, x+100, y+100), fill=fg)
                elif style == 1:
                    draw.ellipse((x+25, y+25, x+65, y+65), fill=mid)
                elif style == 2:
                    draw.arc((x, y, x+180, y+180), 0, 300, fill=fg, width=12)
                elif style == 3:
                    draw.polygon([(x+50,y), (x+100,y+50), (x+50,y+100), (x,y+50)], fill=mid)
                elif style == 4:
                    draw.line((x, y, x+100, y+100), fill=fg, width=3)
                    draw.line((x, y+100, x+100, y), fill=mid, width=3)
    return image, name


def generate(root=ROOT):
    library = Path(root) / "images/library"
    if any(file.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} for file in library.rglob("*")):
        return
    for category in CATEGORIES:
        folder = library / category
        folder.mkdir(parents=True, exist_ok=True)
        for index in range(25):
            image, name = make_image(category, index)
            image.save(folder / f"{name}_{index+1:02d}.jpg", quality=88)
    print("Generated 100 original procedural reference images.")


if __name__ == "__main__":
    generate()
