import {tokenVariables} from '/demo/token_map.js';

export class ThemeResult {
  constructor({api, sessionId, notify, restart}) {
    this.api = api; this.sessionId = sessionId; this.notify = notify; this.restart = restart;
    this.frame = document.querySelector('#demo-preview'); this.after = true; this.result = null;
    document.querySelector('#preview-before').addEventListener('click', () => this.setPreview(false));
    document.querySelector('#preview-after').addEventListener('click', () => this.setPreview(true));
    this.frame.addEventListener('load', () => this.push());
    window.addEventListener('message', event => {if (event.origin === location.origin && event.source === this.frame.contentWindow && event.data?.type === 'demo-ready') this.push();});
    document.querySelector('#copy-json').addEventListener('click', () => this.copy());
    document.querySelector('#download-json').addEventListener('click', () => this.download('json'));
    document.querySelector('#download-css').addEventListener('click', () => this.download('css'));
    document.querySelector('#try-again').addEventListener('click', () => this.restart());
    document.querySelector('#reset-demo').addEventListener('click', () => this.reset());
    document.querySelector('#apply-demo').addEventListener('click', () => this.apply());
  }
  render(result) {
    this.result = result; const tokens = result.tokens;
    document.querySelector('#result-name').textContent = tokens.name;
    document.querySelector('#result-rationale').textContent = tokens.rationale;
    document.querySelector('#tokens-json').textContent = JSON.stringify(tokens, null, 2);
    document.querySelector('#baseline-summary').textContent = result.baseline.summary;
    const attributes = document.querySelector('#baseline-attributes'); attributes.replaceChildren();
    result.baseline.attributes.forEach(attribute => {const tag = document.createElement('span'); tag.textContent = attribute; attributes.append(tag);});
    const swatches = document.querySelector('#result-swatches'); swatches.replaceChildren();
    for (const [name, hex] of Object.entries(tokens.colors)) {
      const swatch = document.createElement('div'); swatch.className = 'result-swatch'; swatch.title = `${name}: ${hex}`;
      const chip = document.createElement('i'); chip.style.setProperty('--swatch', hex);
      const label = document.createElement('span'); label.textContent = hex; swatch.append(chip, label); swatches.append(swatch);
    }
    this.after = true; this.frame.src = '/demo/?default=1'; this.setPreview(true);
  }
  setPreview(after) {
    this.after = after;
    for (const [id, active] of [['#preview-before', !after], ['#preview-after', after]]) {const button = document.querySelector(id); button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active));}
    document.querySelector('#demo-fullscreen').href = after ? '/demo/' : '/demo/?default=1'; this.push();
  }
  push() {
    if (this.result && this.frame.contentWindow) this.frame.contentWindow.postMessage({type: 'apply-vibe', tokens: this.result.tokens, reset: !this.after}, location.origin);
  }
  async copy() {
    try {await navigator.clipboard.writeText(JSON.stringify(this.result.tokens, null, 2)); this.notify('Design tokens copied.');}
    catch {this.notify('Clipboard unavailable. Use Download JSON to save your tokens.', true);}
  }
  download(format) {
    const tokens = this.result.tokens;
    const content = format === 'json' ? JSON.stringify(tokens, null, 2) : ':root {\n'+Object.entries(tokenVariables(tokens)).map(([key, value]) => `  ${key}: ${value};`).join('\n')+'\n}\n';
    const blob = new Blob([content], {type: format === 'json' ? 'application/json' : 'text/css'});
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `doodle2design-theme.${format}`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async apply() {
    const button = document.querySelector('#apply-demo'); button.disabled = true;
    try {await this.api('/api/extract', {method: 'POST', body: {session_id: this.sessionId()}}); this.setPreview(true); this.frame.scrollIntoView({behavior: 'smooth', block: 'center'}); this.notify('Your theme is applied to the demo site.');}
    catch (error) {this.notify(error.message, true);} finally {button.disabled = false;}
  }
  async reset() {
    const button = document.querySelector('#reset-demo'); button.disabled = true;
    try {await this.api('/api/reset', {method: 'POST', body: {session_id: this.sessionId(), demo_only: true}}); this.setPreview(false); this.notify('Demo restored to its default theme.');}
    catch (error) {this.notify(error.message, true);} finally {button.disabled = false;}
  }
}
