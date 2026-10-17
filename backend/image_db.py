import json
from pathlib import Path

from scripts.build_manifest import ROOT, build_manifest

CATEGORIES = ("architecture", "landscapes", "textures", "patterns")


class ImageDB:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        manifest = self.root / "images/manifest.json"
        entries = json.loads(manifest.read_text())["images"] if manifest.exists() else build_manifest(self.root)
        self.images = {}
        for entry in entries:
            resolved = (self.root / entry["path"]).resolve()
            if entry["category"] not in CATEGORIES or not resolved.is_relative_to((self.root / "images/library").resolve()):
                raise ValueError("Invalid library manifest path or category.")
            if not resolved.is_file() or entry["id"] in self.images:
                raise ValueError("Missing image or duplicate id in manifest; rebuild it.")
            self.images[entry["id"]] = entry
        for category in CATEGORIES:
            if len(self.category(category)) < 6:
                raise ValueError(f"Add at least 6 images to {category}, then rebuild the manifest.")

    def category(self, category):
        return [entry for entry in self.images.values() if entry["category"] == category]

    def path(self, image_id):
        return self.root / self.images[image_id]["path"]

    def url(self, image_id):
        from urllib.parse import quote
        return "/" + quote(self.images[image_id]["path"], safe="/")
