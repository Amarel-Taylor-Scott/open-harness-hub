import { chromium } from 'playwright';
const b = await chromium.launch({ channel:'chrome', headless:true });
const OUT='/tmp/claude-1000/-home-username-ai-harness-and-knowledge-facts-and-logic-website-sharing/a1b3374d-9cc4-43b0-9f7b-b9dd635cf5cb/scratchpad/surface-review';
for (const [name,port] of [['baltor',8001],['aidoneright',8002],['teleon',8003],['openhubforai',8130]]) {
  const p = await (await b.newContext({viewport:{width:1440,height:900}})).newPage();
  const errs=[]; p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,80))}); p.on('pageerror',e=>errs.push('PE'));
  try {
    await p.goto(`http://localhost:${port}/`, {waitUntil:'networkidle',timeout:25000}); await p.waitForTimeout(3000);
    const i=await p.evaluate(()=>({title:document.title.slice(0,46),h1:document.querySelector('h1')?.textContent?.trim().slice(0,46),act:document.querySelectorAll('a,button').length,len:document.body.innerText.length}));
    console.log(`[${name}:${port}] ${JSON.stringify(i)} errs=${errs.length} ${JSON.stringify(errs.slice(0,2))}`);
    await p.screenshot({path:`${OUT}/sc-${name}.png`,fullPage:true});
  } catch(e){ console.log(`[${name}:${port}] FAIL ${String(e).slice(0,70)}`); }
  await p.close();
}
await b.close();
