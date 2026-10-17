"""Restore the pinned real-photo library without generating replacement images."""
import csv
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import urllib.request

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def download(row):
    target = ROOT / row['path']
    if target.exists():
        if row.get('sha256') and sha256(target.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError(f"Existing photo differs from dataset: {target}")
        return
    request = urllib.request.Request(row['source']['download_url'], headers={'User-Agent': 'Doodle2Design/1.0 (photo reference dataset)'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
    with Image.open(BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, 'JPEG', quality=90, optimize=True)
        data = output.getvalue()
    if row.get('sha256') and sha256(data).hexdigest() != row['sha256']:
        raise ValueError(f"Remote photo has changed: {row['id']}; existing dataset left intact")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    print(f"Downloaded {row['id']}", flush=True)


def main():
    dataset = ROOT / 'images/dataset.json'
    if dataset.exists():
        rows = json.loads(dataset.read_text(encoding='utf-8'))['images']
    else:
        rows, counts = [], {}
        with (ROOT / 'scripts/photo_sources.tsv').open(encoding='utf-8', newline='') as stream:
            for source in csv.DictReader(stream, delimiter='\t'):
                category = source['category']
                counts[category] = counts.get(category, 0) + 1
                image_id = f'{category}_{counts[category]:03d}'
                rows.append({'id': image_id, 'category': category,
                             'path': f'images/library/{category}/{image_id}.jpg',
                             'source': {'provider': 'Unsplash', 'photo_id': source['photo_id'],
                                        'photographer': source['photographer'],
                                        'source_title': source['source_title'],
                                        'page_url': f"https://unsplash.com/photos/{source['photo_id']}",
                                        'download_url': f"https://images.unsplash.com/photo-{source['asset_id']}?w=1200&q=85&fm=jpg&fit=max",
                                        'license': 'Unsplash License', 'license_url': 'https://unsplash.com/license'}})
        (ROOT / 'tmp').mkdir(exist_ok=True)
        (ROOT / 'tmp/photo_candidates.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
    with ThreadPoolExecutor(max_workers=6) as executor:
        list(executor.map(download, rows))
    print(f'Photo library ready: {len(rows)} images.')


if __name__ == '__main__':
    main()
