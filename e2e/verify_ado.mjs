import { chromium } from 'playwright';
const b = await chromium.launch({ channel:'chrome', headless:true });
const p = await (await b.newContext({viewport:{width:1440,height:900}})).newPage();
const errs=[]; p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,80))});
try { await p.goto('http://localhost:8774/', {waitUntil:'networkidle',timeout:20000}); await p.waitForTimeout(2500);
  const i=await p.evaluate(()=>({title:document.title.slice(0,50),h1:document.querySelector('h1')?.textContent?.trim().slice(0,50),act:document.querySelectorAll('a,button').length,len:document.body.innerText.length,mentionsObserver:/observer|session|review|reinvention/i.test(document.body.innerText)}));
  console.log(JSON.stringify({...i,errs:errs.length}));
} catch(e){ console.log('FAIL '+String(e).slice(0,70)); }
await b.close();
