"""Erzeugt die statische Seite SC_Warenwerte.html (Was ist eine Ware wert? Mining-Filter, Roh und Raffiniert getrennt)."""
import datetime as dt
import json
import os

import mining

KIND_DE = {
    "metal": "Metall", "mineral": "Mineral", "minteral": "Mineral", "gas": "Gas", "raw materials": "Rohstoffe",
    "natural": "Natürlich", "scrap": "Schrott", "non-metal": "Nichtmetall", "halogen": "Halogen", "alloy": "Legierung",
    "food": "Lebensmittel", "man-made": "Industrieprodukt", "medical": "Medizin", "agricultural": "Landwirtschaft",
    "drug": "Droge", "vice": "Genussmittel", "fuel": "Treibstoff", "temporary": "Event", "other": "Sonstiges",
    "chemical": "Chemikalie", "waste": "Abfall", "animal": "Tier", "liquid": "Flüssigkeit", "seed": "Saat",
    "explosive": "Sprengstoff", "ammunition": "Munition", "crafting": "Crafting", "electronics": "Elektronik",
    "commodity": "Sonstiges", "organic": "Organisch",
}

PAGE = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SC Warenwerte · Star Citizen</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Exo+2:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { font-size:115%; }   /* alle Schriftgrößen sind in rem: hier zentral skalieren, gleich wie im Frachtrechner */
  body { background:#f5f7fa; color:#1a2030; font-family:'Exo 2',sans-serif; padding:28px 28px 48px; max-width:none; }
  .topbar { display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:22px; padding-bottom:16px; border-bottom:1px solid #d8e2ec; }
  .back-btn { display:inline-flex; gap:6px; font-size:.76rem; font-weight:600; color:#4a5a70; text-decoration:none; padding:5px 12px; border:1px solid #d0d8e4; border-radius:7px; background:#fff; }
  .back-btn:hover { background:#e8eef5; color:#1a2030; }
  h1 { font-family:'Rajdhani',sans-serif; font-size:1.5rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:3px; }
  .subtitle { font-size:.72rem; color:#8090a8; letter-spacing:.08em; text-transform:uppercase; margin-bottom:22px; }
  .panel { background:#fff; border:1px solid #d0d8e4; border-radius:12px; padding:16px 20px; margin-bottom:18px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
  .opts { display:flex; flex-wrap:wrap; gap:10px 14px; align-items:center; font-size:.85rem; margin-bottom:10px; }
  .opts label { display:inline-flex; gap:6px; align-items:center; cursor:pointer; }
  input[type=text], input[type=number], select { font-family:'Exo 2',sans-serif; font-size:.9rem; color:#1a2030; background:#f4f7fa; border:1px solid #c8d4e4; border-radius:8px; padding:8px 12px; }
  input#q { width:260px; max-width:100%; }
  button { font-family:'Exo 2',sans-serif; font-size:.85rem; font-weight:600; color:#1a2030; background:#e8eef5; border:1px solid #c8d4e4; border-radius:8px; padding:8px 14px; cursor:pointer; }
  button:hover { background:#d8e2ee; }
  .hint { font-size:.74rem; color:#6b7a90; margin-top:4px; line-height:1.55; }
  .sum { font-size:.82rem; color:#4a5a70; margin:0 0 8px; }
  .warn { background:#fef3c7; border:1px solid #f0d58a; color:#7a4b00; border-radius:8px; padding:7px 12px; font-size:.8rem; margin-bottom:10px; }
  .wrap { background:#fff; border:1px solid #d0d8e4; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.05); overflow-x:auto; }
  table { border-collapse:collapse; width:100%; font-size:.8rem; }
  th { text-align:left; font-family:'Rajdhani',sans-serif; font-size:.76rem; letter-spacing:.04em; text-transform:uppercase; color:#3a4a60; background:#eef2f7; padding:8px 8px; white-space:nowrap; position:sticky; top:0; cursor:pointer; user-select:none; border-bottom:1px solid #d0d8e4; }
  th.num, td.num { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  th.on { color:#15803d; }
  td { padding:7px 8px; border-bottom:1px solid #edf1f6; vertical-align:top; }
  td.bp { white-space:normal; min-width:130px; max-width:210px; }
  .abb { white-space:nowrap; }
  tr:last-child td { border-bottom:none; }
  tr:hover td { background:#f8fafc; }
  .nm { font-weight:600; }
  .sub { font-size:.72rem; color:#6b7a90; display:block; font-weight:400; }
  .bd { display:inline-block; font-size:.68rem; font-weight:600; padding:1px 7px; border-radius:6px; margin-right:3px; border:1px solid; }
  .bS { color:#1d4ed8; background:#eff6ff; border-color:#bfdbfe; }
  .bR { color:#b45309; background:#fffbeb; border-color:#fcd34d; }
  .bH { color:#15803d; background:#f0fdf4; border-color:#86efac; }
  .bG { color:#7e22ce; background:#faf5ff; border-color:#d8b4fe; }
  .typ-raw { color:#b45309; } .typ-ref { color:#1d4ed8; }
  .val { font-weight:700; color:#15803d; }
  .none { color:#a0b0c0; }
  .old { color:#b45309; }
  .seg { display:inline-flex; border:1px solid #c8d4e4; border-radius:9px; overflow:hidden; }
  .seg button { border:none; border-radius:0; background:#f4f7fa; }
  .seg button.on { background:#15803d; color:#fff; }
  .chip { border-radius:20px; padding:6px 14px; }
  .chip.on { background:#15803d; color:#fff; border-color:#15803d; }
  .lbl { font-size:.78rem; font-weight:600; color:#4a5a70; letter-spacing:.05em; text-transform:uppercase; }
  details.adv summary { cursor:pointer; font-size:.8rem; color:#4a5a70; margin:6px 0 2px; }
  th.grp { text-align:center; background:#e4ebf3; cursor:default; }
  th.nosort { cursor:default; }
  .empty { color:#6b7a90; font-size:.9rem; padding:16px; }
  .footer { margin-top:20px; font-size:.62rem; color:#a0b0c0; letter-spacing:.07em; text-transform:uppercase; border-top:1px solid #e0e8f0; padding-top:10px; line-height:1.7; }
</style>
</head>
<body>
<div class="topbar"><a href="./" class="back-btn">← Star Citizen</a><a href="SC_Frachtrechner.html" class="back-btn">Frachtrechner</a><a href="SC_Schiffspreise.html" class="back-btn">Schiffspreise</a></div>
<h1>SC Warenwerte</h1>
<div class="subtitle">Was ist eine Ware wert? · Verkaufspreise je SCU · Stand Preisdaten __UEXSTAND__</div>

<div class="panel">
  <div class="opts" style="margin-bottom:12px">
    <div class="seg"><button type="button" id="va" class="on">Alle Waren</button><button type="button" id="vm">Mining</button></div>
    <input type="text" id="q" placeholder="Ware suchen (z. B. Hadanite)" autocomplete="off">
    <label>Menge <input type="number" id="qty" min="0" step="1" placeholder="SCU" style="width:90px"></label>
    <button type="button" id="rst" style="margin-left:auto">Filter zurücksetzen</button>
  </div>
  <div class="opts" id="chips">
    <span class="lbl">Abbauart</span>
    <button type="button" class="chip on" data-m="">Alle</button>
    <button type="button" class="chip" data-m="H">Handmining</button>
    <button type="button" class="chip" data-m="R">ROC</button>
    <button type="button" class="chip" data-m="G">ATLS GEO</button>
    <button type="button" class="chip" data-m="S">Schiffs-Mining</button>
  </div>
  <div class="opts" id="catrow" style="display:none">
    <label>Kategorie <select id="fk"></select></label>
  </div>
  <details class="adv">
    <summary>Erweitert</summary>
    <div class="opts" style="margin-top:10px">
      <span>Systeme <span id="sy"></span></span>
      <label><input type="checkbox" id="oi"> illegale Waren und No-Questions-Asked-Terminals einbeziehen</label>
      <label><input type="checkbox" id="od"> Terminals ohne Nachfrage ausklammern</label>
      <label><input type="checkbox" id="oz"> Waren ohne Käufer anzeigen</label>
      <label>Preise ignorieren, die älter sind als
        <select id="oa"><option value="0" selected>(egal)</option><option value="7">7 Tage</option><option value="14">14 Tage</option><option value="30">30 Tage</option><option value="90">90 Tage</option></select></label>
    </div>
  </details>
  <div class="hint" id="hint"></div>
</div>

<div class="sum" id="sum"></div>
<div id="msg"></div>
<div class="wrap"><table>
  <thead id="hd"></thead>
  <tbody id="tb"></tbody>
</table></div>

<div class="footer">Quelle: UEX Corp (Community-Preise je Terminal, stündlich aktualisiert, Fehler möglich) · Abbauart: Community-Übersichten (starvein.app, scminer.rocks, ROC-Guide Alpha 4.10), ATLS GEO laut CIG-Q&amp;A · Seite erzeugt __STAND__</div>

<script>
const T = __TERMINALS__;
const C = __COMMODITIES__;
const P = __PRICES__;
const TM={}, CM={};
T.forEach(t=>TM[t.id]=t); C.forEach(c=>CM[c.id]=c);
const $=id=>document.getElementById(id);
const nf=(n,d=0)=>Number(n).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const LS='sc_werte_v2';
const SYS=[...new Set(T.map(t=>t.s))].sort((a,b)=>['Stanton','Pyro','Nyx'].indexOf(a)-['Stanton','Pyro','Nyx'].indexOf(b));
const MNAME={S:'Schiff',R:'ROC',H:'Hand',G:'GEO'}, MTITLE={S:'Schiffs-Mining (Prospector, MOLE, Orion …)',R:'ROC (Bodenfahrzeug)',H:'Handmining (Multitool)',G:'ATLS GEO (Mining-Powersuit, baut Hand- und ROC-Vorkommen ab)'};
let view='all', chip='', sortKey='med', sortDir=-1;

$('sy').innerHTML=SYS.map(s=>`<label class="sy" style="display:inline-flex;gap:5px;margin-right:10px"><input type="checkbox" value="${esc(s)}" checked> ${esc(s)}</label>`).join('');
const kinds=[...new Set(C.map(c=>c.k).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'de'));
$('fk').innerHTML='<option value="">(alle)</option>'+kinds.map(k=>`<option>${esc(k)}</option>`).join('');
const selSys=()=>[...document.querySelectorAll('#sy input:checked')].map(i=>i.value);
const defSort=v=>v==='mining'?'fmed':'med';

function save(){try{localStorage.setItem(LS,JSON.stringify({v:view,c:chip,q:$('q').value,fk:$('fk').value,qty:$('qty').value,
  sy:selSys(),oi:$('oi').checked,od:$('od').checked,oz:$('oz').checked,oa:$('oa').value,sk:sortKey,sd:sortDir}));}catch(e){}}
function load(){try{const s=JSON.parse(localStorage.getItem(LS)||'null');if(!s)return;
  if(s.v==='mining')view='mining';chip=['H','R','G','S'].includes(s.c)?s.c:'';
  $('q').value=s.q||'';if(kinds.includes(s.fk))$('fk').value=s.fk;$('qty').value=s.qty||'';
  if(Array.isArray(s.sy)&&s.sy.some(x=>SYS.includes(x)))document.querySelectorAll('#sy input').forEach(i=>{i.checked=s.sy.includes(i.value);});
  $('oi').checked=!!s.oi;$('od').checked=!!s.od;$('oz').checked=!!s.oz;if(s.oa!=null)$('oa').value=s.oa;
  if(typeof s.sk==='string'){sortKey=s.sk;sortDir=s.sd===1?1:-1;}}catch(e){}}
function syncUi(){
  $('vm').classList.toggle('on',view==='mining');$('va').classList.toggle('on',view==='all');
  $('chips').style.display=view==='mining'?'':'none';$('catrow').style.display=view==='all'?'':'none';
  document.querySelectorAll('.chip').forEach(b=>b.classList.toggle('on',b.dataset.m===chip));
  $('hint').innerHTML=view==='mining'
    ?'Eine Zeile pro Mineral. <b>Raffiniert / verkaufsfertig</b> ist das, was du am Terminal verkaufst (Edelsteine wie Hadanite direkt, Erze nach dem Raffinieren). <b>Roh</b> ist das unraffinierte Erz; dafür gibt es nur selten Käufer. Der <b>Median</b> ist der mittlere Preis über alle Terminals und weniger anfällig für Ausreißer als der <b>Durchschnitt</b>. Alle Preise in aUEC je SCU. Ein rotes ⏱ heißt: der neueste Preis ist älter als 7 Tage. Der <b>ATLS GEO</b> (Mining-Powersuit) baut laut CIG alles ab, was per Hand oder mit dem ROC geht, aber keine Schiffs-Erze. Ein Fragezeichen bei der Abbauart heißt, dass die Quellen sich widersprechen.'
    :'Alle Waren als flache Liste, Roh und raffiniert getrennt. Preise in aUEC je SCU, der <b>Median</b> ist der mittlere Preis über alle Terminals. Ein rotes ⏱ heißt: der neueste Preis ist älter als 7 Tage.';
}
let timer=null;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{save();render();},150);}
['q','fk','qty','oi','od','oz','oa'].forEach(i=>$(i).addEventListener('input',schedule));
$('sy').addEventListener('change',schedule);
function setView(v){view=v;sortKey=defSort(v);sortDir=-1;syncUi();save();render();}
$('vm').onclick=()=>setView('mining');$('va').onclick=()=>setView('all');
$('chips').addEventListener('click',e=>{const b=e.target.closest('.chip');if(!b)return;chip=b.dataset.m;syncUi();save();render();});
$('rst').onclick=()=>{$('q').value='';$('fk').value='';$('qty').value='';$('oi').checked=false;$('od').checked=false;$('oz').checked=false;$('oa').value='0';chip='';
  document.querySelectorAll('#sy input').forEach(i=>i.checked=true);view='all';sortKey='med';sortDir=-1;syncUi();save();render();};

function stats(o){
  const now=Date.now()/1000,by={},sys=selSys();
  for(const [tid,cid,price,mod,st] of P){
    const t=TM[tid],c=CM[cid];if(!t||!c||!sys.includes(t.s))continue;
    if(!o.illegal&&(t.nqa||c.il))continue;
    if(o.age&&now-mod>o.age*86400)continue;
    if(o.noDemand&&st===7)continue;
    (by[cid]=by[cid]||[]).push({price,mod,t});
  }
  const out={};
  for(const cid in by){
    const a=by[cid].sort((x,y)=>x.price-y.price),n=a.length;
    const med=n%2?a[(n-1)/2].price:(a[n/2-1].price+a[n/2].price)/2;
    const avg=a.reduce((s,x)=>s+x.price,0)/n;
    const top=a[n-1],newest=Math.max(...a.map(x=>x.mod));
    out[cid]={med,avg,min:a[0].price,max:top.price,best:top.price,bestAt:top.t,cnt:n,age:Math.floor((now-newest)/86400)};
  }
  return out;
}
const ageHtml=a=>`<span class="${a>7?'old':''}">${a>7?'⏱ ':''}${a<=0?'heute':a===1?'1 Tag':a+' Tage'}</span>`;
const badgesOf=(m,x)=>m.map(v=>{const k=v[0],q=v.length>1;return `<span class="bd b${k}" title="${esc(MTITLE[k])}${q?' – Quellen widersprechen sich':''}">${MNAME[k]}${q?'?':''}</span>`;}).join('')
  ||(x?'<span class="bd" style="color:#6b7a90;background:#f4f7fa;border-color:#d0d8e4" title="abbaubar, Abbauart nicht zugeordnet">?</span>':'<span class="none">–</span>');
const th=(k,l,cls='')=>`<th class="${cls}${k===sortKey?' on':''}" data-k="${k}">${l}${k===sortKey?(sortDir<0?' ▼':' ▲'):''}</th>`;

function renderMining(o,st,qty){
  const groups={};
  C.forEach(c=>{if(!c.m.length&&!c.x)return;const k=c.b.toLowerCase();(groups[k]=groups[k]||{name:c.b,m:c.m,x:c.x,k:c.k,list:[]}).list.push(c);if(c.m.length)groups[k].m=c.m;});
  let rows=Object.values(groups).map(g=>{
    const priced=g.list.filter(c=>st[c.id]);
    let fin=null,raw=null;
    if(priced.length===1)fin=priced[0];
    else if(priced.length>1){
      const byCnt=(a,b)=>st[b.id].cnt-st[a.id].cnt;
      const r=priced.filter(c=>c.t==='raw').sort(byCnt),f=priced.filter(c=>c.t!=='raw').sort(byCnt);
      if(f.length){fin=f[0];raw=r[0]||null;}else{fin=priced.sort(byCnt)[0];}
    }
    return {g,f:fin?st[fin.id]:null,r:raw?st[raw.id]:null};
  });
  rows=rows.filter(r=>(!o.q||r.g.name.toLowerCase().includes(o.q))&&(!chip||r.g.m.some(v=>v[0]===chip))&&(r.f||r.r||$('oz').checked));
  const val=r=>{const k=sortKey;if(k==='n')return r.g.name.toLowerCase();
    const s=k[0]==='f'?r.f:r.r;const f=k.slice(1);if(!s)return f==='age'?1e9:-1;return {med:s.med,avg:s.avg,best:s.best,age:s.age}[f];};
  rows.sort((a,b)=>{const x=val(a),y=val(b);const r=typeof x==='string'?x.localeCompare(y,'de'):x-y;return (r||a.g.name.localeCompare(b.g.name,'de'))*sortDir;});
  $('hd').innerHTML=`<tr><th rowspan="2" data-k="n"${sortKey==='n'?' class="on"':''}>Mineral${sortKey==='n'?(sortDir<0?' ▼':' ▲'):''}</th><th rowspan="2" class="nosort">Abbauart</th>`+
    `<th colspan="4" class="grp nosort">Raffiniert / verkaufsfertig</th><th colspan="3" class="grp nosort">Roh</th>${qty>0?'<th rowspan="2" class="num nosort">Wert für '+nf(qty,qty%1?1:0)+' SCU</th>':''}</tr>`+
    `<tr>${th('fmed','Median','num')}${th('favg','Ø','num')}${th('fbest','Bester Preis','num')}${th('fage','Stand','num')}${th('rmed','Median','num')}${th('ravg','Ø','num')}${th('rage','Stand','num')}</tr>`;
  $('sum').textContent=rows.length+' Mineralien'+(rows.filter(r=>!r.f&&!r.r).length?` (${rows.filter(r=>!r.f&&!r.r).length} ohne Käufer)`:'');
  $('tb').innerHTML=rows.length?rows.map(({g,f,r})=>{
    const none='<span class="none">–</span>';
    const fc=f?`<td class="num val">${nf(f.med)}</td><td class="num">${nf(f.avg)}</td><td class="num bp">${nf(f.best)}<span class="sub">${esc(f.bestAt.pl)} · ${esc(f.bestAt.s)}</span></td><td class="num">${ageHtml(f.age)}<span class="sub">${f.cnt} Terminal${f.cnt>1?'s':''}</span></td>`
      :`<td class="num none" colspan="4">kein Käufer</td>`;
    const rc=r?`<td class="num">${nf(r.med)}</td><td class="num">${nf(r.avg)}</td><td class="num">${ageHtml(r.age)}<span class="sub">${r.cnt} Terminal${r.cnt>1?'s':''}</span></td>`:`<td class="num none">–</td><td class="num none">–</td><td class="num none">–</td>`;
    const w=f||r;
    return `<tr><td class="nm">${esc(g.name)}<span class="sub">${esc(g.k||'')}</span></td><td class="abb">${badgesOf(g.m,g.x)}</td>${fc}${rc}`+(qty>0?`<td class="num val">${w?nf(w.med*qty)+' aUEC':'–'}</td>`:'')+`</tr>`;
  }).join(''):`<tr><td class="empty" colspan="11">Kein Mineral passt zu den Filtern.</td></tr>`;
}
function renderAll(o,st,qty){
  let rows=C.filter(c=>(!o.q||c.n.toLowerCase().includes(o.q))&&(!o.fk||c.k===o.fk)).map(c=>({c,s:st[c.id]||null}));
  if(!$('oz').checked)rows=rows.filter(r=>r.s);
  const val=r=>{const k=sortKey;if(k==='n')return r.c.n.toLowerCase();if(k==='t')return r.c.t;if(k==='m')return r.c.m.join('');if(k==='k')return r.c.k;
    if(!r.s)return k==='age'?1e9:-1;return {med:r.s.med,avg:r.s.avg,best:r.s.best,min:r.s.min,cnt:r.s.cnt,age:r.s.age}[k];};
  rows.sort((a,b)=>{const x=val(a),y=val(b);const r=typeof x==='string'?x.localeCompare(y,'de'):x-y;return (r||a.c.n.localeCompare(b.c.n,'de'))*sortDir;});
  $('hd').innerHTML='<tr>'+th('n','Ware')+th('t','Art')+th('m','Abbauart')+th('k','Kategorie')+th('med','Median je SCU','num')+th('avg','Ø je SCU','num')+th('best','Bester Preis','num')+th('min','Spanne','num')+th('cnt','Terminals','num')+th('age','Stand','num')+(qty>0?'<th class="num nosort">Wert für '+nf(qty,qty%1?1:0)+' SCU</th>':'')+'</tr>';
  $('sum').textContent=rows.length+' Waren'+(rows.filter(r=>!r.s).length?` (${rows.filter(r=>!r.s).length} ohne Käufer)`:'');
  const TYP={raw:'<span class="typ-raw">Roh</span>',ref:'<span class="typ-ref">Raffiniert</span>',oth:'<span class="none">–</span>'};
  $('tb').innerHTML=rows.length?rows.map(({c,s})=>{
    const cells=s?`<td class="num val">${nf(s.med)}</td><td class="num">${nf(s.avg)}</td><td class="num bp">${nf(s.best)}<span class="sub">${esc(s.bestAt.pl)} · ${esc(s.bestAt.s)}</span></td>`+
      `<td class="num">${s.min===s.max?nf(s.min):nf(s.min)+' – '+nf(s.max)}</td><td class="num">${s.cnt}</td><td class="num">${ageHtml(s.age)}</td>`
      :`<td class="num none" colspan="6">kein Terminal kauft diese Ware</td>`;
    return `<tr><td class="nm">${esc(c.n)}</td><td>${TYP[c.t||'oth']}</td><td class="abb">${badgesOf(c.m,c.x)}</td><td>${esc(c.k||'–')}</td>${cells}`+(qty>0?`<td class="num val">${s?nf(s.med*qty)+' aUEC':'–'}</td>`:'')+`</tr>`;
  }).join(''):`<tr><td class="empty" colspan="11">Keine Ware passt zu den Filtern.</td></tr>`;
}
function render(){
  const o={q:$('q').value.trim().toLowerCase(),fk:$('fk').value,illegal:$('oi').checked,noDemand:$('od').checked,age:+$('oa').value};
  const qty=parseFloat($('qty').value)||0;
  $('msg').innerHTML='';
  if(!selSys().length){$('hd').innerHTML='';$('tb').innerHTML='';$('sum').textContent='';$('msg').innerHTML='<div class="warn">Wähle unter „Erweitert“ mindestens ein System.</div>';return;}
  const st=stats(o);
  if(view==='mining')renderMining(o,st,qty);else renderAll(o,st,qty);
}
$('hd').addEventListener('click',e=>{const t=e.target.closest('th');if(!t||!t.dataset.k)return;const k=t.dataset.k;
  if(sortKey===k)sortDir=-sortDir;else{sortKey=k;sortDir=['n','t','m','k','age','fage','rage','min'].includes(k)?1:-1;}save();render();});
load();syncUi();render();
</script>
</body>
</html>
'''


def build(con, target):
    import uex
    terms = []
    for r in con.execute("SELECT * FROM uex_terminals ORDER BY id"):
        t = dict(r)
        terms.append({"id": t["id"], "pl": uex.place_name(t), "s": t["star_system"], "nqa": t["is_nqa"]})
    priced = {r[0] for r in con.execute("SELECT DISTINCT id_commodity FROM uex_prices")}
    coms = []
    for r in con.execute("SELECT * FROM uex_commodities ORDER BY lower(name)"):
        m = mining.methods(r["name"])
        if r["id"] not in priced and not m and not r["is_extractable"]:
            continue
        kind = KIND_DE.get((r["kind"] or "").strip().lower(), r["kind"] or "")
        typ = "raw" if r["is_raw"] else ("ref" if r["is_refined"] else "")
        coms.append({"id": r["id"], "n": r["name"], "k": kind, "t": typ, "b": mining.base_name(r["name"]), "m": m, "il": r["is_illegal"],
                     "x": 1 if (r["is_extractable"] and not m) else 0})
    prices = [[r["id_terminal"], r["id_commodity"], round(r["price_sell"]), r["date_modified"], r["status_sell"]]
              for r in con.execute("SELECT * FROM uex_prices")]
    newest = max((p[3] for p in prices), default=0)
    stand = dt.datetime.fromtimestamp(newest).strftime("%d.%m.%Y %H:%M") if newest else "unbekannt"

    def js(x):
        return json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = (PAGE.replace("__TERMINALS__", js(terms)).replace("__COMMODITIES__", js(coms)).replace("__PRICES__", js(prices))
            .replace("__UEXSTAND__", stand).replace("__STAND__", dt.datetime.now().strftime("%d.%m.%Y %H:%M")))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, target)
    return len(prices)
