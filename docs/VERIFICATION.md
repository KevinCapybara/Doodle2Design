# Verification — Doodle2Design

## Real-photo dataset update — October 17, 2026

The active reference library now contains **50 real photographs**, ten each in landscapes, architecture, objects, animals and patterns/textures. It replaces the procedural library described in the earlier verification below.

- Photo-update suite before integration: **42 passed**, 18.48 seconds, Python 3.13. No live model calls were made. One upstream Starlette/httpx deprecation warning remains.
- Dataset checks cover exactly 50 distinct IDs and file hashes, five balanced categories, readable JPEGs, saved dimensions, complete vision annotations, source/license metadata, CSV parity, and absence of additional files in the active library.
- Manifest rebuild preserves full annotations and stable IDs. Empty libraries report an explicit restore instruction instead of generating synthetic images.
- Existing ten-round API tests pass with all five categories and twenty distinct photo IDs.
- The gallery was inspected in the in-app browser. The patterns filter displays ten cards, the replacement material photo has the correct description, external gallery JavaScript works under the app's content security policy, and the desktop layout has no horizontal overflow.
- Preview: [dataset gallery](dataset_gallery.png). Dataset and annotation methodology: [images/README.md](../images/README.md).

## Website-generation verification

Verified on Windows with Python 3.12 and headless Microsoft Edge on 2026-10-17.
Regression tests do not make live paid model requests. Keys are stripped from
the test environment and all provider responses are local fakes. A separate live
OpenAI authentication/model lookup and tiny image/JSON streaming check verify
the configured adapter. Full paid website generation was not run.

## Current document-led LLM redesign

- Python suite: **62 passed**. Legacy Node mapping suite: **6 passed**.
- OpenAI-only operation covers baseline analysis, comparison planning, taste
  extraction, document matching and full website generation. Image conversion,
  provider/model selection, invalid JSON retry, failed/incomplete/refused streams,
  metadata and setup errors are covered. The real installed OpenAI SDK serializes
  and decodes an SSE response through an in-memory HTTP transport, with no network.
  The live image-only check caught OpenAI's requirement for JSON in input text;
  the adapter now supplies that instruction when missing and a regression covers it.
- All 30 exact document titles, complete design-system sections and original
  DOCX SHA-256 hashes verified.
- Matching receives the baseline, mood, original images, ten winning images,
  selected/rejected tags and the complete catalog of selection descriptions.
  Unknown/invented theme names are rejected.
- Generation receives the selected full design brief and original Northwind
  content. The pipeline returns model-written markup/CSS/JavaScript rather
  than selecting a preset renderer.
- SDK streaming is exercised with fake responses. Invalid JSON is retried once;
  generated structure, required sections, business data and code boundaries
  are validated. Failures produce an error state, without exposing internal
  transport details.
- Job caching prevents duplicate generation. Reset cancels active work and
  removes completed artifacts. Missing key and incomplete calibration return
  clear API errors.
- Generated HTML carries HTTP sandbox/CSP headers; downloads also contain an
  embedded resource policy. The host application's policy remains unchanged.

## Browser integration

The repeatable browser fixture uses real FastAPI routes and the real wizard,
substituting only model responses. Its simple generated page is an integration
fixture, not an example of live model design quality.

- Complete drawing and all ten A/B selections through browser controls.
- Missing-key error disables AI preview/download, then retry reaches generation.
- Exact theme title, match reason, model and generated summary appear.
- Generated markup/CSS/scripts load and local form validation/confirmation works.
- Before/after changes between the original and generated website.
- Full HTML and model-written CSS download with correct filenames.
- Pause/resume and operating-system reduced motion work.
- Wizard checked at 320, 768, 1024 and 1440 pixels without document overflow.
- Generated iframe cannot access the host DOM and its network request is blocked.
- Fullscreen retains the HTTP sandbox, blocked network and inaccessible storage.
- Reset discards the artifact and returns to the landing page.
- No uncaught browser script errors in the fixture flow.
- A separate ten-round flow against the real localhost:8000 configuration ends
  in the expected API-key setup message, rather than a fake generated design.
- Result and setup screenshots were visually inspected.

The browser checks caught and corrected sandboxed form handling: allow-forms
enables validation and submit events, while CSP form-action none continues to
block submissions. The trusted original preview retains its normal origin;
generated code never receives allow-same-origin.

## Existing behavior retained

The suite still covers strict token models, readable text contrast, image
normalization, content-based reference deduplication, reproducible ten-round
same-category pairing, twenty unique references, category coverage, full draw
and upload APIs, upload restrictions, idempotent voting, phase guards,
baseline/extraction offline fallbacks, token reset/reapply and legacy visual
mappings.

Prior launcher checks confirmed fresh installation, requirement-hash caching,
generated reference libraries, loopback serving, occupied-port fallback to 8001
and restart behavior. The OpenAI integration adds the bounded openai>=2,<3 SDK dependency.

## Limits

Live theme choice, generated design quality, runtime correctness of
arbitrary model output and full website generation latency remain unverified
by a paid end-to-end run. Integration fixtures establish the pipeline and browser boundary,
not how well the real model follows every visual detail in a brief.

The original under-15-second goal applies to taste extraction, which keeps its
14-second model deadline and offline fallback. Full website generation is a
separate, visibly longer background step with an eight-minute job budget.
Output validation checks selected immutable business facts and required sections;
it cannot prove all copy, interactions or responsive layouts are perfect.

Starlette emits one TestClient/httpx dependency deprecation warning. Tests pass;
the warning is not suppressed. The application runtime does not use TestClient.
