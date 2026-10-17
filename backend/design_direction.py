"""Coherent visual directions for offline inference, using constrained tokens only."""
import colorsys
from backend.schemas import Visuals


def shade(hue, saturation, brightness):
    return "#" + "".join(f"{round(c*255):02x}" for c in colorsys.hsv_to_rgb(hue, saturation, brightness))


def is_green(stats):
    return .18 <= stats["hue"] <= .46 and stats["saturation"] > .12


def enrich_theme(tokens, stats, anchor):
    if is_green(anchor) or is_green(stats):
        hue = min(.38, max(.25, anchor["hue"] if is_green(anchor) else stats["hue"]))
        dark = anchor["brightness"] < .42
        tokens.name = "Moonlit Grove" if dark else "Forest Reverie"
        tokens.colors.bg = shade(hue, .28 if dark else .055, .12 if dark else .97)
        tokens.colors.surface = shade(hue, .22 if dark else .035, .19 if dark else 1)
        tokens.colors.text = "#eef3e6" if dark else "#203c2c"
        tokens.colors.text_muted = shade(hue, .18, .72 if dark else .39)
        tokens.colors.primary = shade(hue, .44 if dark else .56, .77 if dark else .38)
        tokens.colors.secondary = shade(hue-.025, .25, .61)
        tokens.colors.accent = shade(.18, .4, .79)
        tokens.colors.border = shade(hue, .18, .3 if dark else .83)
        tokens.typography.heading_font = "serif"
        tokens.typography.heading_weight = 500
        tokens.typography.scale = "spacious"
        tokens.geometry.radius, tokens.geometry.border_width, tokens.geometry.density = "round", "thin", "airy"
        tokens.effects.shadow, tokens.effects.gradient, tokens.effects.texture = "soft", "subtle", "none"
        tokens.visuals = Visuals(motif="forest", layout="centered", motion="calm", button_style="pill", card_style="organic")
        description = "The green, organic direction in your references becomes a layered forest, translucent tree silhouettes, soft leaf-shaped surfaces and pill buttons, with slow floating motion."
    elif .48 <= anchor["hue"] <= .9 and anchor["saturation"] > .16 and (anchor["brightness"] < .55 or anchor["saturation"] > .45):
        tokens.name = "Electric Orbit"
        tokens.typography.heading_font = "display"
        tokens.typography.heading_weight = 700
        tokens.geometry.radius, tokens.geometry.border_width = "round", "thin"
        tokens.effects.shadow, tokens.effects.gradient = "glow", "subtle"
        tokens.visuals = Visuals(motif="orbital", layout="split", motion="kinetic", button_style="soft", card_style="glass")
        description = "Your cool, expressive starting palette becomes an orbital illustration, luminous glass panels, rounded controls and animated rings and chart bars."
    elif stats["edge"] > .065 or anchor["saturation"] < .08:
        tokens.name = "Concrete Signal"
        tokens.typography.heading_font = "mono"
        tokens.typography.heading_weight = 800
        tokens.typography.scale = "compact"
        tokens.geometry.radius, tokens.geometry.border_width, tokens.geometry.density = "sharp", "thick", "tight"
        tokens.effects.shadow, tokens.effects.gradient = "hard", "none"
        tokens.visuals = Visuals(motif="grid", layout="poster", motion="kinetic", button_style="cut", card_style="outline")
        description = "Your structured references become an architectural grid, bold blocks, clipped-corner buttons and outlined cards, with crisp entrances and graphic motion."
    else:
        tokens.name = "Sunroom Studio"
        tokens.typography.heading_font = "serif"
        tokens.typography.heading_weight = 500
        tokens.typography.scale = "spacious"
        tokens.geometry.radius, tokens.geometry.density = "round", "airy"
        tokens.effects.shadow, tokens.effects.gradient = "soft", "subtle"
        tokens.visuals = Visuals(motif="waves", layout="poster", motion="calm", button_style="pill", card_style="paper")
        description = "Your warmer, softer references become flowing paper-cut graphics, an editorial composition, sculpted cards and pill buttons, with gentle motion."
    selection = tokens.rationale.split(". ", 1)
    tokens.rationale = description + (" " + selection[1] if len(selection) > 1 else "")
    return tokens
