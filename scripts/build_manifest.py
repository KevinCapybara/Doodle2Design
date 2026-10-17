"""Index local photographs while preserving dataset annotations and provenance."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from backend.library_config import CATEGORIES


def build_manifest(root=ROOT):
    root = Path(root)
    path = root / "images/manifest.json"
    old = {}
    if path.exists():
        old = {entry["path"]: entry for entry in json.loads(path.read_text(encoding="utf-8"))["images"]}
    dataset_path = root / "images/dataset.json"
    if dataset_path.exists():
        old.update({entry["path"]: entry for entry in json.loads(dataset_path.read_text(encoding="utf-8"))["images"]})
    images = []
    for category in CATEGORIES:
        for file in sorted((root / "images/library" / category).glob("*")):
            if file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                continue
            relative = file.relative_to(root).as_posix()
            previous = old.get(relative, {})
            images.append({**previous, "id": previous.get("id", f"{category}_{len([i for i in images if i['category'] == category])+1:03d}"), "category": category, "path": relative, "tags": previous.get("tags", [])})
    if not images:
        raise ValueError("Photo library is empty. Run scripts/download_photo_dataset.py to restore it.")
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps({"images": images}, indent=2)+"\n", encoding="utf-8")
    return images


if __name__ == "__main__":
    print(f"Indexed {len(build_manifest())} reference images.")
