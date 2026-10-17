/* Optional: run fixture server first; requires Playwright and installed Edge. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const base = process.env.DOODLE_QA_URL || 'http://localhost:8002';

(async () => {
  const browser = await chromium.launch({channel:'msedge',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
    const errors = [];
    page.setDefaultTimeout(15000);
    page.on('pageerror', e=>errors.push(e.message));
    let failedOnce = false;
    await page.route('**/api/redesign', async route=>{
      if (route.request().method()==='POST' && !failedOnce) {
        failedOnce=true;
        await route.fulfill({status:503,json:{detail:'LLM website generation needs OPENAI_API_KEY in .env and VIBE_MOCK=0.'}});
      } else await route.continue();
    });
    await page.goto(base);
    await page.locator('#start-draw').click();
    await page.locator('#draw-done').click();
    for(let index=0;index<10;index++) {
      await page.waitForFunction(n=>document.querySelector('#ab-progress').getAttribute('aria-valuenow')===String(n),index);
      await page.locator('#ab-left').click();
    }
    await page.locator('#phase-result').waitFor({state:'visible'});
    await page.locator('#generation-panel[data-state=error]').waitFor();
    assert((await page.locator('#generation-detail').innerText()).includes('OPENAI_API_KEY'));
    assert(await page.locator('#preview-after').isDisabled());
    assert(await page.locator('#download-html').isDisabled());
    await page.locator('#generation-retry').click();
    await page.locator('#generation-panel[data-state=ready]').waitFor({timeout:15000});
    assert.equal(await page.locator('#result-name').innerText(),'Botanical');
    assert((await page.locator('#generation-model').innerText()).startsWith('OpenAI:'));
    assert((await page.locator('#result-rationale').innerText()).includes('organic'));
    const frame = page.frameLocator('#demo-preview');
    await frame.locator('h1').waitFor({state:'visible'});
    await page.screenshot({path:'tmp/llm-result-initial-qa.png',fullPage:true});
    await frame.locator('body[data-parent-access=blocked][data-network=blocked]').waitFor();
    assert.equal(await page.locator('#demo-preview').getAttribute('sandbox'),'allow-scripts allow-forms');
    assert.equal(await frame.locator('h1').innerText(),'Clarity, naturally.');
    assert.equal(await frame.locator('.tree').evaluate(e=>getComputedStyle(e).animationName),'sway');
    await frame.locator('#d2d-motion').click();
    assert.equal(await frame.locator('.tree').evaluate(e=>getComputedStyle(e).animationName),'none');
    await frame.locator('#d2d-motion').click();
    assert.equal(await frame.locator('.tree').evaluate(e=>getComputedStyle(e).animationName),'sway');
    await page.emulateMedia({reducedMotion:'reduce'});
    assert.equal(await frame.locator('.tree').evaluate(e=>getComputedStyle(e).animationName),'none');
    await frame.locator('input[type=email]').fill('tester@example.com');
    await frame.locator('#contact-form button').click();
    assert((await frame.locator('#contact-form [role=status]').innerText()).includes('No message'));
    await page.locator('#preview-before').click();
    await frame.locator('.hero').waitFor();
    await page.locator('#preview-after').click();
    await frame.locator('h1').filter({hasText:'Clarity, naturally.'}).waitFor();
    const downloading = page.waitForEvent('download');
    await page.locator('#download-html').click();
    const download = await downloading;
    assert.equal(download.suggestedFilename(),'doodle2design-website.html');
    await download.saveAs('tmp/qa-generated-website.html');
    const cssDownload = page.waitForEvent('download');
    await page.locator('#download-css').click();
    assert.equal((await cssDownload).suggestedFilename(),'doodle2design-website.css');
    for(const width of [320,768,1024,1440]) {
      await page.setViewportSize({width,height:1000});
      assert(await page.locator('html').evaluate(e=>e.scrollWidth<=e.clientWidth),'Wizard overflow at '+width);
    }
    await page.setViewportSize({width:1440,height:1000});
    await frame.locator('h1').waitFor({state:'visible'});
    await frame.locator('h1').screenshot({path:'tmp/llm-preview-heading.png'});
    assert.equal(await page.locator('#demo-preview').evaluate(e=>e.clientWidth),await frame.locator('html').evaluate(e=>e.clientWidth));
    await page.locator('#demo-preview').screenshot({path:'tmp/llm-preview-box.png'});
    await page.screenshot({path:'tmp/llm-result-qa.png',fullPage:true});
    // Full-screen retains the HTTP sandbox, independently of the host iframe.
    const previewUrl = await page.locator('#demo-fullscreen').getAttribute('href');
    const standalone = await browser.newPage();
    const response = await standalone.goto(base+previewUrl);
    assert(response.headers()['content-security-policy'].includes('sandbox allow-scripts'));
    await standalone.locator('body[data-network=blocked]').waitFor();
    assert(!response.headers()['content-security-policy'].includes('allow-same-origin'));
    assert.equal(await standalone.evaluate(()=>{try{void localStorage;return 'allowed'}catch{return 'blocked'}}),'blocked');
    await standalone.close();
    await page.locator('#try-again').click();
    await page.locator('#phase-landing').waitFor({state:'visible'});
    assert.equal((await page.request.get(base+previewUrl)).status(),409);
    assert.deepEqual(errors,[]);
    console.log('PASS: ten-round flow, missing-key/retry, document title/reason, generated code, before/after, HTML/CSS download, motion, 320-1440px, opaque origin, blocked network, fullscreen isolation, reset.');
    await page.close();
    // Real configuration: no API key must not generate a preset.
    const local = await browser.newPage({reducedMotion:'reduce'});
    const config = await (await local.request.get('http://localhost:8000/api/config')).json();
    if (!config.offline) {
      console.log('Real-server calibration skipped because AI is enabled; QA never makes paid calls.');
      await local.close();
      return;
    }
    await local.goto('http://localhost:8000');
    await local.locator('#start-draw').click();
    await local.locator('#draw-done').click();
    for(let i=0;i<10;i++){
      await local.waitForFunction(n=>document.querySelector('#ab-progress').getAttribute('aria-valuenow')===String(n),i);
      await local.locator('#ab-left').click();
    }
    await local.locator('#generation-panel[data-state=error]').waitFor();
    assert((await local.locator('#generation-detail').innerText()).includes('OPENAI_API_KEY'));
    await local.screenshot({path:'tmp/llm-setup-qa.png',fullPage:true});
    await local.locator('#try-again').click();
    console.log('PASS: real local no-key configuration gives an honest setup message after calibration.');
    await local.close();
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
