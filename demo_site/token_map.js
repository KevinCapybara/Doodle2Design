// The model selects vocabulary. Only this deterministic map produces CSS.
const fonts = {serif: "Georgia, 'Times New Roman', serif", sans: 'Inter, system-ui, sans-serif', mono: "'JetBrains Mono', ui-monospace, monospace", display: "'Trebuchet MS', 'Arial Black', sans-serif"};
const maps = {
  letter_spacing: {tight: '-0.03em', normal: '0', wide: '0.08em'},
  scale: {compact: '0.92', normal: '1', spacious: '1.12'},
  radius: {sharp: '0px', soft: '6px', round: '16px', pill: '999px'},
  border_width: {none: '0px', thin: '1px', thick: '3px'},
  density: {tight: '0.75rem', normal: '1rem', airy: '1.5rem'},
  shadow: {flat: 'none', soft: '0 4px 16px rgba(0,0,0,.12)', hard: '6px 6px 0 var(--text)', neumorphic: '8px 8px 16px rgba(0,0,0,.25), -8px -8px 16px rgba(255,255,255,.06)', glow: '0 0 24px var(--primary)'},
  gradient: {none: 'none', subtle: 'linear-gradient(135deg, var(--surface), var(--bg))', bold: 'linear-gradient(135deg, var(--primary), var(--secondary))'},
  texture: {none: '0', grain: '0.08'},
};
export function tokenVariables(tokens) {
  const variables = {};
  for (const key of ['bg', 'surface', 'text', 'text_muted', 'primary', 'secondary', 'accent', 'border']) {
    const value = tokens.colors?.[key];
    if (!/^#[0-9a-fA-F]{6}$/.test(value)) throw new Error('Invalid theme color');
    variables[`--${key.replaceAll('_', '-')}`] = value;
  }
  const {typography: t, geometry: g, effects: e} = tokens;
  if (!t || !g || !e || !Object.hasOwn(fonts, t.heading_font) || !['serif', 'sans', 'mono'].includes(t.body_font) || !Number.isInteger(t.heading_weight) || t.heading_weight < 100 || t.heading_weight > 900 || t.heading_weight % 100) throw new Error('Invalid typography');
  variables['--font-heading'] = fonts[t.heading_font]; variables['--font-body'] = fonts[t.body_font]; variables['--heading-weight'] = String(t.heading_weight);
  for (const [section, key, variable] of [[t, 'letter_spacing', '--letter-spacing'], [t, 'scale', '--type-scale'], [g, 'radius', '--radius'], [g, 'border_width', '--border-width'], [g, 'density', '--space'], [e, 'shadow', '--shadow'], [e, 'gradient', '--hero-gradient'], [e, 'texture', '--grain-opacity']]) {
    if (!Object.hasOwn(maps[key], section[key])) throw new Error(`Invalid theme ${key}`);
    variables[variable] = maps[key][section[key]];
  }
  return variables;
}
