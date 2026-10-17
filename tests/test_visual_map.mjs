// Optional developer check: node --test tests/test_visual_map.mjs (no npm install).
import test from 'node:test';
import assert from 'node:assert/strict';
import {tokenVariables} from '../demo_site/token_map.js';

const classic = {
  colors:{bg:'#edf4e9',surface:'#ffffff',text:'#203c2c',text_muted:'#4e6254',primary:'#426342',secondary:'#819773',accent:'#c4cc82',border:'#cbd6c6'},
  typography:{heading_font:'serif',body_font:'sans',heading_weight:500,letter_spacing:'normal',scale:'spacious'},
  geometry:{radius:'round',border_width:'thin',density:'airy'},
  effects:{shadow:'soft',gradient:'subtle',texture:'none'},
};
test('legacy themes map to neutral decoration and motion',()=>{
  const variables=tokenVariables(classic);
  assert.equal(variables['--scene-image'],'none');
  assert.equal(variables['--art-animation'],'none');
  assert.equal(variables['--button-radius'],'var(--radius)');
});
test('forest includes self-contained colored trees, pill controls, organic surfaces and motion',()=>{
  const variables=tokenVariables({...classic,visuals:{motif:'forest',layout:'centered',motion:'calm',button_style:'pill',card_style:'organic'}});
  assert.match(decodeURIComponent(variables['--scene-image']), /<svg/);
  assert.match(decodeURIComponent(variables['--scene-image']), /#426342/);
  assert.equal(variables['--button-radius'],'999px');
  assert.equal(variables['--card-radius'],'40px 10px 40px 10px');
  assert.equal(variables['--art-animation'],'forest-sway');
  assert.equal(variables['--hero-text-align'],'center');
});
test('motion can be disabled independently of the illustration',()=>{
  const variables=tokenVariables({...classic,visuals:{motif:'forest',motion:'none'}});
  assert.notEqual(variables['--scene-image'],'none');
  assert.equal(variables['--art-animation'],'none');
  assert.equal(variables['--chart-animation'],'none');
  assert.equal(variables['--reveal-opacity'],'1');
});
test('invalid visual values and fields are rejected',()=>{
  for(const visuals of [{motif:'url(evil)'},{motion:'eval'},{css:'arbitrary'},null,[]]) assert.throws(()=>tokenVariables({...classic,visuals}));
});
test('illustrations cannot interpolate unvalidated colors',()=>{
  assert.throws(()=>tokenVariables({...classic,colors:{...classic.colors,primary:'"/><script>evil</script>'},visuals:{motif:'forest'}}));
});
test('primary controls choose a legible foreground independently of page background',()=>{
  const light=tokenVariables({...classic,colors:{...classic.colors,primary:'#eef2d0'}});
  const dark=tokenVariables({...classic,colors:{...classic.colors,primary:'#222255'}});
  assert.equal(light['--primary-ink'],'#000000');
  assert.equal(dark['--primary-ink'],'#ffffff');
  const middle=tokenVariables({...classic,colors:{...classic.colors,primary:'#777777'}});
  assert.equal(middle['--primary-ink'],'#000000');
});
