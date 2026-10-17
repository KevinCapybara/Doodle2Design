import colorsys
from io import BytesIO
import warnings

from PIL import Image, ImageFilter, ImageOps, ImageStat, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 25_000_000


def prepare_image(data):
    """Validate actual decoded format and normalize every VLM image identically."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in {"PNG", "JPEG", "WEBP"}:
                    raise ValueError("Use a PNG, JPG or WebP image.")
                if source.width * source.height > Image.MAX_IMAGE_PIXELS:
                    raise ValueError("Images must be at most 25 megapixels.")
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGBA")
                white = Image.new("RGBA", image.size, "white")
                white.alpha_composite(image)
                image = white.convert("RGB")
                image.thumbnail((768, 768), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, "JPEG", quality=80)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("This image could not be read. Use a PNG, JPG or WebP under 25 megapixels.") from error


def image_stats(images):
    samples = []
    for data in images:
        with Image.open(BytesIO(data)) as source:
            samples.append(source.convert("RGB").resize((96, 96)))
    if not samples:
        raise ValueError("At least one image is required.")
    sheet = Image.new("RGB", (96 * len(samples), 96))
    for i, sample in enumerate(samples):
        sheet.paste(sample, (96*i, 0))
    mean = tuple(v/255 for v in ImageStat.Stat(sheet).mean)
    hue, saturation, brightness = colorsys.rgb_to_hsv(*mean)
    palette = sheet.quantize(colors=5, method=Image.Quantize.MEDIANCUT)
    color_table = palette.getpalette()
    counts = sorted(palette.getcolors(), reverse=True)
    colors = ["#" + "".join(f"{c:02x}" for c in color_table[index*3:index*3+3]) for _, index in counts]
    # Ignore the perimeter artifact of FIND_EDGES.
    gray = sheet.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES).crop((2, 2, gray.width-2, gray.height-2))
    edge = ImageStat.Stat(edges).mean[0]/255
    return {"hue": hue, "saturation": saturation, "brightness": brightness, "edge": edge, "colors": colors}


def luminance(value):
    rgb = [int(value[i:i+2], 16)/255 for i in (1, 3, 5)]
    linear = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    return sum(c*w for c, w in zip(linear, (.2126, .7152, .0722)))


def contrast_ratio(a, b):
    x, y = sorted((luminance(a), luminance(b)))
    return (y+.05)/(x+.05)


def fix_contrast(tokens):
    result = tokens.model_copy(deep=True)
    if contrast_ratio(result.colors.text, result.colors.bg) < 4.5:
        result.colors.text = max(("#ffffff", "#111111"), key=lambda c: contrast_ratio(c, result.colors.bg))
    return result
