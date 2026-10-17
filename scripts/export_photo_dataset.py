"""Package the assistant's image-specific vision annotations; no inference or network calls."""
import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]


def palette(image):
    # An observed color sample, independent of subjective mood/design interpretations.
    reduced = image.resize((160, 160)).quantize(colors=5)
    colors = reduced.getpalette()
    return ['#' + ''.join(f'{channel:02x}' for channel in colors[index*3:index*3+3])
            for count, index in sorted(reduced.getcolors(), reverse=True)]


def main():
    candidate_path = ROOT / 'tmp/photo_candidates.json'
    if (ROOT / 'images/dataset.json').exists():
        rows = json.loads((ROOT / 'images/dataset.json').read_text(encoding='utf-8'))['images']
    else:
        rows = json.loads(candidate_path.read_text(encoding='utf-8'))
    with (ROOT / 'scripts/photo_annotations.tsv').open(encoding='utf-8', newline='') as stream:
        annotations = {row['id']: row for row in csv.DictReader(stream, delimiter='\t')}
    assert len(rows) == len(annotations) == 50
    assert {r['id'] for r in rows} == set(annotations)
    for row in rows:
        a = annotations[row['id']]
        path = ROOT / row['path']
        with Image.open(path) as image:
            image = image.convert('RGB')
            row['width'], row['height'] = image.size
            row['observed'] = {'description': a['caption'], 'color_words': a['color_words'].split('|'),
                               'palette_hex': palette(image), 'shapes': a['shapes'].split('|'),
                               'textures': a['textures'].split('|'), 'composition': a['composition'],
                               'brightness': a['brightness'], 'contrast': a['contrast']}
        row['sha256'] = sha256(path.read_bytes()).hexdigest()
        row['image_type'] = 'photograph'
        row['source']['retrieved_on'] = '2026-10-17'
        row['source']['selection_evidence'] = 'Photographer-credited Unsplash photo listing; asset URL predates 2022-02; visually inspected by assistant.'
        row['annotation'] = {'method': 'assistant_vision', 'author': 'Codex', 'human_reviewed': False,
                             'date': '2026-10-17', 'scope': 'Visible pixels inspected in labeled contact sheets. Palette hex values sampled with Pillow.'}
        row['feeling'] = {'mood_words': a['moods'].split('|'), 'status': 'subjective AI interpretation'}
        row['suggested_design'] = {'theme': a['theme'], 'corners': a['corners'], 'motion': a['motion'],
                                    'effects': a['effects'].split('|'), 'rationale': a['rationale'],
                                    'status': 'design hypothesis, not validated preference ground truth'}
        row['tags'] = list(dict.fromkeys([*row['feeling']['mood_words'], *row['observed']['color_words'],
                                          *row['observed']['shapes'], *row['observed']['textures'],
                                          f"{a['theme']} theme", f"{a['corners']} corners", f"{a['motion']} motion",
                                          f"{a['brightness']} brightness", f"{a['contrast']} contrast"]))
    assert len({r['sha256'] for r in rows}) == 50
    metadata = {'name': 'Doodle2Design real-photo reference set', 'version': '1.0.0', 'image_count': 50,
                'created_on': '2026-10-17', 'category_counts': {c: sum(r['category'] == c for r in rows) for c in dict.fromkeys(r['category'] for r in rows)},
                'annotation_method': 'Assistant vision analysis; no human-reviewed annotations or imported emotion labels.',
                'interpretation_note': 'Observed visual properties, subjective feelings and suggested design treatments are separate. No emotion or design claim is experimentally validated.',
                'provenance_note': 'Selected as existing credited photographs, excluding illustrations and premium assets. Source history and visual inspection support photographic origin; no forensic authenticity certification is claimed.',
                'license_note': 'Photos retain the Unsplash License; they are not covered by the repository MIT license. See images/LICENSES.md.',
                'images': rows}
    (ROOT / 'images/dataset.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    fields = ['id', 'category', 'path', 'description', 'mood_words', 'color_words', 'palette_hex', 'shapes', 'textures',
              'composition', 'brightness', 'contrast', 'theme', 'corners', 'motion', 'effects', 'design_rationale',
              'photographer', 'source_url', 'download_url', 'license', 'license_url', 'annotation_method', 'human_reviewed', 'sha256']
    with (ROOT / 'images/dataset.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            o, f, d, s = row['observed'], row['feeling'], row['suggested_design'], row['source']
            writer.writerow({'id': row['id'], 'category': row['category'], 'path': row['path'],
                             'description': o['description'], 'mood_words': '|'.join(f['mood_words']),
                             **{k: '|'.join(o[k]) for k in ['color_words', 'palette_hex', 'shapes', 'textures']},
                             **{k: o[k] for k in ['composition', 'brightness', 'contrast']},
                             **{k: d[k] for k in ['theme', 'corners', 'motion']}, 'effects': '|'.join(d['effects']),
                             'design_rationale': d['rationale'], 'photographer': s['photographer'], 'source_url': s['page_url'],
                             'download_url': s['download_url'], 'license': s['license'], 'license_url': s['license_url'],
                             'annotation_method': 'assistant_vision', 'human_reviewed': False, 'sha256': row['sha256']})
    # A standalone gallery: all data is inline, photos use relative local paths, no server or CDN needed.
    cards = []
    for row in rows:
        o, f, d, s = row['observed'], row['feeling'], row['suggested_design'], row['source']
        chips = ''.join(f'<span class="chip" style="background:{color}" title="{color}"></span>' for color in o['palette_hex'])
        cards.append(f'''<article data-category="{row['category']}"><img src="../{escape(row['path'])}" alt="{escape(o['description'])}" loading="lazy">
<div class="body"><small>{row['id']} · {row['category']}</small><h2>{escape(o['description'])}</h2><div>{chips}</div>
<p><b>Feeling:</b> {escape(', '.join(f['mood_words']))}</p><p><b>Visible:</b> {escape(', '.join(o['shapes'] + o['textures']))}</p>
<p>{escape(o['composition'])} {o['brightness'].capitalize()} brightness; {o['contrast']} contrast.</p>
<p><b>Design:</b> {d['theme']} theme · {d['corners']} corners · {d['motion']} motion · {escape(', '.join(d['effects']))}</p>
<p>{escape(d['rationale'])}</p><a href="{s['page_url']}">Photo: {escape(s['photographer'])} / Unsplash</a></div></article>''')
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Doodle2Design · 50 real photographs</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3f2ed;color:#252b27;font:15px/1.5 system-ui,sans-serif}header{max-width:1500px;margin:auto;padding:40px 24px 24px}h1{font-size:36px;margin:0 0 12px}header p{max-width:900px}nav{display:flex;flex-wrap:wrap;gap:8px;margin:24px 0}button{font:inherit;border:1px solid #b7beb4;border-radius:24px;padding:8px 16px;background:white;color:inherit;cursor:pointer}button[aria-pressed=true]{background:#243d2c;color:white}main{max-width:1500px;margin:auto;padding:0 24px 40px;display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:22px}article{background:white;border:1px solid #dde1d8;border-radius:12px;overflow:hidden}article[hidden]{display:none}article>img{width:100%;height:290px;object-fit:contain;background:#e7e9e3;display:block}.body{padding:20px}small{color:#53604f}h2{font-size:17px;line-height:1.4}.chip{display:inline-block;width:28px;height:28px;border-radius:50%;margin:4px 4px 0 0;border:1px solid #7775}a{color:#28603b}p{margin:10px 0}footer{padding:24px;text-align:center}</style>
<header><h1>50 photographs. Five directions.</h1><p>10 each: scenery, architecture, objects, animals and photographed patterns/textures. Photos by credited Unsplash photographers. Annotations by Codex using vision; <b>no human review</b>. Feelings are subjective interpretations, and design treatments are hypotheses.</p>
<p><a href="dataset.json">JSON dataset</a> · <a href="dataset.csv">CSV dataset</a> · <a href="LICENSES.md">Photo licenses</a> · <a href="README.md">Dataset notes</a></p><nav aria-label="Filter category">'''
    for value, label in [('all','All 50'), ('landscapes','Scenery'), ('architecture','Architecture'), ('objects','Objects'), ('animals','Animals'), ('patterns','Patterns & textures')]:
        html += f'<button type="button" data-filter="{value}" aria-pressed="{str(value == "all").lower()}">{label}</button>'
    html += '</nav><p id="count" role="status">Showing 50 photographs</p></header><main>'+''.join(cards)+'''</main><footer>Images retain the Unsplash License. AI annotations are not measured human responses.</footer><script src="gallery.js"></script></html>'''
    (ROOT / 'images/gallery.html').write_text(html, encoding='utf-8')
    (ROOT / 'images/gallery.js').write_text("""document.querySelectorAll('button[data-filter]').forEach(button=>button.addEventListener('click',()=>{const category=button.dataset.filter;let count=0;document.querySelectorAll('article').forEach(card=>{card.hidden=category!=='all'&&card.dataset.category!==category;if(!card.hidden)count++});document.querySelectorAll('button[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));document.getElementById('count').textContent=`Showing ${count} photographs`;}));\n""", encoding='utf-8')
    contact_dir = ROOT / 'images/contact_sheets'
    contact_dir.mkdir(exist_ok=True)
    for category in metadata['category_counts']:
        sheet = Image.new('RGB', (1800, 680), '#eeeeee')
        draw = ImageDraw.Draw(sheet)
        for index, row in enumerate(r for r in rows if r['category'] == category):
            with Image.open(ROOT / row['path']) as image:
                thumb = ImageOps.contain(image.convert('RGB'), (350, 280))
            x, y = (index % 5)*360, (index // 5)*340
            sheet.paste(thumb, (x+(350-thumb.width)//2, y))
            draw.text((x+8, y+286), row['id'], fill='black')
            draw.text((x+8, y+304), ', '.join(row['feeling']['mood_words']), fill='black')
        sheet.save(contact_dir / f'{category}.jpg', quality=92)
    print('Exported 50 annotated photos, JSON, CSV, gallery and five contact sheets.')


if __name__ == '__main__':
    main()
