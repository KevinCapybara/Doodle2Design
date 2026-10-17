# Doodle2Design implementation plan

The supplied 16-page specification is the product contract, with the user's naming correction: Doodle2Design. The original extracted source is in SPEC.extracted.txt.

1. Local launcher, FastAPI shell, health and static routes.
2. Deterministic procedural library, manifest tooling, image index.
3. Strict token schemas, input analysis, offline extraction, selection, CSS mapping.
4. Fixed Northwind Analytics demo with default theme and live token application.
5. Full in-memory session API, file validation, contrast correction, offline tests.
6. Drawing/upload wizard, ten image-only rounds, extraction, results and iframe.
7. Anthropic baseline/planning/extraction with validated output, retry and fallback.
8. Browser verification, launcher verification, documentation and polish.

All eight implementation stages are complete. Final evidence and remaining live-service verification limits are in [VERIFICATION.md](VERIFICATION.md).

## Boundaries and choices

- Localhost only, no auth/database/cloud/deployment/npm/build pipeline.
- Images and model output are untrusted: decode uploads, enforce size/type/pixel limits, validate all token fields, use fixed CSS mappings and textContent.
- API keys stay server-side. Uploads remain in session memory; only the latest theme is written to disk.
- Python stdlib plus the specified Python packages; pytest and httpx are added for offline verification.
- Same-origin iframe messages are checked before applying tokens.
- Model calls have 30-second per-attempt limits and one retry. A 14-second overall extraction budget falls back offline to keep the final transition bounded; real model latency cannot be guaranteed.

## Official references

- https://fastapi.tiangolo.com/tutorial/request-files/ (multipart UploadFile)
- https://fastapi.tiangolo.com/advanced/events/ (lifespan)
- https://platform.claude.com/docs/en/api/sdks/python (AsyncAnthropic, timeouts and retries)
- https://platform.claude.com/docs/en/build-with-claude/working-with-messages (base64 image content)
