from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
Category = Literal["architecture", "landscapes", "textures", "patterns"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class BaselineProfile(StrictModel):
    summary: str = Field(min_length=1, max_length=1000)
    attributes: list[str] = Field(min_length=3, max_length=6)
    dominant_colors: list[HexColor] = Field(min_length=2, max_length=5)
    mood_words: list[str] = Field(min_length=3, max_length=5)
    preferred_categories: list[Category] = Field(max_length=4)


class ABPair(StrictModel):
    round: int = Field(ge=1, le=10)
    category: Category
    left_id: str
    right_id: str
    left_url: str
    right_url: str


class Choice(StrictModel):
    round: int = Field(ge=1, le=10)
    winner_id: str
    loser_id: str
    category: Category


class Colors(StrictModel):
    bg: HexColor
    surface: HexColor
    text: HexColor
    text_muted: HexColor
    primary: HexColor
    secondary: HexColor
    accent: HexColor
    border: HexColor


class Typography(StrictModel):
    heading_font: Literal["serif", "sans", "mono", "display"]
    body_font: Literal["serif", "sans", "mono"]
    heading_weight: int = Field(ge=100, le=900, multiple_of=100)
    letter_spacing: Literal["tight", "normal", "wide"]
    scale: Literal["compact", "normal", "spacious"]


class Geometry(StrictModel):
    radius: Literal["sharp", "soft", "round", "pill"]
    border_width: Literal["none", "thin", "thick"]
    density: Literal["tight", "normal", "airy"]


class Effects(StrictModel):
    shadow: Literal["flat", "soft", "hard", "neumorphic", "glow"]
    gradient: Literal["none", "subtle", "bold"]
    texture: Literal["none", "grain"]


class VibeTokens(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    colors: Colors
    typography: Typography
    geometry: Geometry
    effects: Effects
    rationale: str = Field(min_length=1, max_length=1600)


class SessionRequest(StrictModel):
    session_id: str = Field(min_length=1, max_length=80)


class ChoiceRequest(SessionRequest):
    round: int = Field(ge=1, le=10)
    winner_id: str = Field(max_length=200)
    loser_id: str = Field(max_length=200)


class ResetRequest(SessionRequest):
    demo_only: bool = False


class ExtractResponse(StrictModel):
    tokens: VibeTokens
    baseline: BaselineProfile
    degraded: bool
