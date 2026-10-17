import {tokenVariables} from './token_map.js';
let appliedKeys = [];
window.resetVibe = function () {
  for (const key of appliedKeys) document.documentElement.style.removeProperty(key);
  appliedKeys = [];
};
window.applyVibe = function (tokens) {
  const variables = tokenVariables(tokens);
  window.resetVibe();
  for (const [key, value] of Object.entries(variables)) document.documentElement.style.setProperty(key, value);
  appliedKeys = Object.keys(variables);
};
window.addEventListener('message', event => {
  if (event.origin !== location.origin || event.source !== window.parent || event.data?.type !== 'apply-vibe') return;
  try {
    if (event.data.reset) window.resetVibe(); else window.applyVibe(event.data.tokens);
  } catch (error) { console.warn('Rejected invalid theme:', error.message); }
});
if (!new URLSearchParams(location.search).has('default')) {
  try { const response = await fetch('/api/tokens'); if (response.ok) window.applyVibe(await response.json()); } catch { /* Keep default theme. */ }
}
window.parent.postMessage({type: 'demo-ready'}, location.origin);
document.querySelector('#contact-form').addEventListener('submit', event => {
  event.preventDefault();
  document.querySelector('#form-feedback').textContent = 'Thanks! This is a local demo, so your message stays in your browser.';
});
