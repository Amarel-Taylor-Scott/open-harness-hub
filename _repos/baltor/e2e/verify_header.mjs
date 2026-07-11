import { chromium } from 'playwright';
const b = await chromium.launch({ channel:'chrome', headless:true });
const p = await (await b.newContext({viewport:{width:1440,height:900}})).newPage();
const errs=[]; p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,70))});
await p.goto('http://localhost:8003/', {waitUntil:'networkidle',timeout:25000}); await p.waitForTimeout(3000);
const r = await p.evaluate(()=>({
  dropdownBtn: document.querySelectorAll('.ohs-pf-btn, .ohs-pf').length,
  demoLinks: [...document.querySelectorAll('header a, header button')].filter(a=>/^demo$/i.test(a.textContent.trim())).length,
  navItems: [...document.querySelectorAll('.ohs-top-nav a')].map(a=>a.textContent.trim()).slice(0,10),
}));
console.log(JSON.stringify({...r, consoleErrors:errs.length}));
await b.close();
