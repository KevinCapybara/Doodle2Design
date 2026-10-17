export class ReferenceUpload {
  constructor() {
    this.files = []; this.urls = [];
    this.input = document.querySelector('#upload-files'); this.zone = document.querySelector('#drop-zone');
    this.input.addEventListener('change', () => {this.add([...this.input.files]); this.input.value = '';});
    for (const event of ['dragenter', 'dragover']) this.zone.addEventListener(event, e => {e.preventDefault(); this.zone.classList.add('dragging');});
    for (const event of ['dragleave', 'drop']) this.zone.addEventListener(event, e => {e.preventDefault(); this.zone.classList.remove('dragging');});
    this.zone.addEventListener('drop', e => this.add([...e.dataTransfer.files]));
    this.zone.addEventListener('keydown', event => {if (['Enter', ' '].includes(event.key)) {event.preventDefault(); this.input.click();}});
  }
  add(files) {
    let error = '';
    if (this.files.length+files.length > 3) error = 'Choose up to 3 images. Remove one below to make room.';
    else if (files.some(file => !['image/png', 'image/jpeg', 'image/webp'].includes(file.type))) error = 'Choose PNG, JPG or WebP images.';
    else if (files.some(file => file.size > 8*1024*1024)) error = 'Each image must be 8 MB or smaller.';
    document.querySelector('#upload-error').textContent = error;
    if (error) return;
    this.files.push(...files); this.render();
  }
  render() {
    this.urls.forEach(url => URL.revokeObjectURL(url)); this.urls = [];
    const container = document.querySelector('#upload-thumbnails'); container.replaceChildren();
    this.files.forEach((file, index) => {
      const wrapper = document.createElement('div'); wrapper.className = 'upload-thumbnail';
      const image = document.createElement('img'); image.src = URL.createObjectURL(file); this.urls.push(image.src); image.alt = `Reference ${index+1}`;
      const name = document.createElement('p'); name.textContent = file.name;
      const remove = document.createElement('button'); remove.textContent = '×'; remove.setAttribute('aria-label', `Remove reference ${index+1}`);
      remove.addEventListener('click', () => {this.files.splice(index, 1); document.querySelector('#upload-error').textContent = ''; this.render(); document.querySelector('#drop-zone').focus();});
      wrapper.append(image, remove, name); container.append(wrapper);
    });
    document.querySelector('#upload-done').disabled = this.files.length === 0;
  }
  clear() {this.files = []; this.render(); document.querySelector('#upload-error').textContent = '';}
}
