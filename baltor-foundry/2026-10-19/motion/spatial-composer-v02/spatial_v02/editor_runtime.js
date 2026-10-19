/* Baltor Spatial Studio v0.2 — standalone, offline JSON spatial compositor editor.
 * Browser canvas preview is approximate; Python compositor is authoritative for final pixels.
 * All controls edit the SAME JSON node schema as layouts.json; no external resources loaded.
 */
'use strict';
let cfg = window.EMBEDDED_CONFIG;
let images = window.EMBEDDED_IMAGES;
const canvas = document.getElementById('stage');
const g = canvas.getContext('2d');
const label = document.getElementById('status');
const profile = document.getElementById('profile');
const preset = document.getElementById('preset');
let current = 'cinematic';
let selectedIndex = -1;
let drag = null;
let boxes = [];
let showGuides = true;
let currentScene = null;
let W = 540, H = 960;
let safeRects = {
  reels:[.095,.105,.185,.060],shorts:[.095,.115,.195,.055],tiktok:[.105,.135,.210,.055],
  vertical_general:[.075,.075,.145,.055],landscape:[.072,.065,.110,.065],square:[.075,.070,.105,.070],full:[.030,.030,.045,.030]
};
const anchors = {
 top_left:[0,0],top_center:[.5,0],top_right:[1,0],middle_left:[0,.5],center:[.5,.5],middle_right:[1,.5],
 bottom_left:[0,1],bottom_center:[.5,1],bottom_right:[1,1],upper_third_left:[0,.333],upper_third_center:[.5,.333],upper_third_right:[1,.333],lower_third_left:[0,.667],lower_third_center:[.5,.667],lower_third_right:[1,.667]
};
const kindOptions=['text','pill','tag','box','line','progress','reticle','circle','waveform','image','panel_grid'];
function ns(v){return Number(v)||0}
function rectSafe(){let [t,r,b,l]=safeRects[profile.value];return {x:l*W,y:t*H,w:(1-r-l)*W,h:(1-t-b)*H}}
function getRect(node){
 let b=node.box||{};
 const canvasRect={x:0,y:0,w:W,h:H};
 let p=b.space==='canvas'?canvasRect:rectSafe();
 if(b.space && boxes.find(x=>x.id===b.space)){const hit=boxes.find(x=>x.id===b.space);p=hit.rect}
 const [ax,ay]=anchors[b.anchor||'top_left']||[0,0];
 const w=b.w_px?b.w_px*W/540:ns(b.w)*p.w;
 const h=b.h_px?b.h_px*H/960:ns(b.h)*p.h;
 return {x:p.x+p.w*ax-w*ax+ns(b.dx)*p.w,y:p.y+p.h*ay-h*ay+ns(b.dy)*p.h,w,h};
}
function roundedRect(x,y,w,h,rad){const r=Math.max(0,Math.min(rad,w/2,h/2));g.beginPath();g.roundRect(x,y,w,h,r)}
function cropImage(im, rect, crop, mirror=false){
 const [a,b,c,d]=crop||[0,0,1,1];
 const sx=a*im.width, sy=b*im.height, sw=(c-a)*im.width, sh=(d-b)*im.height;
 const cover = Math.max(rect.w/sw, rect.h/sh);const ww=sw*cover,hh=sh*cover;
 g.save();roundedRect(rect.x,rect.y,rect.w,rect.h,7);g.clip();
 if(mirror){g.translate(rect.x*2+rect.w,0);g.scale(-1,1)}
 g.drawImage(im,sx,sy,sw,sh,rect.x+(rect.w-ww)/2,rect.y+(rect.h-hh)/2,ww,hh);
 g.restore();
}
function wrapText(txt,maxw,font){
 let result=[];String(txt).split('\n').forEach(block=>{
  let cur='';block.split(' ').forEach(word=>{
   let next=cur?(cur+' '+word):word;
   if(g.measureText(next).width<=maxw || !cur)cur=next;
   else{result.push(cur);cur=word}
  });if(cur)result.push(cur);
 });return result;
}
function drawNode(node,rect){
 let kind=node.kind||'text';g.save();g.globalAlpha=ns(node.opacity===undefined?1:node.opacity);
 const color=node.color||'#F4F3E6',border=node.border||'#85F4E8';
 if(kind==='image' && currentScene){
  cropImage(currentScene,rect,node.crop,node.mirror);g.strokeStyle=border;g.lineWidth=node.border_width||2;g.strokeRect(rect.x,rect.y,rect.w,rect.h)
 }else if(kind==='panel_grid' && currentScene){
  const r=node.rows||2,c=node.cols||2,gap=node.gap||8;
  const cw=(rect.w-gap*(c-1))/c,ch=(rect.h-gap*(r-1))/r;
  for(let j=0;j<r*c;j++){
   const rr={x:rect.x+(j%c)*(cw+gap),y:rect.y+Math.floor(j/c)*(ch+gap),w:cw,h:ch};
   cropImage(currentScene,rr,(node.crops||[])[j],node.mirror_alternate && j%2===1);
   g.strokeStyle=(j%2?node.border:node.accent)||'#85F4E8';g.lineWidth=2;g.strokeRect(rr.x,rr.y,rr.w,rr.h);
   g.fillStyle='#081826E8';g.fillRect(rr.x+4,rr.y+4,rr.w-8,24);
   g.font='bold 13px system-ui';g.fillStyle='#F3F1E7';g.fillText((node.labels||[])[j]||`CAM ${j+1}`,rr.x+9,rr.y+21);
  }
 }else if(kind==='box' || kind==='pill' || kind==='tag' || node.background){
  if(node.background!==false){g.fillStyle=node.fill||'#081521DF';roundedRect(rect.x,rect.y,rect.w,rect.h,node.radius||8);g.fill()}
  if(node.outline!==false){g.strokeStyle=border;g.lineWidth=node.border_width||1;roundedRect(rect.x,rect.y,rect.w,rect.h,node.radius||8);g.stroke()}
 }
 if(['text','pill','metric','tag','button'].includes(kind)){
  const p=Array.isArray(node.padding)?node.padding:[node.padding||0,node.padding||0,node.padding||0,node.padding||0];
  const pt=p[0],pr=p[1],pb=p[2],pl=p[3];
  let size=node.font_size||22;
  let maxw=Math.max(1,rect.w-pl-pr),maxh=Math.max(1,rect.h-pt-pb);
  const family=node.font==='mono'?'ui-monospace':node.font==='serif'?'Georgia':node.font==='condensed'?'Impact':'system-ui';
  let lines;
  do{
   g.font=`${node.font==='sans'?400:700} ${size}px ${family}`;
   lines=wrapText(node.text||'',maxw,g.font);
   if(lines.length*(size*1.17)<=maxh && lines.length<=(node.max_lines||5))break;
   size--;
  }while(size>=Math.max(node.min_font_size||11,8));
  g.fillStyle=color;g.textBaseline='top';g.textAlign=node.align||'left';
  const htxt=lines.length*size*1.17;
  const valign=node.valign||(kind==='text'?'top':'center');
  let y=rect.y+pt+(valign==='center'?(maxh-htxt)/2:valign==='bottom'?maxh-htxt:0);
  let x=node.align==='center'?rect.x+pl+maxw/2:node.align==='right'?rect.x+rect.w-pr:rect.x+pl;
  lines.forEach(line=>{if(node.shadow){g.shadowBlur=3;g.shadowColor='#000'}g.fillText(line,x,y);g.shadowBlur=0;y+=size*1.17});
 }else if(kind==='pointer'){
  let target=node.target||[.5,.5];g.strokeStyle=color;g.lineWidth=node.width||2;g.beginPath();g.moveTo(rect.x+rect.w/2,rect.y+rect.h/2);g.lineTo(target[0]*W,target[1]*H);g.stroke();g.fillStyle=color;g.beginPath();g.arc(target[0]*W,target[1]*H,4,0,Math.PI*2);g.fill();
 }else if(kind==='line'){
  g.strokeStyle=color;g.lineWidth=node.width||2;g.beginPath();g.moveTo(rect.x,rect.y+rect.h/2);g.lineTo(rect.x+rect.w,rect.y+rect.h/2);g.stroke();
 }else if(kind==='progress'){
  g.fillStyle=node.track||'#314A56';roundedRect(rect.x,rect.y,rect.w,rect.h,5);g.fill();
  const p=node.value==='resource_level'?.18:node.value==='signal_strength'?.28: .54;
  g.fillStyle=color;roundedRect(rect.x,rect.y,rect.w*p,rect.h,5);g.fill();
 }else if(kind==='circle' || kind==='reticle'){
  g.strokeStyle=color;g.lineWidth=2;
  const x=rect.x+rect.w/2,y=rect.y+rect.h/2,r=Math.min(rect.w,rect.h)/3;
  for(let j of (kind==='circle'?[1]:[.7,1,1.3])){g.beginPath();g.arc(x,y,r*j,0,Math.PI*2);g.stroke()}
 }else if(kind==='waveform'){
  const bars=node.bars||32;g.fillStyle=color;
  for(let i=0;i<bars;i++){
   const hh=rect.h*(.16+.8*Math.abs(Math.sin(i*.87+2)*Math.sin(i*.18)));
   g.fillRect(rect.x+(i+.5)*rect.w/bars,rect.y+rect.h/2-hh/2,Math.max(2,rect.w/bars*.45),hh)
  }
 }
 g.restore();
}
function draw(){
 if(!cfg.layouts[current])return;
 g.clearRect(0,0,W,H);
 if(currentScene)g.drawImage(currentScene,0,0,W,H);else {g.fillStyle='#121C2B';g.fillRect(0,0,W,H)}
 boxes=[];
 const order=cfg.layouts[current].elements.map((n,i)=>({n,i})).sort((a,b)=>(a.n.z||0)-(b.n.z||0));
 for(const {n,i} of order){const r=getRect(n);boxes.push({id:n.id,rect:r,i});drawNode(n,r)}
 if(showGuides){
  g.save();g.strokeStyle='#F1D479A6';g.lineWidth=2;g.setLineDash([9,7]);
  const q=rectSafe();g.strokeRect(q.x,q.y,q.w,q.h);
  g.strokeStyle='#9DC4C45C';g.lineWidth=1;g.setLineDash([4,12]);
  for(let p of [1/3,2/3]){g.beginPath();g.moveTo(W*p,0);g.lineTo(W*p,H);g.stroke();g.beginPath();g.moveTo(0,H*p);g.lineTo(W,H*p);g.stroke()}
  g.restore();
 }
 if(selectedIndex>=0){
  let node=cfg.layouts[current].elements[selectedIndex];
  if(node){const r=getRect(node);g.save();g.lineWidth=2;g.strokeStyle='#FFE699';g.setLineDash([5,4]);g.strokeRect(r.x,r.y,r.w,r.h);g.setLineDash([]);g.fillStyle='#FFE699';g.fillRect(r.x-3,r.y-3,8,8);g.restore()}
 }
 let n=cfg.layouts[current].elements.length;
 label.textContent=`${W}×${H} working canvas · ${n} elements · ${profile.value} safe zone · ${current}`;
}
function domId(id){return document.getElementById(id)}
function setCurrent(key){
 current=key;selectedIndex=-1;
 const img=new Image();img.onload=()=>{currentScene=img;draw()};
 img.src=images[key];
 populateList();populateInspector();draw();
}
function populateList(){
 const cont=domId('elementList');cont.innerHTML='';
 cfg.layouts[current].elements.forEach((n,i)=>{
  const b=document.createElement('button');b.className='node '+(i===selectedIndex?'selected':'');
  b.textContent=`${String(n.z||0).padStart(2,'0')}  ${n.id}  · ${n.kind}`;
  b.onclick=()=>{selectedIndex=i;populateList();populateInspector();draw()};cont.appendChild(b)
 });
}
function inspectorRow(name,value,step,cb,opts={}){
 const row=document.createElement('label');row.className='property';
 const tag=document.createElement('span');tag.textContent=name;
 let input;
 if(opts.options){input=document.createElement('select');opts.options.forEach(v=>{let o=document.createElement('option');o.value=v;o.textContent=v;input.appendChild(o)})}
 else if(opts.multi){input=document.createElement('textarea');input.rows=2}
 else{input=document.createElement('input');input.type=opts.type||'number';if(step!==null)input.step=step}
 input.value=value;input.oninput=()=>{cb(input.value);draw();if(opts.redrawList)populateList()};row.append(tag,input);return row;
}
function populateInspector(){
 const panel=domId('inspector');panel.innerHTML='';const elems=cfg.layouts[current].elements;
 if(selectedIndex<0 || !elems[selectedIndex]){panel.innerHTML='<p>Choose an element, then change its coordinates, padding, style, size and layer. Drag its selected box on the preview.</p>';return}
 const n=elems[selectedIndex],box=n.box||{};
 const title=document.createElement('h3');title.textContent=`Edit: ${n.id}`;panel.appendChild(title);
 function add(name,value,step,cb,opts){panel.appendChild(inspectorRow(name,value,step,cb,opts||{}))}
 add('Type',n.kind||'text',null,v=>n.kind=v,{options:kindOptions});
 if(['text','pill','tag','metric','button'].includes(n.kind)){
  add('Text',n.text||'',null,v=>n.text=v,{multi:true});
  add('Font family',n.font||'bold',null,v=>n.font=v,{options:['sans','bold','mono','serif','condensed']});
  add('Text size',n.font_size||22,1,v=>n.font_size=ns(v));
  add('Min text size',n.min_font_size||11,1,v=>n.min_font_size=ns(v));
  add('Align',n.align||'left',null,v=>n.align=v,{options:['left','center','right']});
 }
 add('Anchor',box.anchor||'top_left',null,v=>box.anchor=v,{options:Object.keys(anchors)});
 add('Coordinate space',box.space||'safe',null,v=>box.space=v,{options:['safe','canvas']});
 for(let k of ['dx','dy','w','h'])add(`${k} (relative)`,ns(box[k]).toFixed(3),.005,v=>box[k]=ns(v));
 for(let side of ['top','right','bottom','left']){
  const k={top:0,right:1,bottom:2,left:3}[side];
  if(!Array.isArray(n.padding))n.padding=[0,0,0,0];
  add(`Padding ${side} (px)`,n.padding[k]||0,1,v=>n.padding[k]=ns(v));
 }
 add('Z-index (layer)',n.z||0,1,v=>n.z=ns(v),{redrawList:true});
 add('Opacity (0–1)',n.opacity??1,.05,v=>n.opacity=ns(v));
 add('Text / stroke color',n.color||'#F4F3E6',null,v=>n.color=v,{type:'text'});
 add('Background color',n.fill||'#081521DF',null,v=>{n.fill=v;n.background=true},{type:'text'});
 add('Border color',n.border||'#85F4E8',null,v=>{n.border=v;n.outline=true},{type:'text'});
 add('Corner radius',n.radius||8,1,v=>n.radius=ns(v));
 const p=document.createElement('div');p.className='inspector-actions';
 const dup=document.createElement('button');dup.textContent='Duplicate';dup.onclick=()=>{const nn=structuredClone(n);nn.id=n.id+'_copy';nn.box.dx=(nn.box.dx||0)+.03;nn.z=(nn.z||0)+1;elems.push(nn);selectedIndex=elems.length-1;populateList();populateInspector();draw()};
 const del=document.createElement('button');del.textContent='Delete';del.onclick=()=>{elems.splice(selectedIndex,1);selectedIndex=-1;populateList();populateInspector();draw()};
 p.append(dup,del);panel.appendChild(p);
}
const selector = domId('preset');
Object.entries(cfg.layouts).forEach(([k,v])=>{const opt=document.createElement('option');opt.value=k;opt.textContent=v.name;selector.appendChild(opt)});
selector.onchange=()=>setCurrent(selector.value);
profile.value='reels';profile.onchange=draw;
domId('toggleGuides').onclick=()=>{showGuides=!showGuides;draw()};
domId('addText').onclick=()=>{let a=cfg.layouts[current].elements;a.push({id:'new_label_'+(a.length+1),kind:'text',box:{space:'safe',anchor:'top_left',dx:.09,dy:.48,w:.70,h:.09},layer:'typography',z:60,text:'EDIT THIS TITLE',font_size:26,color:'#F4F3E6',padding:[5,8,5,8]});selectedIndex=a.length-1;populateList();populateInspector();draw()};
domId('addPanel').onclick=()=>{let a=cfg.layouts[current].elements;a.push({id:'new_panel_'+(a.length+1),kind:'box',box:{space:'safe',anchor:'top_left',dx:.1,dy:.54,w:.7,h:.20},layer:'panels',z:17,fill:'#081521DB',border:'#85F4E8',background:true,outline:true,radius:8});selectedIndex=a.length-1;populateList();populateInspector();draw()};
domId('exportConfig').onclick=()=>{
 const result=JSON.stringify({schema:cfg.schema,layout:current,profile:profile.value,elements:cfg.layouts[current].elements},null,2);
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([result],{type:'application/json'}));a.download=`${current}_edited.json`;a.click();URL.revokeObjectURL(a.href)
};
domId('exportPNG').onclick=()=>{const a=document.createElement('a');a.download=`${current}_preview.png`;a.href=canvas.toDataURL('image/png');a.click()};
canvas.addEventListener('pointerdown',e=>{
 const r=canvas.getBoundingClientRect();const x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H;
 for(let a of [...boxes].reverse()){
  const b=a.rect;if(x>=b.x&&x<b.x+b.w&&y>=b.y&&y<b.y+b.h){selectedIndex=a.i;drag={x,y,ox:cfg.layouts[current].elements[a.i].box.dx||0,oy:cfg.layouts[current].elements[a.i].box.dy||0};canvas.setPointerCapture(e.pointerId);populateList();populateInspector();draw();return}
 }
 selectedIndex=-1;populateList();populateInspector();draw();
});
canvas.addEventListener('pointermove',e=>{
 if(!drag||selectedIndex<0)return;
 const r=canvas.getBoundingClientRect();const x=(e.clientX-r.left)/r.width*W,y=(e.clientY-r.top)/r.height*H;
 const node=cfg.layouts[current].elements[selectedIndex];const parent=node.box.space==='canvas'?{w:W,h:H}:rectSafe();
 node.box.dx=Math.round((drag.ox+(x-drag.x)/parent.w)*1000)/1000;
 node.box.dy=Math.round((drag.oy+(y-drag.y)/parent.h)*1000)/1000;
 draw();
});
canvas.addEventListener('pointerup',()=>{drag=null;populateInspector()});
canvas.addEventListener('pointercancel',()=>{drag=null;populateInspector()});
setCurrent(current);
