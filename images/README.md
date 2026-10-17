# Doodle2Design: 50 real-photo references

This is the active local A/B reference library: **50 photographs, 10 per category**.

| Category | Contents |
|---|---|
| `landscapes` | Hills, mountains, lakes, forests and river valleys |
| `architecture` | Glass towers, angular buildings, curved facades and a neon skyline |
| `objects` | Ceramic vessels, fruit, coffee and flower arrangements |
| `animals` | Fox, deer, butterflies, birds, dogs and big cats |
| `patterns` | Photographed tiles, sculptural lines, wall pattern, plaster, glass, concrete, fabric, paper, ice and stone |

## Files

- `dataset.json`: canonical dataset with image-specific observations, feelings, design hypotheses and source metadata.
- `dataset.csv`: the same 50 records flattened for spreadsheet use; list fields use `|` separators.
- `manifest.json`: application index built from the dataset, preserving annotations, source fields and stable IDs.
- `gallery.html`: standalone filterable visual catalog; open locally or visit `/images/gallery.html` while the app is running.
- `contact_sheets/`: one labeled visual overview per category.
- `library/`: the 50 locally stored JPEG photographs; original aspect ratios retained, longest edge at most 1200 px.
- `LICENSES.md`: photo terms and attribution notes.

## Annotation method

Codex inspected all 50 downloaded photographs using vision in labeled contact sheets on October 17, 2026. **No human review** was performed and no dataset emotion ratings were imported. The records explicitly set `annotation.method = "assistant_vision"` and `human_reviewed = false`.

Each record keeps three separate groups:

1. `observed`: an image-specific description, color words, visible shapes, textures, composition, brightness and contrast. `palette_hex` is a five-color sample computed from the actual JPEG with Pillow; it is not a recommended interface palette.
2. `feeling`: three subjective mood words inferred by the assistant from the image. These are not measured human responses.
3. `suggested_design`: light/dark theme, corner style, motion, effects and a rationale. These are design hypotheses, not validated ground truth. Suggested motion is an interface interpretation of a still photo; it is not motion detected in the image.

`tags` combines these attributes for the application's existing comparison selection. The online theme extractor receives the selected and rejected records' annotations. The offline fallback continues to derive its theme from image pixels. Each of the five categories appears exactly twice in the ten-round test, with no repeated photo.

Source titles can be inaccurate: for example, the source labeled `objects_001` as stones, but the downloaded image visibly shows pears. `observed.description` follows the visible photograph; `source.source_title` preserves the catalog label.

## Provenance

Photos were selected from free, photographer-credited Unsplash photo listings, excluding premium assets and illustrations. The selected image asset identifiers predate February 2022, and all downloaded images were visually inspected. These checks support photographic origin; they are not a forensic guarantee of authenticity. Photos may have normal photographic editing and color grading.

Every record includes the photographer, Unsplash photo ID, source page, pinned CDN URL, license link, retrieval date and SHA-256 of the included JPEG. This is a assistant-curated image set with AI annotations, not an established emotion benchmark.

## Restore and export

The photos are bundled, so normal application startup is offline. To restore missing photos, with project dependencies installed:

```sh
python scripts/download_photo_dataset.py
python scripts/build_manifest.py
```

The downloader never generates replacement images and never overwrites an existing file. It checks included file hashes and rejects a changed remote rendition rather than silently accepting it. Exact restoration depends on Unsplash serving the same rendition and the Pillow encoder version; the checked-in JPEGs are the canonical copies.

To regenerate JSON/CSV/gallery/contact-sheet exports from the saved assistant annotations:

```sh
python scripts/export_photo_dataset.py
python scripts/build_manifest.py
```

`scripts/photo_sources.tsv` records the selected sources. `scripts/photo_annotations.tsv` contains the saved image-by-image vision analysis; the export script does not call an AI model or infer moods from filenames or categories.
