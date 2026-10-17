import json
from hashlib import sha256
from pathlib import Path

from PIL import Image, ImageOps

from scripts.build_manifest import ROOT, build_manifest

CATEGORIES = ("architecture", "landscapes", "textures", "patterns")


class ImageDB:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        manifest = self.root / "images/manifest.json"
        entries = json.loads(manifest.read_text())["images"] if manifest.exists() else build_manifest(self.root)
        self.images = {}
        seen_ids, seen_content = set(), set()
        for entry in entries:
            resolved = (self.root / entry["path"]).resolve()
            if entry["category"] not in CATEGORIES or not resolved.is_relative_to((self.root / "images/library").resolve()):
                raise ValueError("Invalid library manifest path or category.")
            if not resolved.is_file() or entry["id"] in seen_ids:
                raise ValueError("Missing image or duplicate id in manifest; rebuild it.")
            seen_ids.add(entry["id"])
            # Compare visual content, not filenames or encoded file bytes. Normalizing
            # also catches copies with different metadata or image dimensions.
            with Image.open(resolved) as source:
                thumbnail = ImageOps.exif_transpose(source).convert("RGB").resize((64, 64), Image.Resampling.LANCZOS)
                fingerprint = sha256(thumbnail.tobytes()).digest()
            if fingerprint in seen_content:
                continue
            seen_content.add(fingerprint)
            self.images[entry["id"]] = entry
        for category in CATEGORIES:
            if len(self.category(category)) < 6:
                raise ValueError(f"Add at least 6 distinct images to {category}, then rebuild the manifest.")

    def category(self, category):
        return [entry for entry in self.images.values() if entry["category"] == category]

    def path(self, image_id):
        return self.root / self.images[image_id]["path"]

    def url(self, image_id):
        from urllib.parse import quote
        return "/" + quote(self.images[image_id]["path"], safe="/")
