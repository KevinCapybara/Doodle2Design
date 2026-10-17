"""Index supplied local images; generate procedural art only for an empty library."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.fetch_sample_images import CATEGORIES, generate


def build_manifest(root=ROOT):
    root = Path(root)
    generate(root)
    path = root / "images/manifest.json"
    old = {}
    if path.exists():
        old = {entry["path"]: entry.get("tags", []) for entry in json.loads(path.read_text())["images"]}
    images = []
    for category in CATEGORIES:
        for file in sorted((root / "images/library" / category).glob("*")):
            if file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            relative = file.relative_to(root).as_posix()
            images.append({"id": f"{category}_{len([i for i in images if i['category'] == category])+1:03d}", "category": category, "path": relative, "tags": old.get(relative, [])})
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"images": images}, indent=2)+"\n", encoding="utf-8")
    return images


if __name__ == "__main__":
    print(f"Indexed {len(build_manifest())} reference images.")
