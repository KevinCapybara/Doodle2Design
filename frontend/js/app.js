import {DrawingCanvas} from './canvas.js';
import {ReferenceUpload} from './upload.js';
import {Comparisons} from './ab.js';
import {ThemeResult} from './result.js';

const state = {phase: 'landing', mode: 'draw', sessionId: null, baseline: null, offline: false};
let toastTimeout;
function notify(message, error = false) {
  if (state.phase === 'ab') return;
  const toast = document.querySelector('#toast'); toast.textContent = message; toast.classList.toggle('error', error); toast.hidden = false;
  clearTimeout(toastTimeout); toastTimeout = setTimeout(() => {toast.hidden = true;}, error ? 6500 : 3500);
}
async function api(url, options = {}) {
  const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 145000);
  const headers = {};
  let body = options.body;
  if (body && !(body instanceof FormData)) {headers['Content-Type'] = 'application/json'; body = JSON.stringify(body);}
  try {
    const response = await fetch(url, {...options, headers, body, signal: controller.signal});
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Something could not be processed. Please try again.');
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('The request took too long. Please try again.');
    if (error instanceof TypeError) throw new Error('Could not reach the local server. Check that Doodle2Design is still running.');
    throw error;
  } finally {clearTimeout(timeout);}
}
function phase(name) {
  state.phase = name; document.body.dataset.phase = name;
  document.querySelectorAll('.phase').forEach(section => {section.hidden = section.id !== `phase-${name}`;});
  document.querySelector('#toast').hidden = true;
  document.querySelector('#offline-badge').hidden = !state.offline || name === 'ab';
  window.scrollTo(0, 0);
  if (name !== 'ab') document.querySelector(`#phase-${name} h1`)?.focus({preventScroll: true});
}
function busy(value) {document.querySelector('#busy-overlay').hidden = !value; document.querySelector('main').setAttribute('aria-busy', String(value)); document.querySelector('main').inert = value;}
const drawing = new DrawingCanvas(document.querySelector('#drawing-canvas'));
const upload = new ReferenceUpload();
const result = new ThemeResult({api, sessionId: () => state.sessionId, notify, restart});
const comparisons = new Comparisons({api, sessionId: () => state.sessionId, finish: extract, report: error => console.info('Comparison can be retried:', error.message)});

function input(mode) {
  state.mode = mode;
  document.querySelector('#draw-panel').hidden = mode !== 'draw'; document.querySelector('#upload-panel').hidden = mode !== 'upload';
  document.querySelector('#input-title').textContent = mode === 'draw' ? 'Start with a feeling.' : 'Collect what moves you.';
  document.querySelector('#input-subtitle').textContent = mode === 'draw' ? 'No right lines. No wrong colors. Make something that feels like you.' : 'A place, a texture, a moment. Choose images for how they feel.';
  phase('input');
}
document.querySelector('#start-draw').addEventListener('click', () => input('draw'));
document.querySelector('#start-upload').addEventListener('click', () => input('upload'));
document.querySelector('#input-back').addEventListener('click', () => phase('landing'));
document.querySelector('#draw-done').addEventListener('click', () => submit());
document.querySelector('#upload-done').addEventListener('click', () => submit());

async function submit() {
  busy(true);
  try {
    if (!state.sessionId) state.sessionId = (await api('/api/session', {method: 'POST'})).session_id;
    const files = state.mode === 'draw' ? [new File([await drawing.blob()], 'doodle.png', {type: 'image/png'})] : upload.files;
    const form = new FormData(); form.append('session_id', state.sessionId); form.append('mode', state.mode); files.forEach(file => form.append('files', file));
    if (!state.baseline) state.baseline = await api('/api/baseline', {method: 'POST', body: form});
    await comparisons.start(); busy(false); phase('ab');
    document.querySelector('#ab-left').focus({preventScroll: true});
  } catch (error) {busy(false); notify(error.message, true);}
}
async function extract(winners = comparisons.winners) {
  const artwork = document.querySelector('#extracting-art'); artwork.replaceChildren();
  winners.forEach((url, index) => {const image = document.createElement('img'); image.src = url; image.alt = ''; image.style.setProperty('--index', index); artwork.append(image);});
  const colors = document.querySelector('#extraction-swatches'); colors.replaceChildren();
  (state.baseline?.dominant_colors || ['#d6edab']).forEach((color, index) => {const swatch = document.createElement('i'); swatch.style.setProperty('--swatch', color); swatch.style.setProperty('--index', index); colors.append(swatch);});
  phase('extracting'); document.querySelector('#extract-retry').hidden = true;
  try {
    const [response] = await Promise.all([api('/api/extract', {method: 'POST', body: {session_id: state.sessionId}}), new Promise(resolve => setTimeout(resolve, matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 950))]);
    state.offline = response.degraded; result.render(response); phase('result');
  } catch (error) {notify(error.message, true); document.querySelector('#extract-retry').hidden = false;}
}
document.querySelector('#extract-retry').addEventListener('click', () => extract());
async function restart() {
  busy(true);
  try {
    if (state.sessionId) await api('/api/reset', {method: 'POST', body: {session_id: state.sessionId}});
    state.sessionId = null; state.baseline = null; upload.clear();
    result.stop(); result.frame.src = 'about:blank'; result.result = null;
    phase('landing');
  } catch (error) {notify(error.message, true);} finally {busy(false); if (state.phase === 'landing') document.querySelector('#landing-title').focus({preventScroll: true});}
}
const dialog = document.querySelector('#how-dialog');
document.querySelector('#how-button').addEventListener('click', () => dialog.showModal());
dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {if (event.target === dialog) {const b = dialog.getBoundingClientRect(); if (event.clientX < b.left || event.clientX > b.right || event.clientY < b.top || event.clientY > b.bottom) dialog.close();}});
api('/api/config').then(config => {state.offline = config.offline; document.querySelector('#offline-badge').hidden = !config.offline || state.phase === 'ab';}).catch(error => notify(error.message, true));
