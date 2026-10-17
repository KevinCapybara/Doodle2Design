"""Deterministic, image-derived offline inference. No network or arbitrary CSS."""
import colorsys
from backend.imaging import image_stats, fix_contrast
from backend.schemas import BaselineProfile, VibeTokens


def color(h, s, v):
    return "#" + "".join(f"{round(c*255):02x}" for c in colorsys.hsv_to_rgb(h % 1, max(0, min(s, 1)), max(0, min(v, 1))))


def baseline_profile(images):
    s = image_stats(images)
    dark, sharp = s["brightness"] < .48, s["edge"] > .075
    vivid = s["saturation"] > .3
    palette = s["colors"]
    if len(palette) < 2:
        palette = palette + [color(s["hue"], .2, .85 if dark else .2)]
    return BaselineProfile(
        summary=f"{'A moody' if dark else 'A light-filled'}, {'structured' if sharp else 'soft'} aesthetic with {'expressive color' if vivid else 'a quiet palette'}.",
        attributes=["dark mode" if dark else "light mode", "sharp edges" if sharp else "organic", "vivid" if vivid else "minimal", "high contrast" if sharp else "gentle contrast"],
        dominant_colors=palette,
        mood_words=["dramatic" if dark else "open", "precise" if sharp else "calm", "energetic" if vivid else "grounded"],
        preferred_categories=["architecture", "patterns", "textures", "landscapes"] if sharp else ["landscapes", "textures", "architecture", "patterns"],
    )


def extract_tokens(images, choices=None, db=None):
    s = image_stats(images)
    dark = s["brightness"] < .52
    sharp = s["edge"] > .065
    h, sat = s["hue"], s["saturation"]
    vivid = sat > .3
    palette = {
        "bg": color(h, min(sat, .3), .09 if dark else .97),
        "surface": color(h, min(sat, .24), .15 if dark else 1),
        "text": "#f5f5f0" if dark else "#202925",
        "text_muted": color(h, .12, .69 if dark else .38),
        "primary": color(h, max(.38, sat), .88 if dark else .5),
        "secondary": color(h+.13, .48, .76 if dark else .44),
        "accent": color(h+.33, .5, .88 if dark else .74),
        "border": color(h, .16, .27 if dark else .83),
    }
    pole = "sharp geometry" if sharp else "soft, open shapes"
    rationale = f"Your input and selected references lean toward {'deep' if dark else 'light'}, {'expressive' if vivid else 'restrained'} color, so the theme uses a related palette and {pole}."
    if choices and db:
        winner = db.images[choices[0].winner_id]["path"].split("/")[-1].rsplit(".", 1)[0].replace("_", " ")
        loser = db.images[choices[0].loser_id]["path"].split("/")[-1].rsplit(".", 1)[0].replace("_", " ")
        rationale += f" Choosing {winner} over {loser} helped anchor that direction."
    return fix_contrast(VibeTokens(
        name=("Midnight" if dark else "Daylight") + (" Structure" if sharp else " Reverie"),
        colors=palette,
        typography={"heading_font": "mono" if sharp and dark else "display" if vivid else "serif", "body_font": "sans", "heading_weight": 700 if sharp else 500, "letter_spacing": "tight" if sharp else "normal", "scale": "compact" if dark else "spacious"},
        geometry={"radius": "sharp" if sharp or dark else "round", "border_width": "thick" if sharp else "thin", "density": "tight" if dark else "airy"},
        effects={"shadow": "hard" if sharp else "glow" if dark and vivid else "soft", "gradient": "bold" if vivid else "subtle", "texture": "grain" if s["edge"] > .04 else "none"},
        rationale=rationale,
    ))
