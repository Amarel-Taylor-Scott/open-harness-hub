import { chromium } from 'playwright';
const b = await chromium.launch({ channel:'chrome', headless:true });
const p = await (await b.newContext({viewport:{width:1440,height:900}})).newPage();
const errs=[]; p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,110))}); p.on('pageerror',e=>errs.push('PE:'+String(e).slice(0,110)));
await p.goto('http://localhost:8003/', {waitUntil:'networkidle',timeout:25000}); await p.waitForTimeout(3000);
const i=await p.evaluate(()=>({h1:document.querySelector('h1')?.textContent?.trim().slice(0,40), act:document.querySelectorAll('a,button').length,
  ohlayout: typeof window.OHSite!=='undefined' ? ('OhLayout' in (window.OHSite||{})) : 'n/a'}));
console.log(JSON.stringify({...i, consoleErrors:errs.length, errs:errs.slice(0,3)}));
await b.close();
