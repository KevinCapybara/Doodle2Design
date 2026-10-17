// Source: https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API
export function initializeMotion() {
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      for (const entry of entries) {
        if (entry.isIntersecting) {entry.target.classList.add('is-visible'); observer.unobserve(entry.target);}
      }
    }, {threshold:.08});
    document.querySelectorAll('.hero>div:first-child,.section-heading,.features .card,.dashboard,.pricing .card,.contact>div,.contact form,.chart').forEach((element,index) => {
      element.classList.add('theme-reveal');
      element.style.setProperty('--reveal-delay',`${(index%3)*.08}s`);
      observer.observe(element);
    });
  }
  const toggle = document.querySelector('#motion-toggle');
  toggle.addEventListener('click', () => {
    const paused = document.documentElement.classList.toggle('motion-paused');
    toggle.textContent = paused ? 'Resume motion ▷' : 'Pause motion Ⅱ';
    toggle.setAttribute('aria-pressed',String(paused));
  });
}
