export class ThemeResult {
  constructor({api, sessionId, notify, restart}) {
    Object.assign(this, {api, sessionId, notify, restart});
    this.frame = document.querySelector('#demo-preview');
    this.result = null; this.generated = null; this.after = false; this.version = 0;
    document.querySelector('#preview-before').addEventListener('click', () => this.setPreview(false));
    document.querySelector('#preview-after').addEventListener('click', () => this.setPreview(true));
    document.querySelector('#copy-json').addEventListener('click', () => this.copy());
    document.querySelector('#download-json').addEventListener('click', () => this.downloadTokens());
    document.querySelector('#download-css').addEventListener('click', () => this.downloadCode('css'));
    document.querySelector('#download-html').addEventListener('click', () => this.downloadCode('download'));
    document.querySelector('#try-again').addEventListener('click', () => this.restart());
    document.querySelector('#reset-demo').addEventListener('click', () => {this.setPreview(false); this.notify('Showing the original website. Your generated design is saved.');});
    document.querySelector('#apply-demo').addEventListener('click', () => this.generated ? this.setPreview(true) : this.startGeneration());
    document.querySelector('#generation-retry').addEventListener('click', () => this.startGeneration());
  }
  stop() {this.version++; clearTimeout(this.pollTimer); this.generated = null;}
  render(result) {
    this.stop(); this.result = result;
    const tokens = result.tokens;
    document.querySelector('#result-name').textContent = 'Finding your design…';
    document.querySelector('#result-rationale').textContent = 'Your visual preferences will guide the theme and the complete website redesign.';
    document.querySelector('#tokens-json').textContent = JSON.stringify(tokens, null, 2);
    document.querySelector('#baseline-summary').textContent = result.baseline.summary;
    document.querySelector('#taste-source').textContent = result.degraded ? 'Taste profile includes offline analysis. Theme selection and website generation use the LLM.' : 'Your drawing and choices were analyzed with AI.';
    const attributes = document.querySelector('#baseline-attributes'); attributes.replaceChildren();
    result.baseline.attributes.forEach(attribute => {const tag = document.createElement('span'); tag.textContent = attribute; attributes.append(tag);});
    const swatches = document.querySelector('#result-swatches'); swatches.replaceChildren();
    for (const [name, hex] of Object.entries(tokens.colors)) {
      const swatch = document.createElement('div'); swatch.className = 'result-swatch'; swatch.title = name + ': ' + hex;
      const chip = document.createElement('i'); chip.style.setProperty('--swatch', hex);
      const label = document.createElement('span'); label.textContent = hex; swatch.append(chip, label); swatches.append(swatch);
    }
    this.setPreview(false);
    this.startGeneration();
  }
  showStatus(status) {
    const active = ['queued', 'matching', 'generating'].includes(status.phase);
    const messages = {queued: 'Your design is queued.', matching: 'Matching your vibe to one of 30 design themes…', generating: 'Generating a complete ' + (status.theme || '') + ' website…', ready: 'Your LLM-generated website is ready.', error: 'Website generation needs attention.'};
    const panel = document.querySelector('#generation-panel');
    panel.dataset.state = status.phase; panel.setAttribute('aria-busy', String(active));
    document.querySelector('#generation-status').textContent = messages[status.phase] || 'Preparing your design…';
    document.querySelector('#generation-detail').textContent = status.error || (active ? 'The model is composing layouts, illustrations, button shapes and animations. This can take a few minutes.' : status.summary || '');
    document.querySelector('#generation-retry').hidden = status.phase !== 'error';
    document.querySelector('#generation-model').textContent = status.model ? 'Model: ' + status.model : '';
    if (status.theme) {
      document.querySelector('#result-name').textContent = status.theme;
      document.querySelector('#result-rationale').textContent = status.reason || '';
    } else if (status.phase === 'error') {
      document.querySelector('#result-name').textContent = 'Your vibe is ready.';
    }
    document.querySelector('#preview-after').disabled = !this.generated;
    document.querySelector('#download-css').disabled = !this.generated;
    document.querySelector('#download-html').disabled = !this.generated;
    const apply = document.querySelector('#apply-demo');
    apply.disabled = active;
    apply.textContent = active ? 'Designing your website…' : this.generated ? 'Show redesigned site ↗' : 'Generate website ↗';
  }
  async startGeneration() {
    const version = ++this.version;
    clearTimeout(this.pollTimer);
    this.showStatus({phase: 'matching'});
    try {
      const status = await this.api('/api/redesign', {method: 'POST', body: {session_id: this.sessionId()}});
      if (version !== this.version) return;
      this.acceptStatus(status, version);
    } catch (error) {
      if (version === this.version) this.showStatus({phase: 'error', error: error.message});
    }
  }
  acceptStatus(status, version) {
    if (version !== this.version) return;
    if (status.phase === 'ready') {
      this.generated = status; this.showStatus(status); this.setPreview(true);
      return;
    }
    this.showStatus(status);
    if (['queued', 'matching', 'generating'].includes(status.phase)) {
      this.pollTimer = setTimeout(async () => {
        try {
          const next = await this.api('/api/redesign?session_id=' + encodeURIComponent(this.sessionId()));
          this.acceptStatus(next, version);
        } catch (error) {
          if (version === this.version) this.showStatus({phase: 'error', error: error.message + ' Retry to reconnect to your saved generation job.'});
        }
      }, 1800);
    }
  }
  setPreview(after) {
    this.after = Boolean(after && this.generated);
    const url = this.after ? this.generated.preview_url : '/demo/?default=1';
    // Generated code stays opaque; only the trusted original uses its normal origin.
    this.frame.setAttribute('sandbox', this.after ? 'allow-scripts allow-forms' : 'allow-scripts allow-same-origin');
    if (this.frame.getAttribute('src') !== url) this.frame.src = url;
    for (const [id, active] of [['#preview-before', !this.after], ['#preview-after', this.after]]) {
      const button = document.querySelector(id); button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));
    }
    document.querySelector('#demo-fullscreen').href = url;
  }
  async copy() {
    try {await navigator.clipboard.writeText(JSON.stringify(this.result.tokens, null, 2)); this.notify('Taste profile copied.');}
    catch {this.notify('Clipboard unavailable. Use Download JSON.', true);}
  }
  downloadTokens() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(this.result.tokens, null, 2)], {type: 'application/json'}));
    const link = document.createElement('a'); link.href = url; link.download = 'doodle2design-taste.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  downloadCode(kind) {
    if (!this.generated) return;
    const link = document.createElement('a');
    link.href = '/api/redesign/' + kind + '?session_id=' + encodeURIComponent(this.sessionId());
    link.download = kind === 'css' ? 'doodle2design-website.css' : 'doodle2design-website.html';
    link.click();
  }
}
