# Doodle2Design

**Your instinct. A design language.**

Draw a feeling or upload visual references, follow your eye through ten A/B
comparisons, and let an LLM turn that taste into a completely redesigned website.

## Quick start

Install Python **3.10 or newer**, clone this repository, then run:

```sh
python start.py
```

On Windows you can double-click run.bat; macOS/Linux users can run ./run.sh.
The launcher creates .venv, installs requirements, creates .env, indexes the bundled 50 real
photographs with AI-authored visual annotations, and opens [localhost:8000](http://localhost:8000).
It tries port 8001 if 8000 is occupied. Ctrl+C stops the server.

No frontend build, npm, database, authentication or hosting is required.
Use one server worker bound to loopback; this is a personal local application.

## Enable LLM website generation

Set your OpenAI key in the local, Git-ignored .env file:

```dotenv
AI_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-5.4
OPENAI_VISION_MODEL=
OPENAI_REDESIGN_MODEL=
VIBE_MOCK=0
```

Restart the server after changes. Existing environment variables take precedence.
OPENAI_MODEL is the default for all OpenAI calls. OPENAI_VISION_MODEL and
OPENAI_REDESIGN_MODEL optionally override analysis and redesign respectively.
The key remains on the backend and is never returned by the API or UI.

Anthropic remains supported with AI_PROVIDER=anthropic, ANTHROPIC_API_KEY,
VLM_MODEL and optional REDESIGN_MODEL. AI_PROVIDER=auto prefers OpenAI if its
key is present, otherwise Anthropic. Explicit selection never falls back to the
other provider. Leave VIBE_MOCK=0 to enable AI; VIBE_MOCK=1 disables both.

Without a key, drawing, uploads, ten comparisons and taste extraction work offline.
Website generation shows a setup message; it does not substitute a preset.
Configure the key before starting a calibration because restarting clears sessions.

With AI enabled, normalized source images and winning references are sent to
the selected provider for visual analysis, theme matching and code generation. Matching also
uses descriptions of rejected references. The selected full design brief and
original demo content are sent for generation.

## Use it

1. **Express your taste.** Draw with brush, shapes and color, or upload 1â€“3
   PNG/JPG/WebP references (8 MB and 25 megapixels maximum per image).
2. **Follow your eye.** Choose between two distinct images in each of ten
   text-free rounds. Click, tap or use the left/right arrow keys.
3. **Match a theme.** The LLM considers your baseline, mood, sentiment, shapes,
   texture, palette and accepted/rejected preferences to select one of the exact
   30 document titles from the supplied design catalog.
4. **Generate the website.** The LLM follows that theme's full brief to write new
   HTML, CSS and JavaScript: layout, hierarchy, graphics, button shapes, surfaces,
   animations and local interactions. This can take several minutes.
5. **Inspect and save.** See the theme and match reason, compare the original and
   AI redesign, open the isolated preview full screen, or download the entire
   standalone HTML website and model-written CSS. JSON export preserves the
   extracted taste profile.

Before/after, showing the saved redesign and downloads reuse the completed
artifact. They do not trigger another paid generation. A failed job has an
explicit retry. Start a new feeling cancels active work and clears the session.

Generated pages include pause/resume motion and respect reduced-motion settings.
The contact form validates locally and shows a demo confirmation; it sends nothing.

## Real-photo reference dataset

The A/B library contains **50 real Unsplash photographs**, ten each in scenery,
architecture, objects, animals and photographed patterns/textures. All annotations
were authored by Codex using vision, with **no human review**. Observed colors,
shapes, textures and composition are separate from subjective mood words and
suggested design treatments.

Browse [the gallery](images/gallery.html), [JSON](images/dataset.json),
[CSV](images/dataset.csv), and [dataset notes and licenses](images/README.md).
Photographer credits, source URLs and file hashes are included for every photo.
The five categories each appear twice across ten rounds, with no repeated photo.

Normal startup uses the bundled local files. To restore missing photos and rebuild:

```sh
python scripts/download_photo_dataset.py
python scripts/build_manifest.py
```

The downloader checks hashes and never generates placeholders. Rebuilding preserves
complete annotations and provenance from `images/dataset.json`. Custom images can
be added under the architecture, landscapes, objects, animals and patterns folders
in `images/library/`; keep at least six distinct images per category. Restart the
server after rebuilding. Photos retain the Unsplash License rather than the
repository's MIT software license.

## Your design documents

The supplied archive contains 30 **Word documents**, despite the original PDF
description. Original files and their complete extracted design-system sections
are stored in [design_prompts](design_prompts/README.md).

Theme names exactly match filenames: Academia, Art Deco, Bauhaus, Botanical,
Bold Typography, Claymorphism, Cyberpunk, Enterprise, Flat Design, Industrial,
Kinetic, Luxury, Material Design, Maximalism, Minimal Dark, Modern Dark,
Monochrome, Neo Brutalism, Neumorphism, Newsprint, Organic, Playful Geometric,
Professional, Retro, SaaS, Sketch, Swiss Minimalist, Terminal, Vaporwave and Web3.

The common agent-role preamble is excluded. Documents provide visual requirements,
not tool commands or permissions. Selection uses catalog excerpts; generation
receives the selected complete design brief. Framework examples and web-font
suggestions are adapted to vanilla browser code, inline SVG/CSS and system fonts.

Reimport a revised archive with:

```sh
python scripts/import_design_prompts.py "path/to/Design Prompts.zip"
```

Restart after importing so the cached catalog reloads.

## Architecture and isolation

The app uses FastAPI, in-memory UUID sessions, Pillow, Pydantic, vanilla JavaScript
and the OpenAI/Anthropic async SDKs. Drawing/upload and A/B calibration feed the existing
validated taste profile. A background job then selects a document and generates a
new website. Status is polled while the UI remains responsive.

Generated code is never executed on the server or inserted into the host DOM.
A sandboxed iframe and an HTTP content security policy isolate it from the app:
no host DOM access, storage, network connections, external scripts/resources,
nested frames or form submissions. Local scripts, animations and form handlers
work. Exported HTML includes its own restrictive resource policy.

The trusted original Northwind demo remains under /demo/ for comparison.
The earlier token renderer is retained for compatibility, but is no longer the
result page's redesign engine. Its fixed visual vocabulary is taste evidence,
not a limit on the generated website.

Sessions are process-local, limited to 100, with idle cleanup after two hours.
Reset cancels generation and discards the artifact. Restart loses sessions and
generated pages; download HTML to keep a design. Uploads stay in memory.
The legacy latest-token file demo_site/vibe.json remains ignored by Git.

Two generation jobs can run concurrently, with at most four pending. Each model
stage allows at most two attempts, including invalid output. The total job budget
is eight minutes. Selection and generation failures produce retryable errors.
The original taste extraction retains its 14-second model deadline and offline
fallback.

See [LLM_REDESIGN.md](docs/LLM_REDESIGN.md) for contracts, lifecycle and boundaries.

## API

[OpenAPI schema](http://localhost:8000/openapi.json) is available locally.

| Method | Route | Behavior |
| --- | --- | --- |
| POST | /api/session | Create session |
| POST | /api/baseline | Multipart session_id, mode, files |
| GET | /api/ab/next | Current pair; optional prefetch=true |
| POST | /api/ab/choice | Validated, idempotent choice |
| POST | /api/extract | Extract and cache taste profile |
| POST | /api/redesign | Start/reuse document-led generation |
| GET | /api/redesign | Poll phase, theme, match reason and output links |
| GET | /api/redesign/preview | Isolated generated HTML |
| GET | /api/redesign/download | Standalone HTML attachment |
| GET | /api/redesign/css | Model-written CSS attachment |
| POST | /api/reset | Cancel and clear session; demo_only retains session |
| GET | /api/config | Offline/generation availability and catalog size |
| GET | /api/tokens | Legacy latest saved taste tokens |

Session-specific GET endpoints use session_id query parameters. Mutation requests
use JSON session_id unless noted. Invalid phases return 409, unknown sessions 404,
invalid inputs 422, missing generation configuration 503, and a full job queue 429.

## Verification

Run .venv/Scripts/python -m pytest -q on Windows, or
.venv/bin/python -m pytest -q on macOS/Linux. The suite never calls a paid model.

Optional legacy mapping tests: node --test tests/test_visual_map.mjs.
Optional Edge browser QA requires Playwright and the normal server on port 8000:
start python tests/redesign_fixture_server.py on port 8002, then run
node tests/browser_redesign.cjs.
The fixture substitutes model responses while exercising the real backend and UI.

See [VERIFICATION.md](docs/VERIFICATION.md) for results and limitations.
A working API key is required to assess actual model output and generation latency;
local fixture tests verify integration, not live model design quality.

MIT licensed. See [LICENSE](LICENSE).
