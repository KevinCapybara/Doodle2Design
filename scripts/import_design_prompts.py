"""Import user-supplied DOCX design briefs without extracting arbitrary ZIP paths."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def import_catalog(archive_path, destination):
    entries = []
    seen = set()
    with zipfile.ZipFile(archive_path) as archive:
        if len(archive.infolist()) > 100:
            raise ValueError("Expected a small collection of design documents.")
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = Path(item.filename).name
            if not name.endswith(".docx") or item.file_size > 2_000_000 or name in seen:
                raise ValueError("Unexpected or duplicate design document.")
            seen.add(name)
            raw = archive.read(item)
            with zipfile.ZipFile(io.BytesIO(raw)) as document:
                xml = document.getinfo("word/document.xml")
                if xml.file_size > 4_000_000:
                    raise ValueError("Design document is too large.")
                tree = ET.fromstring(document.read(xml))
            paragraphs = ["".join(p.itertext()) for p in tree.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p")]
            text = "\n".join(paragraphs)
            if "<design-system>" not in text or "</design-system>" not in text:
                raise ValueError(name + " must contain a complete design-system section.")
            brief = text.split("<design-system>", 1)[1].split("</design-system>", 1)[0].strip()
            entries.append({"title": name[:-5], "source": name, "sha256": hashlib.sha256(raw).hexdigest(),
                            "summary": brief[:2000], "instructions": brief, "_bytes": raw})
    if not entries:
        raise ValueError("No design documents found.")
    # Validate every entry before writing any output.
    destination.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        (destination / entry["source"]).write_bytes(entry.pop("_bytes"))
    (destination / "catalog.json").write_text(json.dumps(sorted(entries, key=lambda e: e["title"]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(f"Imported {import_catalog(args.archive, ROOT / 'design_prompts')} themes.")
