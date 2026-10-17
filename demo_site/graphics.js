// Original local vector artwork. Colors come only from the validated token palette.
const imageUrl = body => `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800">${body}</svg>`)}")`;

function forest({primary, secondary, accent}) {
  const fir = 'M0 0 -26 65 -12 60 -53 132 -31 124 -82 214 -52 201 -107 297 -13 284 -13 344 13 344 13 284 107 297 52 201 82 214 31 124 53 132 12 60 26 65Z';
  const trees = (positions, fill, opacity) => `<g fill="${fill}" opacity="${opacity}">${positions.map(([x,y,s]) => `<path d="${fir}" transform="translate(${x} ${y}) scale(${s})"/>`).join('')}</g>`;
  return imageUrl(`
    <defs><radialGradient id="haze"><stop stop-color="${accent}" stop-opacity=".42"/><stop offset="1" stop-color="${accent}" stop-opacity="0"/></radialGradient></defs>
    <ellipse cx="660" cy="310" rx="500" ry="340" fill="url(#haze)"/>
    <circle cx="820" cy="180" r="82" fill="${accent}" opacity=".55"/>
    <path d="M0 490Q230 340 510 460T1200 400V800H0Z" fill="${secondary}" opacity=".18"/>
    ${trees([[70,180,1],[240,250,.8],[420,120,1.4],[670,190,1],[960,210,1],[1130,120,1.5]], secondary,.27)}
    <path d="M0 600Q360 430 660 565T1200 510V800H0Z" fill="${primary}" opacity=".12"/>
    ${trees([[30,320,1.2],[175,280,1.5],[350,380,1],[860,310,1.4],[1050,260,1.7],[1210,360,1.3]], primary,.58)}
    <path d="M0 730Q360 580 670 710T1200 670V800H0Z" fill="${primary}" opacity=".28"/>
    <g fill="none" stroke="${primary}" stroke-width="2" opacity=".3"><path d="M600 650q-22-80 30-133m-30 87q-53-3-56-45 45 0 56 45m15-52q-11-41 25-61 17 40-25 61"/></g>`);
}

function orbital({primary, secondary, accent}) {
  const stars = Array.from({length:45}, (_,i) => `<circle cx="${(i*197+41)%1200}" cy="${(i*131+67)%800}" r="${i%4===0?3:1.5}"/>`).join('');
  return imageUrl(`
    <defs><radialGradient id="planet"><stop stop-color="${secondary}"/><stop offset=".65" stop-color="${primary}"/><stop offset="1" stop-color="${primary}" stop-opacity=".15"/></radialGradient></defs>
    <g fill="${accent}" opacity=".6">${stars}</g>
    <circle cx="600" cy="370" r="220" fill="url(#planet)"/>
    <g fill="none" stroke="${primary}" stroke-width="2" opacity=".6" transform="rotate(-24 600 370)"><ellipse cx="600" cy="370" rx="490" ry="180"/><ellipse cx="600" cy="370" rx="430" ry="145"/><ellipse cx="600" cy="370" rx="510" ry="310" stroke-dasharray="4 16"/></g>
    <ellipse cx="600" cy="370" rx="160" ry="340" transform="rotate(38 600 370)" fill="none" stroke="${secondary}" stroke-width="2" opacity=".8"/>
    <circle cx="900" cy="222" r="25" fill="${accent}"/><circle cx="245" cy="490" r="13" fill="${secondary}"/>
    <path d="M923 540v55m-27-28h55M200 160v32m-16-16h32" stroke="${accent}" stroke-width="2"/>`);
}

function grid({primary, secondary, accent}) {
  return imageUrl(`
    <defs><pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M60 0H0V60" fill="none" stroke="${primary}" stroke-width="1" opacity=".2"/></pattern><pattern id="check" width="80" height="80" patternUnits="userSpaceOnUse"><path d="M0 0H40V40H0ZM40 40H80V80H40Z" fill="${primary}"/></pattern></defs>
    <rect width="1200" height="800" fill="url(#grid)"/>
    <rect x="95" y="130" width="260" height="410" fill="${primary}"/>
    <path d="M95 130 255 45 515 45 355 130ZM355 130 515 45V455L355 540Z" fill="${secondary}"/>
    <rect x="480" y="280" width="400" height="330" fill="${accent}"/>
    <path d="M480 280 640 195H1040L880 280ZM880 280 1040 195V525L880 610Z" fill="${primary}" opacity=".7"/>
    <rect x="110" y="580" width="280" height="160" fill="url(#check)" opacity=".8"/>
    <g stroke="${secondary}" stroke-width="5"><path d="M130 190H305M130 240H305M130 290H305M130 340H305M130 390H305"/></g>
    <path d="M920 670h180m-50-50 50 50-50 50" fill="none" stroke="${primary}" stroke-width="12"/>`);
}

function waves({primary, secondary, accent}) {
  return imageUrl(`
    <circle cx="900" cy="190" r="115" fill="${accent}"/>
    <path d="M0 720V410Q270 120 520 360T1200 270V800H0Z" fill="${secondary}" opacity=".28"/>
    <path d="M0 800V600Q310 290 640 530T1200 370V800Z" fill="${primary}" opacity=".45"/>
    <path d="M0 800V750Q270 450 610 660T1200 530V800Z" fill="${primary}"/>
    <g transform="translate(350 270)" fill="${accent}"><ellipse rx="38" ry="115"/><ellipse rx="38" ry="115" transform="rotate(60)"/><ellipse rx="38" ry="115" transform="rotate(120)"/><circle r="30" fill="${primary}"/></g>
    <g fill="none" stroke="${primary}" stroke-width="3" opacity=".65"><path d="M690 110q-230 80-130 270t-70 290M735 125q-230 80-130 270t-70 290M780 140q-230 80-130 270t-70 290"/></g>`);
}

export function sceneImage(motif, colors) {
  const scenes = {forest, orbital, grid, waves};
  return motif === 'none' ? 'none' : scenes[motif](colors);
}
