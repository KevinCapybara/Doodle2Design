from io import BytesIO
import pytest
from PIL import Image
from pydantic import ValidationError

from backend.mock import extract_tokens
from backend.schemas import VibeTokens
from backend.imaging import contrast_ratio, fix_contrast, prepare_image


def png(color):
    data = BytesIO()
    Image.new("RGB", (100, 100), color).save(data, format="PNG")
    return data.getvalue()


def test_valid_tokens():
    assert isinstance(extract_tokens([png("#172a39")]), VibeTokens)


@pytest.mark.parametrize("section,field,value", [("colors", "bg", "red"), ("geometry", "radius", "huge"), ("effects", "shadow", "evil"), ("typography", "heading_weight", 3)])
def test_invalid_tokens(section, field, value):
    tokens = extract_tokens([png("#172a39")]).model_dump()
    tokens[section][field] = value
    with pytest.raises(ValidationError):
        VibeTokens.model_validate(tokens)


def test_extra_keys_rejected():
    tokens = extract_tokens([png("red")]).model_dump()
    tokens["css"] = "arbitrary code"
    with pytest.raises(ValidationError):
        VibeTokens.model_validate(tokens)


def test_contrast_fixer_changes_only_text():
    tokens = extract_tokens([png("#cccccc")])
    tokens.colors.text = tokens.colors.bg
    before = tokens.model_dump()
    corrected = fix_contrast(tokens)
    assert contrast_ratio(corrected.colors.text, corrected.colors.bg) >= 4.5
    before["colors"]["text"] = corrected.colors.text
    assert corrected.model_dump() == before


def test_distinct_input_palettes_produce_distinct_tokens():
    dark = extract_tokens([png("#12142e")])
    light = extract_tokens([png("#e8d3c9")])
    assert dark.colors.bg != light.colors.bg
    assert dark.geometry != light.geometry


def test_image_preparation_downscales_to_jpeg():
    data = BytesIO()
    Image.new("RGBA", (1600, 900), (255, 0, 0, 100)).save(data, format="PNG")
    prepared = prepare_image(data.getvalue())
    with Image.open(BytesIO(prepared)) as image:
        assert max(image.size) == 768
        assert image.format == "JPEG"


def test_legacy_tokens_remain_valid_with_neutral_visual_defaults():
    tokens = extract_tokens([png("#132f29")]).model_dump()
    tokens.pop("visuals", None)
    restored = VibeTokens.model_validate(tokens)
    assert restored.visuals.motif == "none"
    assert restored.visuals.motion == "none"


@pytest.mark.parametrize("field", ["motif", "layout", "motion", "button_style", "card_style"])
def test_arbitrary_visual_instructions_are_rejected(field):
    tokens = extract_tokens([png("#132f29")]).model_dump()
    tokens.setdefault("visuals", {})[field] = "arbitrary-css-or-script"
    with pytest.raises(ValidationError):
        VibeTokens.model_validate(tokens)


@pytest.mark.parametrize("input_color,motif,button,motion", [
    ("#5c8450", "forest", "pill", "calm"),
    ("#20204b", "orbital", "soft", "kinetic"),
    ("#dcb29c", "waves", "pill", "calm"),
])
def test_inputs_select_complete_visual_directions(input_color, motif, button, motion):
    tokens = extract_tokens([png(input_color)])
    assert tokens.visuals.motif == motif
    assert tokens.visuals.button_style == button
    assert tokens.visuals.motion == motion
    if motif == "forest":
        assert tokens.geometry.radius == "round"
        assert tokens.typography.heading_font == "serif"
