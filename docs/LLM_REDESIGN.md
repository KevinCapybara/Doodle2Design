# Document-led LLM redesign

The October 17 request replaces the result page's preset renderer with LLM-generated
HTML, CSS and JavaScript. The drawing/upload and ten A/B rounds remain the taste
calibration step. The older token renderer remains available under /demo/ for
compatibility; it does not produce the new AI redesign.

## Pipeline

1. Extract the baseline and VibeTokens using the existing analysis pipeline.
   Offline fallback remains available for this step and is identified in the UI.
2. Start POST /api/redesign with the completed session_id. The LLM sees original
   images, all ten winners, accepted/rejected tags, mood and sentiment, plus
   descriptions of all 30 supplied themes. It chooses one exact document title.
3. Give the model the selected complete design-system section and original
   Northwind content. Generate body markup, full CSS, JavaScript and a change
   summary. Layout, hierarchy, button shapes, cards, SVG illustrations, texture,
   and motion are explicitly in scope.
4. Validate the structured response, business data and required sections; serve
   the generated artifact in an isolated browser preview. The UI polls status,
   shows the match reason, compares before/after and downloads HTML or CSS.

All original DOCX files, extracted briefs and hashes are in design_prompts/.
The archive supplied Word documents rather than PDFs. Exact filename stems
define theme names; Professional intentionally retains its filename even though
its brief describes a serif aesthetic. The generic role preamble is excluded;
design briefs are reference data, not agent/tool/permission instructions.

## Configuration and lifecycle

Set OPENAI_API_KEY and AI_PROVIDER=openai for OpenAI, or ANTHROPIC_API_KEY
and AI_PROVIDER=anthropic for Anthropic. AI_PROVIDER=auto prefers a configured
OpenAI key and otherwise selects Anthropic. Explicit selection never silently
routes data to the other service. Set VIBE_MOCK=0 to enable AI.

OpenAI uses the Responses API with normalized inline JPEG inputs, JSON mode,
streaming, store=false and backend Pydantic validation. OPENAI_MODEL defaults to
gpt-5.4; OPENAI_VISION_MODEL and OPENAI_REDESIGN_MODEL optionally override it
per stage. No hosted tools are enabled. Anthropic retains VLM_MODEL (default
claude-sonnet-4-6) and REDESIGN_MODEL. Claude model names never reach OpenAI.

Keys stay server-side in the ignored .env file. Restart after changing environment
settings; restarting loses the current in-memory session.

No key means the app can still calibrate taste, but shows an explicit setup error
for generation. There is no simulated success or preset website fallback.
Taste extraction may use offline analysis even when a subsequent generation works.

Generation uses the selected provider's async streaming API, at most two attempts per
stage (including schema failures), 210 seconds per attempt and a 480-second total
job budget including queue time. Transport reads time out after 90 seconds without
data. Two jobs can run concurrently and at most four can be pending. Repeated
POSTs reuse active or completed work; an error can be retried explicitly.
No new paid generation occurs for before/after, reapply or downloads.

Jobs and artifacts live in bounded process-local sessions. Reset cancels the
session's running job and discards its artifact; server shutdown cancels all
jobs. Active jobs are excluded from idle cleanup. Download the HTML to keep it
across restarts. A generated page is not automatically written over repository
source files or executed on the server.

## Browser boundary

The host page keeps its existing CSP. Generated preview and HTML download
responses use a separate CSP with sandbox allow-scripts allow-forms (no allow-same-origin),
no connections, external scripts, external resources, frames, objects, form
submissions or base URLs. The iframe has sandbox="allow-scripts allow-forms".
allow-forms enables local validation and submit handlers; form-action none
blocks actual submissions. The trusted original preview uses its normal origin. Generated code has an opaque
origin and cannot access the host DOM, cookies, storage or local API responses.
The exported HTML embeds its restrictive resource policy before generated content.
Document-level tags and raw-text closing tag breakouts are rejected.

This permits local animation and DOM interaction, without granting access to
application state. The model must use inline SVG/CSS and system fonts, adapting
font suggestions and framework examples in the briefs to this self-contained
runtime. The host adds motion pause/resume and a reduced-motion CSS override.
The contact form provides local demo feedback; there is no submission service.

Output validation checks structure and selected business facts; it cannot prove
every generated layout looks good or every interaction behaves correctly. Model
quality varies. Network/service/key errors surface as retryable UI states.

## Interfaces

- POST /api/redesign: session_id; 202 queued/running, 200 cached ready.
- GET /api/redesign?session_id=...: idle/queued/matching/generating/ready/error.
- GET /api/redesign/preview?session_id=...: isolated generated HTML.
- GET /api/redesign/download?session_id=...: complete standalone HTML attachment.
- GET /api/redesign/css?session_id=...: model-written CSS attachment.

Original extraction/token interfaces remain compatible.

Implementation references:
- [OpenAI Python SDK](https://developers.openai.com/api/reference/python)
- [OpenAI image inputs](https://developers.openai.com/api/docs/guides/images-vision)
- [OpenAI streaming](https://developers.openai.com/api/docs/guides/streaming-responses)
- [OpenAI JSON mode and validation](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Anthropic Python SDK streaming](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)
- [MDN iframe sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe)
- [MDN CSP sandbox](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/sandbox)
