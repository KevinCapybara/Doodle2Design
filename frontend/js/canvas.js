export class DrawingCanvas {
  constructor(canvas) {
    this.canvas = canvas;
    this.context = canvas.getContext('2d');
    this.layer = document.createElement('canvas');
    this.layer.width = canvas.width; this.layer.height = canvas.height;
    this.ink = this.layer.getContext('2d', {willReadFrequently: true});
    this.background = '#ffffff'; this.color = '#222a27'; this.size = 8; this.tool = 'brush'; this.history = []; this.pointer = null;
    this.undoButton = document.querySelector('#canvas-undo');
    this.initializeTools(); this.render();
    canvas.addEventListener('pointerdown', event => this.start(event));
    canvas.addEventListener('pointermove', event => this.move(event));
    for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) canvas.addEventListener(name, () => this.end());
    document.addEventListener('keydown', event => {
      if (document.body.dataset.phase === 'input' && !document.querySelector('#draw-panel').hidden && (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {event.preventDefault(); this.undo();}
    });
  }
  initializeTools() {
    document.querySelectorAll('[data-tool]').forEach(button => button.addEventListener('click', () => {
      this.tool = button.dataset.tool;
      document.querySelectorAll('[data-tool]').forEach(item => {item.classList.toggle('selected', item === button); item.setAttribute('aria-pressed', String(item === button));});
    }));
    const palette = ['#222a27', '#faf7e9', '#9eb48f', '#e3b18e', '#c88182', '#829db9', '#bdabe1', '#e2d17b'];
    for (const color of palette) {
      const button = document.createElement('button'); button.style.setProperty('--swatch', color); button.setAttribute('aria-label', `Use ${color}`); button.setAttribute('aria-pressed', String(color === this.color)); button.dataset.color = color;
      button.addEventListener('click', () => this.setColor(color)); document.querySelector('#brush-swatches').append(button);
    }
    document.querySelector('#brush-color').addEventListener('input', event => this.setColor(event.target.value));
    document.querySelector('#brush-size').addEventListener('input', event => {this.size = Number(event.target.value); document.querySelector('#brush-size-value').value = this.size;});
    document.querySelector('#canvas-background').addEventListener('input', event => {this.snapshot(); this.background = event.target.value; this.render();});
    this.undoButton.addEventListener('click', () => this.undo());
    document.querySelector('#canvas-clear').addEventListener('click', () => {this.snapshot(); this.ink.clearRect(0, 0, this.layer.width, this.layer.height); this.render();});
  }
  setColor(color) {
    this.color = color; document.querySelector('#brush-color').value = color;
    document.querySelectorAll('[data-color]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.color === color)));
  }
  snapshot() {
    this.history.push({data: this.ink.getImageData(0, 0, this.layer.width, this.layer.height), background: this.background});
    if (this.history.length > 20) this.history.shift(); this.undoButton.disabled = false;
  }
  undo() {
    if (!this.history.length || this.pointer !== null) return;
    const prior = this.history.pop(); this.ink.putImageData(prior.data, 0, 0); this.background = prior.background; document.querySelector('#canvas-background').value = this.background;
    this.undoButton.disabled = !this.history.length; this.render();
  }
  point(event) {
    const bounds = this.canvas.getBoundingClientRect();
    return {x: (event.clientX-bounds.left)*this.canvas.width/bounds.width, y: (event.clientY-bounds.top)*this.canvas.height/bounds.height};
  }
  start(event) {
    if (this.pointer !== null || event.button !== 0) return;
    event.preventDefault(); this.pointer = event.pointerId; this.canvas.setPointerCapture(event.pointerId); this.snapshot(); this.origin = this.point(event); this.previous = this.origin;
    this.before = this.ink.getImageData(0, 0, this.layer.width, this.layer.height); this.paint(this.origin);
  }
  move(event) {
    if (event.pointerId !== this.pointer) return; event.preventDefault(); this.paint(this.point(event));
  }
  paint(point) {
    const ctx = this.ink;
    ctx.globalCompositeOperation = this.tool === 'eraser' ? 'destination-out' : 'source-over';
    ctx.strokeStyle = this.color; ctx.fillStyle = this.color; ctx.lineWidth = this.tool === 'eraser' ? this.size*2 : this.size; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    if (this.tool === 'brush' || this.tool === 'eraser') {
      ctx.beginPath(); ctx.moveTo(this.previous.x, this.previous.y); ctx.lineTo(point.x+.01, point.y+.01); ctx.stroke();
    } else {
      ctx.putImageData(this.before, 0, 0); ctx.beginPath();
      if (this.tool === 'rectangle') ctx.rect(this.origin.x, this.origin.y, point.x-this.origin.x, point.y-this.origin.y);
      else if (this.tool === 'circle') ctx.ellipse((this.origin.x+point.x)/2, (this.origin.y+point.y)/2, Math.abs(point.x-this.origin.x)/2, Math.abs(point.y-this.origin.y)/2, 0, 0, Math.PI*2);
      else {ctx.moveTo(this.origin.x, this.origin.y); ctx.lineTo(point.x, point.y);} ctx.stroke();
    }
    ctx.globalCompositeOperation = 'source-over'; this.previous = point; this.render();
  }
  end() {this.pointer = null; this.before = null;}
  render() {this.context.fillStyle = this.background; this.context.fillRect(0, 0, this.canvas.width, this.canvas.height); this.context.drawImage(this.layer, 0, 0);}
  blob() {return new Promise((resolve, reject) => this.canvas.toBlob(blob => blob ? resolve(blob) : reject(new Error('Could not export your drawing. Please try again.')), 'image/png'));}
}
