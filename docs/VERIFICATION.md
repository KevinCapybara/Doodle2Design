# Verification — Doodle2Design

Verified locally on Windows on 2026-10-17 with Python 3.12 and headless Microsoft Edge. No live paid model requests were made.

## Automated backend checks

`python -m pytest -q`: **24 passed**, approximately 3 seconds.

- Strict token schema: exact fields, hex colors, enums and heading-weight bounds.
- Text/background contrast correction reaches 4.5:1 and changes no other token.
- JPEG preparation handles transparency and limits the longest side to 768 px.
- Distinct input palettes produce different offline tokens.
- Exactly ten same-category pairs, 20 unique ids, all four categories at least twice, reproducible seeded plans.
- Full draw and upload session flows, cached extraction, token file creation, latest-token retrieval and reset.
- Corrupt/oversized/excess uploads rejected; unknown sessions and incorrect phases rejected.
- Duplicate vote retries do not advance a round twice; prefetch does not advance the session.
- Default-theme reset preserves a completed session for reapplication when requested.
- Markdown fences parsed, invalid JSON retried once, failures in baseline/planning/extraction return valid offline results.

The installed Starlette version emits one dependency deprecation warning about its TestClient httpx adapter. Tests pass; the application runtime does not use that adapter. The warning is not suppressed.

## Browser checks

- Both input paths complete the entire flow, independently through browser controls.
- Mouse strokes, shape dragging, background/brush colors, size changes and undo work. Undo restores the exact prior canvas bitmap.
- Touch input draws on the canvas; canvas display retains its 3:2 coordinate ratio at all tested widths.
- Modal opens and closes by Escape; image choices work with arrow keys and clicks.
- All ten A/B screens have **zero visible text**, including no header/footer/toasts/badge. Twenty reference URLs are distinct.
- Final-click extraction and preview complete offline in approximately 1.3 seconds, including the intentional brief animation. A full ten-choice flow takes roughly 4.2 seconds with automated input.
- Live preview changes root CSS variables; the demo body structure stays the same. Before/after restores defaults and reapplies tokens without replacing HTML.
- CSS download produces `doodle2design-theme.css`; reset/reapply and restarting the wizard work.
- Upload accepts three references, rejects a fourth, removes a thumbnail and proceeds with the remaining references.
- Wizard views tested at **320, 768, 1024 and 1440 px**. Demo themes additionally tested at **286, 320, 686, 768, 811, 914, 1024 and 1440 px**, including the actual iframe widths.
- No horizontal document overflow in the tested states, and **zero browser console errors** in both complete flows.
- Neon-dark input produced **Midnight Structure** (`#141517` background); pastel input produced **Daylight Structure** (`#edeff7` background) in the captured comparison sessions. Randomized comparison plans can change the precise palette between sessions.
- Full demo pages and mobile views were visually inspected. Screenshots are in `docs/screenshots/`.

## Launcher checks

- Initial startup installs dependencies, creates `.env`, starts uvicorn, and passes `/healthz` on 8000.
- Restart with unchanged requirements skips dependency installation using the requirements hash marker.
- An isolated fresh directory, without `.venv`, `.env`, manifest or images, successfully creates its environment, installs dependencies, generates 100 references and launches on **8001** while 8000 is occupied.
- Browser auto-opening is implemented with `webbrowser.open`; this verification set `VIBE_NO_BROWSER=1` to avoid creating extra visible tabs. A preview was opened through the app panel.
- Backend/scripts pass Python compilation. The repository has no npm dependency or frontend build.

## Review and limits

Reviewed against the complete supplied specification: local-only storage and hosting, in-memory UUID sessions, four-category comparison coverage, exact token contracts, fixed deterministic CSS vocabulary, same-origin iframe messaging, validated image content and constrained model output. Keys remain server-side, filenames are never used as upload destinations, and model text is rendered through `textContent`.

The integration uses the default `claude-sonnet-4-6` string and `VLM_MODEL` override as specified. Real Anthropic output, service availability and paid-model latency remain **unverified without a configured API key**. All network failure paths used by the app are covered by local fakes or deterministic fallback tests. The original “under 15 seconds with the real VLM” target cannot be promised for an external service; the app enforces a 14-second model-extraction deadline and falls back offline.

Optional adaptive replanning after round five and automated VLM image tagging are intentionally omitted from the MVP. Before/after, JSON download and CSS export are implemented.
