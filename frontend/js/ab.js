const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));

export class Comparisons {
  constructor({api, sessionId, finish, report}) {
    this.api = api; this.sessionId = sessionId; this.finish = finish; this.report = report;
    this.buttons = [document.querySelector('#ab-left'), document.querySelector('#ab-right')];
    this.buttons.forEach((button, index) => button.addEventListener('click', () => this.choose(index)));
    document.addEventListener('keydown', event => {
      if (document.body.dataset.phase !== 'ab' || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
      event.preventDefault(); this.choose(event.key === 'ArrowLeft' ? 0 : 1);
    });
    document.querySelector('#ab-retry').addEventListener('click', () => this.retry());
    this.winners = []; this.cached = null; this.busy = false; this.failedAction = null;
  }
  async start() {
    this.winners = []; this.cached = null; this.busy = false;
    const pair = await this.api(`/api/ab/next?session_id=${this.sessionId()}`);
    await this.show(pair);
  }
  async show(pair) {
    if (pair.done) {this.finish(this.winners); return;}
    const urls = [pair.left_url, pair.right_url];
    await Promise.all(urls.map(url => new Promise((resolve, reject) => {const image = new Image(); image.onload = resolve; image.onerror = () => reject(new Error('Reference image unavailable')); image.src = url;})));
    this.pair = pair;
    this.buttons.forEach((button, index) => {button.querySelector('img').src = urls[index]; button.classList.remove('winner', 'loser'); button.disabled = false;});
    const dots = document.querySelector('#ab-progress'); dots.replaceChildren(); dots.setAttribute('aria-valuenow', String(pair.round-1));
    for (let i=1; i<=10; i++) {const dot = document.createElement('i'); dot.className = i < pair.round ? 'done' : i === pair.round ? 'current' : ''; dots.append(dot);}
    this.busy = false; this.failedAction = null; document.querySelector('#ab-retry').hidden = true;
    this.preload(pair.round);
  }
  async preload(round) {
    if (round >= 10) return;
    try {
      const next = await this.api(`/api/ab/next?session_id=${this.sessionId()}&prefetch=true`);
      if (next.round !== round+1) return;
      this.cached = next;
      for (const src of [next.left_url, next.right_url]) {const image = new Image(); image.src = src;}
    } catch { /* The normal request can retry when the user chooses. */ }
  }
  async choose(index) {
    if (this.busy || !this.pair || document.body.dataset.phase !== 'ab') return;
    this.busy = true;
    const pair = this.pair;
    this.buttons.forEach((button, i) => {button.classList.add(i === index ? 'winner' : 'loser'); button.disabled = true;});
    const winner = index === 0 ? pair.left_id : pair.right_id;
    const loser = index === 0 ? pair.right_id : pair.left_id;
    const choice = {session_id: this.sessionId(), round: pair.round, winner_id: winner, loser_id: loser};
    const action = async () => {
      await Promise.all([this.api('/api/ab/choice', {method: 'POST', body: choice}), pause(230)]);
      if (this.winners.length < pair.round) this.winners.push(index === 0 ? pair.left_url : pair.right_url);
      if (pair.round === 10) {this.finish(this.winners); return;}
      const next = this.cached?.round === pair.round+1 ? this.cached : await this.api(`/api/ab/next?session_id=${this.sessionId()}`);
      this.cached = null; await this.show(next);
    };
    try {await action();} catch (error) {this.failedAction = action; document.querySelector('#ab-retry').hidden = false; this.report(error);}
  }
  async retry() {
    if (!this.failedAction) return;
    document.querySelector('#ab-retry').hidden = true;
    try {await this.failedAction();} catch (error) {document.querySelector('#ab-retry').hidden = false; this.report(error);}
  }
}
