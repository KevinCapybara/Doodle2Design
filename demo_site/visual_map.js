import {sceneImage} from './graphics.js';

const defaults = {motif:'none', layout:'split', motion:'none', button_style:'token', card_style:'solid'};
const allowed = {
  motif:['none','forest','orbital','grid','waves'], layout:['split','centered','poster'], motion:['none','calm','kinetic'],
  button_style:['token','pill','soft','cut','sharp'], card_style:['solid','glass','organic','outline','paper'],
};

export function visualVariables(input, colors) {
  if (input !== undefined && (input === null || typeof input !== 'object' || Array.isArray(input))) throw new Error('Invalid visuals');
  const visuals = {...defaults, ...input};
  for (const [key,value] of Object.entries(visuals)) {
    if (!Object.hasOwn(allowed,key) || !allowed[key].includes(value)) throw new Error(`Invalid visual ${key}`);
  }
  const {motif,layout,motion,button_style:button,card_style:card} = visuals;
  const image = sceneImage(motif,colors);
  const active = motif !== 'none';
  const variables = {
    '--scene-image':image, '--hero-art':image, '--scene-opacity':active ? (motif==='forest'?'.2':'.08'):'0',
    '--hero-art-opacity':active?'1':'0', '--orbit-opacity':active?'0':'1',
    '--art-background':active?'transparent':'var(--surface)', '--art-border-width':active?'0px':'var(--border-width)',
    '--art-radius':motif==='forest'?'48% 52% 38% 62% / 42% 46% 54% 58%':motif==='waves'?'50% 40% 30% 50%':'var(--radius)',
    '--art-overflow':active?'visible':'hidden', '--hero-decoration-opacity':motif==='forest'?'.12':'0',
    '--hero-columns':layout==='centered'?'minmax(0,1fr)':'minmax(0,1.2fr) minmax(0,1fr)',
    '--hero-text-align':layout==='centered'?'center':'left', '--hero-copy-order':layout==='poster'?'2':'0',
    '--hero-art-order':layout==='poster'?'1':'0', '--hero-copy-width':layout==='centered'?'52rem':'none',
    '--hero-copy-margin':layout==='centered'?'auto':'0', '--hero-actions-align':layout==='centered'?'center':'flex-start',
    '--hero-art-width':layout==='centered'?'min(100%, 54rem)':'100%', '--hero-art-height':layout==='centered'?'calc(var(--space)*18)':'calc(var(--space)*27)',
    '--hero-art-margin':layout==='centered'?'0 auto':'0', '--feature-columns':layout==='poster'?'2':'3',
    '--heading-style':motif==='forest'||motif==='waves'?'italic':'normal', '--heading-transform':motif==='grid'?'uppercase':'none',
    '--hero-type-size':motif==='forest'?'5rem':motif==='grid'?'4.2rem':'3.8rem',
    '--icon-background':active?'color-mix(in srgb, var(--primary) 10%, transparent)':'transparent',
    '--icon-radius':motif==='forest'?'50% 50% 15% 50%':'var(--radius)', '--icon-padding':active?'calc(var(--space)*.4)':'0px',
    '--feature-number':motif==='grid'? '"0" counter(feature)':'none', '--card-tilt':card==='paper'?'-1deg':'0deg',
    '--button-radius':{token:'var(--radius)',pill:'999px',soft:'14px',cut:'0px',sharp:'0px'}[button],
    '--button-clip':button==='cut'?'polygon(0 0,calc(100% - 12px) 0,100% 12px,100% 100%,12px 100%,0 calc(100% - 12px))':'none',
    '--button-extra-space':button==='pill'?'calc(var(--space)*.5)':'0px',
    '--card-radius':{solid:'var(--radius)',glass:'24px',organic:'40px 10px 40px 10px',outline:'0px',paper:'8px 32px 8px 32px'}[card],
    '--card-background':card==='glass'?'color-mix(in srgb, var(--surface) 72%, transparent)':card==='outline'?'transparent':'var(--surface)',
    '--card-blur':card==='glass'?'blur(18px)':'none',
    '--card-shadow':card==='glass'?'0 12px 48px color-mix(in srgb, var(--primary) 12%, transparent)':'var(--shadow)',
    '--navbar-background':card==='glass'?'color-mix(in srgb, var(--surface) 78%, transparent)':'var(--surface)',
  };
  const animated = motion !== 'none';
  Object.assign(variables, {
    '--motion-duration':motion==='calm'?'.8s':motion==='kinetic'?'.5s':'0s', '--motion-easing':motion==='calm'?'cubic-bezier(.2,.7,.2,1)':'cubic-bezier(.16,1,.3,1)',
    '--float-animation':animated?'theme-float':'none', '--float-duration':motion==='calm'?'8s':'4.5s',
    '--art-animation':animated?{none:'none',forest:'forest-sway',orbital:'orbital-turn',grid:'graphic-drift',waves:'paper-drift'}[motif]:'none',
    '--art-duration':motif==='orbital'?'70s':motion==='calm'?'18s':'10s',
    '--chart-animation':animated?'chart-grow':'none', '--chart-duration':motion==='calm'?'1.6s':'.9s',
    '--reveal-opacity':animated?'0':'1', '--reveal-distance':animated?(motion==='calm'?'20px':'32px'):'0px',
    '--hover-transform':animated?(motion==='calm'?'translateY(-3px)':'translateY(-4px) scale(1.015)'):'none',
    '--card-hover-lift':animated?'-5px':'0px', '--motion-control-display':animated?'inline-flex':'none',
  });
  return variables;
}
