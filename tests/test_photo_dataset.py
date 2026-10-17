import csv
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image
import pytest

from backend.library_config import CATEGORIES
from scripts.build_manifest import build_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_bundled_library_has_50_unique_photos_with_vision_annotations():
    dataset = json.loads((ROOT / 'images/dataset.json').read_text(encoding='utf-8'))
    rows = dataset['images']
    assert len(rows) == len({r['id'] for r in rows}) == len({r['sha256'] for r in rows}) == 50
    assert Counter(r['category'] for r in rows) == {category: 10 for category in CATEGORIES}
    actual_files = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'images/library').rglob('*') if p.is_file()}
    assert actual_files == {r['path'] for r in rows}
    for row in rows:
        photo = ROOT / row['path']
        assert sha256(photo.read_bytes()).hexdigest() == row['sha256']
        with Image.open(photo) as image:
            assert image.format == 'JPEG'
            assert image.size == (row['width'], row['height'])
            assert max(image.size) <= 1200
        assert row['annotation']['method'] == 'assistant_vision'
        assert row['annotation']['human_reviewed'] is False
        assert row['image_type'] == 'photograph'
        assert len(row['feeling']['mood_words']) == 3
        assert len(row['observed']['palette_hex']) == 5
        assert row['observed']['description'] and row['observed']['shapes'] and row['observed']['textures']
        assert row['suggested_design']['rationale'] and row['tags']
        assert row['source']['photographer'] and row['source']['page_url'].startswith('https://unsplash.com/photos/')
        assert row['source']['license_url'] == 'https://unsplash.com/license'
    with (ROOT / 'images/dataset.csv').open(encoding='utf-8-sig', newline='') as stream:
        csv_rows = list(csv.DictReader(stream))
    assert len(csv_rows) == 50
    assert {r['id']: r['sha256'] for r in csv_rows} == {r['id']: r['sha256'] for r in rows}


def test_manifest_rebuild_preserves_full_photo_annotations(tmp_path):
    source = json.loads((ROOT / 'images/dataset.json').read_text(encoding='utf-8'))['images'][0]
    path = tmp_path / source['path']
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / source['path']).read_bytes())
    (tmp_path / 'images/dataset.json').write_text(json.dumps({'images': [source]}), encoding='utf-8')
    assert build_manifest(tmp_path) == [source]
    assert build_manifest(tmp_path) == [source]


def test_empty_library_does_not_generate_synthetic_fallback(tmp_path):
    with pytest.raises(ValueError, match='download_photo_dataset'):
        build_manifest(tmp_path)
    assert not list(tmp_path.rglob('*.jpg'))
