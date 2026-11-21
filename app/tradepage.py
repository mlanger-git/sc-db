"""Erzeugt die statische Seite SC_Frachtrechner.html (Verkaufsstopps fuer Fracht bündeln)."""
import json
import os
import datetime as dt

PAGE = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SC Frachtrechner · Star Citizen</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Exo+2:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background:#f5f7fa; color:#1a2030; font-family:'Exo 2',sans-serif; padding:28px 28px 48px; max-width:1100px; }
  .topbar { display:flex; align-items:center; gap:10px; margin-bottom:22px; padding-bottom:16px; border-bottom:1px solid #d8e2ec; }
  .back-btn { display:inline-flex; gap:6px; font-size:.76rem; font-weight:600; color:#4a5a70; text-decoration:none; padding:5px 12px; border:1px solid #d0d8e4; border-radius:7px; background:#fff; }
  .back-btn:hover { background:#e8eef5; color:#1a2030; }
  h1 { font-family:'Rajdhani',sans-serif; font-size:1.5rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:3px; }
  h2 { font-family:'Rajdhani',sans-serif; font-size:1rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#3a4a60; margin-bottom:10px; }
  .subtitle { font-size:.72rem; color:#8090a8; letter-spacing:.08em; text-transform:uppercase; margin-bottom:22px; }
  .panel { background:#fff; border:1px solid #d0d8e4; border-radius:12px; padding:16px 20px; margin-bottom:18px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
  .row { display:flex; gap:10px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }
  input[type=text], input[type=number], select { font-family:'Exo 2',sans-serif; font-size:.9rem; color:#1a2030; background:#f4f7fa; border:1px solid #c8d4e4; border-radius:8px; padding:8px 12px; }
  input.cn { width:260px; max-width:100%; } input.cs { width:110px; }
  input.err { border-color:#b91c1c; background:#fee2e2; }
  button { font-family:'Exo 2',sans-serif; font-size:.85rem; font-weight:600; color:#1a2030; background:#e8eef5; border:1px solid #c8d4e4; border-radius:8px; padding:8px 14px; cursor:pointer; }
  button:hover { background:#d8e2ee; }
  button.x { padding:6px 10px; color:#8090a8; }
  .opts { display:flex; flex-wrap:wrap; gap:8px 22px; align-items:center; font-size:.85rem; }
  .opts label { display:inline-flex; gap:6px; align-items:center; cursor:pointer; }
  .hint { font-size:.74rem; color:#6b7a90; margin-top:8px; line-height:1.5; }
  .sum { font-size:.82rem; color:#4a5a70; margin:4px 0 0; }
  .card { background:#fff; border:1px solid #d0d8e4; border-radius:12px; padding:16px 20px; margin-bottom:14px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
  .card.best { border-color:#2f7d4f; box-shadow:0 0 0 1px #2f7d4f inset; }
  .chead { display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:6px 16px; margin-bottom:6px; }
  .ctitle { font-family:'Rajdhani',sans-serif; font-size:1.05rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
  .total { font-family:'Rajdhani',sans-serif; font-size:1.25rem; font-weight:700; color:#15803d; }
  .meta { font-size:.76rem; color:#6b7a90; margin-bottom:10px; }
  .stop { border-top:1px solid #edf1f6; padding:9px 0 3px; }
  .sname { font-weight:600; } .sloc { font-size:.74rem; color:#6b7a90; }
  .line { display:flex; justify-content:space-between; gap:14px; font-size:.84rem; padding:2px 0 2px 12px; flex-wrap:wrap; }
  .line .a { font-variant-numeric:tabular-nums; white-space:nowrap; }
  .note { font-size:.7rem; color:#b45309; }
  .warn { background:#fef3c7; border:1px solid #f0d58a; color:#7a4b00; border-radius:8px; padding:7px 12px; font-size:.8rem; margin-bottom:10px; }
  .empty { color:#6b7a90; font-size:.9rem; padding:8px 0; }
  details summary { cursor:pointer; font-size:.8rem; color:#4a5a70; margin-top:4px; }
  .footer { margin-top:20px; font-size:.62rem; color:#a0b0c0; letter-spacing:.07em; text-transform:uppercase; border-top:1px solid #e0e8f0; padding-top:10px; line-height:1.7; }
</style>
</head>
<body>
<div class="topbar"><a href="./" class="back-btn">← Star Citizen</a><a href="SC_Schiffspreise.html" class="back-btn">Schiffspreise</a><a href="SC_Warenwerte.html" class="back-btn">Warenwerte</a></div>
<h1>SC Frachtrechner</h1>
<div class="subtitle">Fracht verkaufen und Verkaufsstopps bündeln · Preisdaten Stand __UEXSTAND__</div>

<div class="panel">
  <h2>Deine Fracht</h2>
  <div id="rows"></div>
  <div class="row"><button type="button" id="add">+ Ware hinzufügen</button><button type="button" id="clr">Alles leeren</button></div>
  <div class="sum" id="sum"></div>
  <datalist id="cl"></datalist>
</div>

<div class="panel">
  <h2>Einstellungen</h2>
  <div class="opts">
    <span class="syl">Systeme <span id="os"></span></span>
    <label>Startpunkt <select id="st"></select></label>
    <label>Streckenkosten <input type="number" id="oc" min="0" step="500" value="2000" style="width:100px"> aUEC je Gm</label>
    <label>Systemwechsel zählt wie <input type="number" id="oj" min="0" step="10" value="100" style="width:80px"> Gm</label>
  </div>
  <div class="opts" style="margin-top:10px">
    <label><input type="checkbox" id="od" checked> Nachfrage der Terminals berücksichtigen</label>
    <label><input type="checkbox" id="oi"> illegale Waren und No-Questions-Asked-Terminals einbeziehen</label>
    <label>Preise ignorieren, die älter sind als
      <select id="oa"><option value="0">(egal)</option><option value="3">3 Tage</option><option value="7">7 Tage</option><option value="14" selected>14 Tage</option><option value="30">30 Tage</option></select></label>
  </div>
  <div class="hint">Als Startpunkt kannst du einen Himmelskörper (z. B. ArcCorp) oder einen Ort wählen. Die Route läuft vom Startpunkt über die Verkaufsstopps, ein Rückweg ist nicht eingerechnet.
  Die <b>Streckenkosten</b> sagen, wie viel dir ein Gigameter Flugstrecke wert ist (Zeit, Treibstoff, Risiko). Je höher der Wert, desto eher wählt der Rechner nahe Stopps, bei 0 zählt nur der Erlös.
  Ein „Stopp“ ist ein Ort (Station, Stadt oder Außenposten); mehrere Terminals am selben Ort zählen als ein Stopp. Mehrere Systeme kannst du gleichzeitig anhaken; die Entfernungen innerhalb eines Systems sind UEX-Schätzungen (geladen: __DTXT__). Ein Wechsel zwischen Systemen wird pauschal mit dem Wert bei „Systemwechsel“ angesetzt.</div>
</div>

<div id="res"></div>

<div class="footer">Quelle: UEX Corp (Community-Preise je Terminal, stündlich aktualisiert, Fehler möglich). Preise in aUEC je SCU, Entfernungen in Gigametern (UEX-Schätzung). Die Preise ändern sich im Spiel mit Angebot und Nachfrage; die Berechnung ist eine Orientierung, keine Garantie. Seite erzeugt __STAND__.</div>

<script>
const T = __TERMINALS__;
const PL = __PLACES__;
const C = __COMMODITIES__;
const P = __PRICES__;
const DT = __DISTS__;
const TM={}, CM={}, CBN={};
T.forEach(t=>TM[t.id]=t); C.forEach(c=>{CM[c.id]=c;CBN[c.n.toLowerCase()]=c;});
const N=PL.length, DM=new Float32Array(N*N).fill(-1);
for(let i=0;i<N;i++)DM[i*N+i]=0;
DT.forEach(([i,j,d])=>{DM[i*N+j]=d;DM[j*N+i]=d;});
let DMX=DM;
function setJump(J){DMX=DM.slice();for(let i=0;i<N;i++)for(let j=0;j<N;j++)if(PL[i].s!==PL[j].s)DMX[i*N+j]=J;}
const $=id=>document.getElementById(id);
const nf=(n,d=0)=>Number(n).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const LS='sc_fracht_v2';
const SYS=[...new Set(T.map(t=>t.s))].sort((a,b)=>['Stanton','Pyro','Nyx'].indexOf(a)-['Stanton','Pyro','Nyx'].indexOf(b));

// ---- Oberfläche -------------------------------------------------------
$('cl').innerHTML=C.map(c=>`<option value="${esc(c.n)}">`).join('');
$('os').innerHTML=SYS.map((x,i)=>`<label class="sy"><input type="checkbox" value="${esc(x)}"${i===0?' checked':''}> ${esc(x)}</label>`).join(' ');
const selSys=()=>[...document.querySelectorAll('#os input:checked')].map(i=>i.value);
function fillStart(sel){
  const sy=selSys(),multi=sy.length>1;let h='<option value="">(kein Startpunkt)</option>';
  sy.forEach(sys=>{
    const bodies=[...new Set(PL.filter(p=>p.s===sys&&p.b).map(p=>p.b))].sort((a,b)=>a.localeCompare(b,'de'));
    const places=PL.map((p,i)=>[p,i]).filter(([p])=>p.s===sys).sort((a,b)=>a[0].pl.localeCompare(b[0].pl,'de'));
    const pre=multi?sys+' · ':'';
    h+=`<optgroup label="${esc(pre)}Himmelskörper">`+bodies.map(b=>`<option value="b:${esc(sys)}|${esc(b)}">${esc(b)}</option>`).join('')+'</optgroup>'
      +`<optgroup label="${esc(pre)}Stationen, Städte, Außenposten">`+places.map(([p,i])=>`<option value="p:${i}">${esc(p.pl)}</option>`).join('')+'</optgroup>';
  });
  $('st').innerHTML=h;
  if(sel&&[...$('st').options].some(o=>o.value===sel))$('st').value=sel;
}
fillStart();
function addRow(name='',scu=''){
  const d=document.createElement('div');d.className='row';
  d.innerHTML=`<input type="text" class="cn" list="cl" placeholder="Ware (z. B. Agricium)" value="${esc(name)}"><input type="number" class="cs" min="0" step="1" placeholder="SCU" value="${esc(scu)}"><button type="button" class="x" title="Zeile entfernen">✕</button>`;
  d.querySelector('.x').onclick=()=>{d.remove();if(!$('rows').children.length)addRow();schedule();};
  $('rows').appendChild(d);
}
$('add').onclick=()=>{addRow();};
$('clr').onclick=()=>{$('rows').innerHTML='';addRow();schedule();};
$('os').addEventListener('change',()=>{fillStart($('st').value);schedule();});
['od','oi','oa','oc','oj','st'].forEach(i=>$(i).addEventListener('input',schedule));
document.addEventListener('input',e=>{if(e.target.matches('.cn,.cs'))schedule();});

function getOpts(){return {sys:selSys(),jump:Math.max(0,+$('oj').value||0),demand:$('od').checked,illegal:$('oi').checked,age:+$('oa').value,cost:Math.max(0,+$('oc').value||0),start:$('st').value};}
function getNeed(){const need={};let bad=false;
  document.querySelectorAll('#rows .row').forEach(r=>{const n=r.querySelector('.cn'),s=r.querySelector('.cs');
    const nm=n.value.trim().toLowerCase(),q=parseFloat(s.value);
    n.classList.remove('err');
    if(!nm&&!(q>0))return;
    const c=CBN[nm];
    if(!c){n.classList.add('err');bad=true;return;}
    if(!(q>0))return;
    need[c.id]=(need[c.id]||0)+q;});
  return {need,bad};}
function save(){try{const o=getOpts();localStorage.setItem(LS,JSON.stringify({rows:[...document.querySelectorAll('#rows .row')].map(r=>[r.querySelector('.cn').value,r.querySelector('.cs').value]),
  od:o.demand,oi:o.illegal,oa:$('oa').value,os:o.sys,st:o.start,oc:$('oc').value,oj:$('oj').value}));}catch(e){}}
function load(){try{const s=JSON.parse(localStorage.getItem(LS)||'null');if(!s)return false;
  (s.rows||[]).forEach(r=>addRow(r[0],r[1]));$('od').checked=s.od!==false;$('oi').checked=!!s.oi;if(s.oa!=null)$('oa').value=s.oa;
  if(s.oc!=null&&s.oc!=='')$('oc').value=s.oc;
  if(s.oj!=null&&s.oj!=='')$('oj').value=s.oj;
  const ss=Array.isArray(s.os)?s.os:(s.os?[s.os]:[]);
  if(ss.some(x=>SYS.includes(x)))document.querySelectorAll('#os input').forEach(i=>{i.checked=ss.includes(i.value);});
  fillStart(s.st);return true;}catch(e){return false;}}
let timer=null;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{save();compute();},250);}

// ---- Rechenlogik ------------------------------------------------------
// off[cid] = Map(ortsindex -> bestes Angebot {tid, price, cap, est, mod}); price in aUEC je SCU, cap = SCU-Nachfrage
function buildOffers(o,need){
  const now=Date.now()/1000,res={};
  for(const cid in need)res[cid]=new Map();
  for(const [tid,cid,price,scu,avg,st,mod] of P){
    if(!(cid in need))continue;
    const t=TM[tid];if(!t||!o.sys.includes(t.s))continue;
    if(!o.illegal&&(t.nqa||CM[cid].il))continue;
    if(o.age&&now-mod>o.age*86400)continue;
    let cap=Infinity,est=false;
    if(o.demand){if(st===7)continue;if(scu>0)cap=scu;else{est=true;if(avg>0)cap=avg;}}
    const m=res[cid],cur=m.get(t.pi);
    if(!cur||price>cur.price)m.set(t.pi,{tid,price,cap,est,mod});
  }
  return res;
}
function fill(list,q){
  list.sort((a,b)=>b.price-a.price);
  let rest=q,rev=0;const asg=[];
  for(const o of list){if(rest<=0)break;const take=Math.min(rest,o.cap);if(!(take>0))continue;rev+=take*o.price;rest-=take;asg.push({o,take});}
  return {rev,rest,asg};
}
function evalSet(S,need,off,detail){
  let rev=0,rest=0;const det=[];
  for(const cid in need){
    const list=[];
    for(const pk of S){const o=off[cid].get(pk);if(o)list.push({pk,price:o.price,cap:o.cap,o});}
    const f=fill(list,need[cid]);rev+=f.rev;rest+=f.rest;
    if(detail)det.push({cid,f});
  }
  return detail?{rev,rest,det}:rev;
}
function combos(arr,k,cb,start=0,cur=[]){
  if(cur.length===k){cb(cur);return;}
  for(let i=start;i<arr.length;i++){cur.push(arr[i]);combos(arr,k,cb,i+1,cur);cur.pop();}
}
function perms(a){if(a.length<=1)return [a.slice()];const out=[];a.forEach((x,i)=>perms(a.filter((_,j)=>j!==i)).forEach(p=>out.push([x,...p])));return out;}
// Startvektor: Entfernung vom Startpunkt zu jedem Ort (-1 = unbekannt); null = kein Startpunkt
function startVec(o){
  if(!o.start)return null;
  const v=new Float32Array(N).fill(-1);
  if(o.start.startsWith('p:')){const i=+o.start.slice(2);for(let j=0;j<N;j++)v[j]=DMX[i*N+j];}
  else{const [sy,b]=o.start.slice(2).split('|');const qs=[];PL.forEach((p,i)=>{if(p.s===sy&&p.b===b)qs.push(i);});
    for(let j=0;j<N;j++){let m=-1;for(const q of qs){const d=DMX[q*N+j];if(d>=0&&(m<0||d<m))m=d;}v[j]=m;}}
  return v;
}
function startSys(o){if(!o.start)return null;if(o.start.startsWith('p:'))return PL[+o.start.slice(2)].s;return o.start.slice(2).split('|')[0];}
function pathDist(order,d0){
  let tot=0,prev=-1;
  for(const p of order){const d=prev<0?(d0?d0[p]:0):DMX[prev*N+p];if(d<0)return -1;tot+=d;prev=p;}
  return tot;
}
function bestRoute(S,d0){
  let best=null;
  for(const order of perms(S)){const d=pathDist(order,d0);if(d>=0&&(!best||d<best.dist))best={order,dist:d};}
  return best;
}
function candidates(need,off,o,d0){
  const set=new Set(),all=new Set();
  for(const cid in need){
    const arr=[...off[cid].entries()].map(([pk,x])=>{
      const v=x.price*Math.min(need[cid],x.cap)-(o.cost>0&&d0&&d0[pk]>=0?o.cost*d0[pk]:0);return [pk,v];}).sort((a,b)=>b[1]-a[1]);
    arr.slice(0,15).forEach(([pk])=>set.add(pk));
    arr.forEach(([pk])=>all.add(pk));
  }
  [...all].map(pk=>{const r=evalSet([pk],need,off,false);const d=o.cost>0&&d0?d0[pk]:0;return [pk,d<0?-Infinity:r-o.cost*(d||0)];})
    .sort((a,b)=>b[1]-a[1]).slice(0,40).forEach(([pk])=>set.add(pk));
  return {cands:[...set],all:[...all]};
}
// bestes Bündel mit genau k Orten (alle besucht); Ziel: Erlös minus Streckenkosten
function evalUsed(S,need,off){
  let rev=0;const used=new Set();
  for(const cid in need){
    const list=[];
    for(const pk of S){const o=off[cid].get(pk);if(o)list.push({pk,price:o.price,cap:o.cap});}
    list.sort((a,b)=>b.price-a.price);
    let rest=need[cid];
    for(const o of list){if(rest<=0)break;const take=Math.min(rest,o.cap);if(!(take>0))continue;rev+=take*o.price;rest-=take;used.add(o.pk);}
  }
  return {rev,used:[...used]};
}
function bestExact(k,cands,need,off,o,d0){
  const kk=Math.min(k,cands.length);let bestV=-Infinity,bestS=null;
  combos(cands,kk,S=>{
    const e=evalUsed(S,need,off);let v=e.rev;
    if(o.cost>0){const r=bestRoute(e.used,d0);if(!r)return;v=e.rev-o.cost*r.dist;}
    if(v>bestV){bestV=v;bestS=S.slice();}
  });
  return bestS?{S:bestS,v:bestV}:null;
}
// Theoretisches Maximum: jede Ware an den jeweils besten Orten (beliebig viele Stopps, ohne Strecke)
function maxPlan(need,off){
  let rev=0;const places=new Set();
  for(const cid in need){
    const list=[...off[cid].entries()].map(([pk,x])=>({pk,price:x.price,cap:x.cap,o:x}));
    const f=fill(list,need[cid]);rev+=f.rev;f.asg.forEach(a=>places.add(a.o.pk));
  }
  return {rev,stops:places.size};
}

// ---- Darstellung ------------------------------------------------------
const ageTxt=m=>{const d=Math.floor((Date.now()/1000-m)/86400);return d<=0?'heute':d===1?'vor 1 Tag':`vor ${d} Tagen`;};
function stopsHtml(plan,order,legs,o){
  const byPlace={};
  plan.det.forEach(({cid,f})=>f.asg.forEach(a=>{(byPlace[a.o.pk]=byPlace[a.o.pk]||[]).push({cid,take:a.take,o:a.o.o});}));
  const seq=order&&order.length?order:Object.keys(byPlace).map(Number).sort((a,b)=>sum(byPlace[b])-sum(byPlace[a]));
  function sum(lines){return lines.reduce((s,l)=>s+l.take*l.o.price,0);}
  const seqF=seq.filter(pk=>byPlace[pk]);
  return seqF.map((pk,i)=>{
    const lines=byPlace[pk].slice().sort((a,b)=>b.take*b.o.price-a.take*a.o.price),pl=PL[pk];
    const terms=[...new Set(lines.map(l=>TM[l.o.tid].tn))].join(', ');
    const prevSys=i===0?startSys(o):PL[seqF[i-1]].s;
    const leg=legs&&legs[i]!=null&&legs[i]>=0?(prevSys&&prevSys!==pl.s?` · <b>Systemwechsel</b> (gerechnet wie ${nf(legs[i])} Gm)`:` · <b>${nf(legs[i])} Gm</b> ${i===0?(o.start?'vom Startpunkt':''):'vom vorherigen Stopp'}`):'';
    return `<div class="stop"><div class="sname">${order&&order.length?`${i+1}. `:''}${esc(pl.pl)} <span class="sloc">· ${esc(pl.lc)} · Terminal: ${esc(terms)}${leg}</span></div>`+
      lines.map(l=>`<div class="line"><span>${esc(CM[l.cid].n)}: ${nf(l.take,l.take%1?1:0)} SCU × ${nf(l.o.price)} aUEC`+
        `${l.o.est?' <span class="note">· Nachfrage geschätzt</span>':''}${(Date.now()/1000-l.o.mod)>7*86400?` <span class="note">· Preis von ${ageTxt(l.o.mod)}</span>`:''}</span>`+
        `<span class="a">${nf(l.take*l.o.price)} aUEC</span></div>`).join('')+
      `<div class="line" style="font-weight:600"><span>Summe an diesem Stopp</span><span class="a">${nf(sum(lines))} aUEC</span></div></div>`;
  }).join('');
}
function compute(){
  const out=$('res');const {need,bad}=getNeed();const o=getOpts();setJump(o.jump);
  const ids=Object.keys(need);
  const tot=ids.reduce((s,c)=>s+need[c],0);
  $('sum').textContent=ids.length?`${ids.length} Ware${ids.length>1?'n':''}, zusammen ${nf(tot,tot%1?1:0)} SCU`:'';
  if(!ids.length){out.innerHTML='<div class="card"><div class="empty">Gib oben mindestens eine Ware und eine SCU-Menge ein.</div></div>';return;}
  if(!o.sys.length){out.innerHTML='<div class="card"><div class="empty">Wähle oben mindestens ein System.</div></div>';return;}
  const off=buildOffers(o,need);
  const warns=[];
  ids.filter(c=>off[c].size===0).forEach(c=>warns.push(`Für ${esc(CM[c].n)} gibt es in ${esc(o.sys.join(', '))} mit den aktuellen Einstellungen keinen Abnehmer.`));
  const active=ids.filter(c=>off[c].size>0);
  const need2={};active.forEach(c=>need2[c]=need[c]);
  let html=bad?'<div class="warn">Mindestens ein Warenname wird nicht erkannt (rot markiert). Bitte aus der Vorschlagsliste wählen.</div>':'';
  if(!active.length){out.innerHTML=html+warns.map(w=>`<div class="warn">${w}</div>`).join('');return;}
  const d0=startVec(o);
  let oo=o;
  // Entfernungsdaten da? Sonst ohne Streckenkosten rechnen und das sagen
  const anyDist=DM.some(v=>v>0);
  if(o.cost>0&&!anyDist){warns.push('Die Entfernungsdaten sind noch nicht geladen, deshalb zählt vorerst nur der Erlös.');oo={...o,cost:0};}
  let {cands,all}=candidates(need2,off,oo,d0);
  let exact=[1,2,3].map(k=>k>all.length&&k>1?null:bestExact(k,cands,need2,off,oo,d0));
  if(oo.cost>0&&exact.every(x=>!x)){
    warns.push('Für diese Orte fehlen Entfernungen (noch nicht alle geladen). Es zählt vorerst nur der Erlös.');
    oo={...o,cost:0};({cands,all}=candidates(need2,off,oo,d0));
    exact=[1,2,3].map(k=>k>all.length&&k>1?null:bestExact(k,cands,need2,off,oo,d0));
  }
  const mx=maxPlan(need2,off);
  const cards=[];
  for(let k=1;k<=3;k++){
    const pool=exact.slice(0,k).filter(Boolean);
    if(!pool.length)continue;
    const pick=pool.reduce((a,b)=>b.v>a.v?b:a);
    const plan=evalSet(pick.S,need2,off,true);
    const usedSet=new Set();plan.det.forEach(d=>d.f.asg.forEach(a=>usedSet.add(a.o.pk)));
    const used=[...usedSet];
    const r=bestRoute(used,d0);
    const order=r?r.order:null,dist=r?r.dist:null;
    const legs=order?order.map((p,i)=>i===0?(d0?d0[p]:null):DMX[order[i-1]*N+p]):null;
    const cost=oo.cost>0&&dist!=null?oo.cost*dist:0;
    cards.push({k,plan,used,order,dist,legs,cost,net:plan.rev-cost,sig:[...used].sort((a,b)=>a-b).join()});
  }
  const shown=[];cards.forEach(c=>{if(shown.length&&shown[shown.length-1].sig===c.sig)return;shown.push(c);});
  const bestNet=Math.max(...shown.map(c=>c.net));
  html+=warns.map(w=>`<div class="warn">${w}</div>`).join('');
  const useCost=oo.cost>0;
  shown.forEach((c,i)=>{
    const unsold=c.plan.det.filter(d=>d.f.rest>0.0001).map(d=>`${nf(d.f.rest,d.f.rest%1?1:0)} SCU ${esc(CM[d.cid].n)}`);
    const rec=useCost&&shown.length>1&&c.net===bestNet;
    const pct=mx.rev>0?c.plan.rev/mx.rev*100:100;
    const meta=[`Erlös ${nf(c.plan.rev)} aUEC (${nf(pct,1)} % des Maximums)`];
    if(c.dist!=null)meta.push(`Strecke ${nf(c.dist)} Gm${o.start?' ab Startpunkt':''}`);
    if(useCost&&c.dist!=null)meta.push(`Streckenkosten ${nf(c.cost)} aUEC`);
    else if(o.cost>0&&c.dist==null)meta.push('Entfernung unbekannt');
    html+=`<div class="card${rec?' best':''}"><div class="chead"><div class="ctitle">${c.used.length} Stopp${c.used.length>1?'s':''}${rec?' · Empfehlung':''}${i===0&&!rec?' · wenigste Stopps':''}</div>`+
      `<div class="total">${nf(useCost&&c.dist!=null?c.net:c.plan.rev)} aUEC${useCost&&c.dist!=null?' <span class="sloc">netto</span>':''}</div></div>`+
      `<div class="meta">${meta.join(' · ')}</div>`+
      (unsold.length?`<div class="warn">Nicht verkauft (keine ausreichende Nachfrage an diesen Stopps): ${unsold.join(', ')}</div>`:'')+
      stopsHtml(c.plan,c.order,c.legs,o)+`</div>`;
  });
  const fullPlan={det:[]};for(const cid in need2){const list=[...off[cid].entries()].map(([pk,x])=>({pk,price:x.price,cap:x.cap,o:x}));fullPlan.det.push({cid,f:fill(list,need2[cid])});}
  html+=`<div class="card"><div class="chead"><div class="ctitle">Theoretisches Maximum</div><div class="total" style="color:#4a5a70">${nf(mx.rev)} aUEC</div></div>`+
    `<div class="meta">Jede Ware am jeweils besten Ort verkauft: ${mx.stops} Stopp${mx.stops>1?'s':''}, ohne Rücksicht auf die Strecke. Dient nur als Vergleich.</div>`+
    `<details><summary>Stopps anzeigen</summary>${stopsHtml(fullPlan,null,null,o)}</details></div>`;
  out.innerHTML=html;
}
if(!load())addRow('','');
if(!$('rows').children.length)addRow();
compute();
</script>
</body>
</html>
'''


def build(con, target):
    import uex
    place_idx, places, terms = {}, [], []
    for r in con.execute("SELECT * FROM uex_terminals ORDER BY id"):
        t = dict(r)
        name = uex.place_name(t)
        key = (t["star_system"], name)
        if key not in place_idx:
            place_idx[key] = len(places)
            places.append({"pl": name, "s": t["star_system"], "b": t["moon"] or t["planet"] or "",
                           "lc": " › ".join(x for x in (t["star_system"], t["planet"], t["moon"]) if x)})
        terms.append({"id": t["id"], "tn": t["nickname"] or t["name"] or str(t["id"]), "s": t["star_system"],
                      "pi": place_idx[key], "nqa": t["is_nqa"]})
    used_c = {r[0] for r in con.execute("SELECT DISTINCT id_commodity FROM uex_prices")}
    coms = [{"id": r["id"], "n": r["name"], "k": r["kind"] or "", "il": r["is_illegal"]}
            for r in con.execute("SELECT * FROM uex_commodities ORDER BY lower(name)") if r["id"] in used_c]
    prices = [[r["id_terminal"], r["id_commodity"], round(r["price_sell"]), round(r["scu_sell"], 1),
               round(r["scu_sell_avg"], 1), r["status_sell"], r["date_modified"]]
              for r in con.execute("SELECT * FROM uex_prices")]
    newest = max((p[6] for p in prices), default=0)
    stand = dt.datetime.fromtimestamp(newest).strftime("%d.%m.%Y %H:%M") if newest else "unbekannt"

    # Entfernungen: Referenz-Terminal je Ort -> Ortsindex
    rep_to_pi = {tid: place_idx[key] for key, tid in uex.place_reps(con).items() if key in place_idx}
    dist, needed = [], 0
    for r in con.execute("SELECT id_a, id_b, gm FROM uex_distances WHERE gm IS NOT NULL"):
        if r["id_a"] in rep_to_pi and r["id_b"] in rep_to_pi:
            dist.append([rep_to_pi[r["id_a"]], rep_to_pi[r["id_b"]], round(r["gm"], 1)])
    try:
        needed = len(uex._needed_pairs(con))
    except Exception:  # noqa: BLE001
        needed = 0
    dtxt = f"{len(dist)} von {needed} Ortspaaren" if needed else "noch keine"

    def js(x):
        return json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = (PAGE.replace("__TERMINALS__", js(terms)).replace("__PLACES__", js(places))
            .replace("__COMMODITIES__", js(coms)).replace("__PRICES__", js(prices)).replace("__DISTS__", js(dist))
            .replace("__UEXSTAND__", stand).replace("__DTXT__", dtxt)
            .replace("__STAND__", dt.datetime.now().strftime("%d.%m.%Y %H:%M")))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, target)
    return len(prices)
