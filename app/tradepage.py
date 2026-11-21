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
<div class="topbar"><a href="./" class="back-btn">← Star Citizen</a><a href="SC_Schiffspreise.html" class="back-btn">Schiffspreise</a></div>
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
  <div class="opts" id="sysbox"></div>
  <div class="opts" style="margin-top:10px">
    <label><input type="checkbox" id="od" checked> Nachfrage der Terminals berücksichtigen</label>
    <label><input type="checkbox" id="oi"> illegale Waren und No-Questions-Asked-Terminals einbeziehen</label>
    <label>Preise ignorieren, die älter sind als
      <select id="oa"><option value="0">(egal)</option><option value="3">3 Tage</option><option value="7">7 Tage</option><option value="14" selected>14 Tage</option><option value="30">30 Tage</option></select></label>
  </div>
  <div class="hint">Ein „Stopp“ ist ein Ort (Station, Stadt oder Außenposten). Mehrere Terminals am selben Ort zählen als ein Stopp. Entfernungen und Flugzeiten sind in dieser Version nicht eingerechnet.</div>
</div>

<div id="res"></div>

<div class="footer">Quelle: UEX Corp (Community-Preise je Terminal, stündlich aktualisiert, Fehler möglich). Preise in aUEC je SCU. Die Preise ändern sich im Spiel mit Angebot und Nachfrage; die Berechnung ist eine Orientierung, keine Garantie. Seite erzeugt __STAND__.</div>

<script>
const T = __TERMINALS__;
const C = __COMMODITIES__;
const P = __PRICES__;
const TM={}, CM={}, CBN={};
T.forEach(t=>TM[t.id]=t); C.forEach(c=>{CM[c.id]=c;CBN[c.n.toLowerCase()]=c;});
const $=id=>document.getElementById(id);
const nf=(n,d=0)=>Number(n).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const LS='sc_fracht_v1';
const SYS=[...new Set(T.map(t=>t.s))].sort();

// ---- Oberfläche -------------------------------------------------------
$('cl').innerHTML=C.map(c=>`<option value="${esc(c.n)}">`).join('');
$('sysbox').innerHTML='<b>Systeme:</b> '+SYS.map(s=>`<label><input type="checkbox" class="sy" value="${esc(s)}" checked> ${esc(s)}</label>`).join('');
function addRow(name='',scu=''){
  const d=document.createElement('div');d.className='row';
  d.innerHTML=`<input type="text" class="cn" list="cl" placeholder="Ware (z. B. Agricium)" value="${esc(name)}"><input type="number" class="cs" min="0" step="1" placeholder="SCU" value="${esc(scu)}"><button type="button" class="x" title="Zeile entfernen">✕</button>`;
  d.querySelector('.x').onclick=()=>{d.remove();if(!$('rows').children.length)addRow();schedule();};
  $('rows').appendChild(d);
}
$('add').onclick=()=>{addRow();};
$('clr').onclick=()=>{$('rows').innerHTML='';addRow();schedule();};
['od','oi','oa'].forEach(i=>$(i).addEventListener('input',schedule));
document.addEventListener('input',e=>{if(e.target.matches('.cn,.cs,.sy'))schedule();});

function getOpts(){const sys={};document.querySelectorAll('.sy').forEach(c=>sys[c.value]=c.checked);
  return {sys,demand:$('od').checked,illegal:$('oi').checked,age:+$('oa').value};}
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
function save(){try{localStorage.setItem(LS,JSON.stringify({rows:[...document.querySelectorAll('#rows .row')].map(r=>[r.querySelector('.cn').value,r.querySelector('.cs').value]),
  od:$('od').checked,oi:$('oi').checked,oa:$('oa').value,sys:getOpts().sys}));}catch(e){}}
function load(){try{const s=JSON.parse(localStorage.getItem(LS)||'null');if(!s)return false;
  (s.rows||[]).forEach(r=>addRow(r[0],r[1]));$('od').checked=s.od!==false;$('oi').checked=!!s.oi;if(s.oa!=null)$('oa').value=s.oa;
  document.querySelectorAll('.sy').forEach(c=>{if(s.sys&&c.value in s.sys)c.checked=s.sys[c.value];});return true;}catch(e){return false;}}
let timer=null;function schedule(){clearTimeout(timer);timer=setTimeout(()=>{save();compute();},250);}

// ---- Rechenlogik ------------------------------------------------------
// off[cid] = Map(ortsschluessel -> bestes Angebot {tid, price, cap, est, mod}); price in aUEC je SCU, cap = SCU-Nachfrage
function buildOffers(o,need){
  const now=Date.now()/1000,res={};
  for(const cid in need)res[cid]=new Map();
  for(const [tid,cid,price,scu,avg,st,mod] of P){
    if(!(cid in need))continue;
    const t=TM[tid];if(!t||!o.sys[t.s])continue;
    if(!o.illegal&&(t.nqa||CM[cid].il))continue;
    if(o.age&&now-mod>o.age*86400)continue;
    let cap=Infinity,est=false;
    if(o.demand){if(st===7)continue;if(scu>0)cap=scu;else{est=true;if(avg>0)cap=avg;}}
    const m=res[cid],cur=m.get(t.k);
    if(!cur||price>cur.price)m.set(t.k,{tid,price,cap,est,mod});
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
function candidates(need,off){
  const set=new Set(),all=new Set();
  for(const cid in need){
    const arr=[...off[cid].entries()].sort((a,b)=>b[1].price-a[1].price);
    arr.slice(0,15).forEach(([pk])=>set.add(pk));
    arr.forEach(([pk])=>all.add(pk));
  }
  [...all].map(pk=>[pk,evalSet([pk],need,off,false)]).sort((a,b)=>b[1]-a[1]).slice(0,40).forEach(([pk])=>set.add(pk));
  return {cands:[...set],all:[...all]};
}
function bestSet(k,cands,need,off){
  const kk=Math.min(k,cands.length);let bestR=-1,bestS=null;
  combos(cands,kk,S=>{const r=evalSet(S,need,off,false);if(r>bestR){bestR=r;bestS=S.slice();}});
  return bestS;
}
// Theoretisches Maximum: jede Ware an den jeweils besten Orten (beliebig viele Stopps)
function maxPlan(need,off){
  let rev=0;const places=new Set();
  for(const cid in need){
    const list=[...off[cid].entries()].map(([pk,o])=>({pk,price:o.price,cap:o.cap,o}));
    const f=fill(list,need[cid]);rev+=f.rev;f.asg.forEach(a=>places.add(a.o.pk));
  }
  return {rev,stops:places.size};
}

// ---- Darstellung ------------------------------------------------------
const ageTxt=m=>{const d=Math.floor((Date.now()/1000-m)/86400);return d<=0?'heute':d===1?'vor 1 Tag':`vor ${d} Tagen`;};
function stopsHtml(plan,need){
  const byPlace={};
  plan.det.forEach(({cid,f})=>f.asg.forEach(a=>{(byPlace[a.o.pk]=byPlace[a.o.pk]||[]).push({cid,take:a.take,o:a.o.o});}));
  const stops=Object.entries(byPlace).map(([pk,lines])=>({pk,lines,rev:lines.reduce((s,l)=>s+l.take*l.o.price,0)})).sort((a,b)=>b.rev-a.rev);
  return stops.map(s=>{
    const t0=TM[s.lines[0].o.tid];
    const terms=[...new Set(s.lines.map(l=>TM[l.o.tid].tn))].join(', ');
    return `<div class="stop"><div class="sname">${esc(t0.pl)} <span class="sloc">· ${esc(t0.lc)} · Terminal: ${esc(terms)}</span></div>`+
      s.lines.map(l=>`<div class="line"><span>${esc(CM[l.cid].n)}: ${nf(l.take,l.take%1?1:0)} SCU × ${nf(l.o.price)} aUEC`+
        `${l.o.est?' <span class="note">· Nachfrage geschätzt</span>':''}${(Date.now()/1000-l.o.mod)>7*86400?` <span class="note">· Preis von ${ageTxt(l.o.mod)}</span>`:''}</span>`+
        `<span class="a">${nf(l.take*l.o.price)} aUEC</span></div>`).join('')+
      `<div class="line" style="font-weight:600"><span>Summe an diesem Stopp</span><span class="a">${nf(s.rev)} aUEC</span></div></div>`;
  }).join('');
}
function compute(){
  const out=$('res');const {need,bad}=getNeed();const o=getOpts();
  const ids=Object.keys(need);
  const tot=ids.reduce((s,c)=>s+need[c],0);
  $('sum').textContent=ids.length?`${ids.length} Ware${ids.length>1?'n':''}, zusammen ${nf(tot,tot%1?1:0)} SCU`:'';
  if(!ids.length){out.innerHTML='<div class="card"><div class="empty">Gib oben mindestens eine Ware und eine SCU-Menge ein.</div></div>';return;}
  const off=buildOffers(o,need);
  const warns=[];
  const missing=ids.filter(c=>off[c].size===0);
  missing.forEach(c=>warns.push(`Für ${esc(CM[c].n)} gibt es mit den aktuellen Einstellungen keinen Abnehmer.`));
  const active=ids.filter(c=>off[c].size>0);
  const need2={};active.forEach(c=>need2[c]=need[c]);
  let html=bad?'<div class="warn">Mindestens ein Warenname wird nicht erkannt (rot markiert). Bitte aus der Vorschlagsliste wählen.</div>':'';
  html+=warns.map(w=>`<div class="warn">${w}</div>`).join('');
  if(!active.length){out.innerHTML=html;return;}
  const {cands,all}=candidates(need2,off);
  const mx=maxPlan(need2,off);
  const cards=[];
  for(const k of [1,2,3]){
    if(k>all.length&&k>1)break;
    const S=bestSet(k,cands,need2,off);const plan=evalSet(S,need2,off,true);
    const used=new Set();plan.det.forEach(d=>d.f.asg.forEach(a=>used.add(a.o.pk)));
    cards.push({k,plan,used:used.size});
  }
  // gleiche Ergebnisse (ein Stopp reicht schon) nicht doppelt zeigen
  const shown=[];cards.forEach(c=>{const last=shown[shown.length-1];if(last&&Math.abs(last.plan.rev-c.plan.rev)<0.5&&c.used<=last.used)return;shown.push(c);});
  shown.forEach((c,i)=>{
    const pct=mx.rev>0?c.plan.rev/mx.rev*100:100;
    const gain=i>0?c.plan.rev-shown[i-1].plan.rev:null;
    const unsold=c.plan.det.filter(d=>d.f.rest>0.0001).map(d=>`${nf(d.f.rest,d.f.rest%1?1:0)} SCU ${esc(CM[d.cid].n)}`);
    html+=`<div class="card"><div class="chead"><div class="ctitle">${c.used} Stopp${c.used>1?'s':''}${i===0?' · bester Einzelstopp':''}</div><div class="total">${nf(c.plan.rev)} aUEC</div></div>`+
      `<div class="meta">${nf(pct,1)} % des theoretischen Maximums${gain!=null?` · ${gain>=0?'+':''}${nf(gain)} aUEC gegenüber ${shown[i-1].used} Stopp${shown[i-1].used>1?'s':''}`:''}</div>`+
      (unsold.length?`<div class="warn">Nicht verkauft (keine ausreichende Nachfrage an diesen Stopps): ${unsold.join(', ')}</div>`:'')+
      stopsHtml(c.plan,need2)+`</div>`;
  });
  const maxPlanFull=(()=>{const det=[];for(const cid in need2){const list=[...off[cid].entries()].map(([pk,x])=>({pk,price:x.price,cap:x.cap,o:x}));det.push({cid,f:fill(list,need2[cid])});}return {det};})();
  html+=`<div class="card"><div class="chead"><div class="ctitle">Theoretisches Maximum</div><div class="total" style="color:#4a5a70">${nf(mx.rev)} aUEC</div></div>`+
    `<div class="meta">Jede Ware am jeweils besten Ort verkauft: ${mx.stops} Stopp${mx.stops>1?'s':''}. Dient nur als Vergleich.</div>`+
    `<details><summary>Stopps anzeigen</summary>${stopsHtml(maxPlanFull,need2)}</details></div>`;
  out.innerHTML=html;
}
if(!load())addRow('','');
if(!$('rows').children.length)addRow();
compute();
</script>
</body>
</html>
'''


def _place(t):
    name = t["space_station"] or t["city"] or t["outpost"] or t["nickname"] or t["displayname"] or t["name"] or "?"
    return name


def build(con, target):
    terms = []
    for r in con.execute("SELECT * FROM uex_terminals"):
        t = dict(r)
        place = _place(t)
        loc = " › ".join(x for x in (t["star_system"], t["planet"], t["moon"]) if x)
        terms.append({"id": t["id"], "tn": t["nickname"] or t["name"] or str(t["id"]), "s": t["star_system"],
                      "k": f"{t['star_system']}|{place}", "pl": place, "lc": loc, "nqa": t["is_nqa"]})
    used_c = {r[0] for r in con.execute("SELECT DISTINCT id_commodity FROM uex_prices")}
    coms = [{"id": r["id"], "n": r["name"], "k": r["kind"] or "", "il": r["is_illegal"]}
            for r in con.execute("SELECT * FROM uex_commodities ORDER BY lower(name)") if r["id"] in used_c]
    prices = [[r["id_terminal"], r["id_commodity"], round(r["price_sell"]), round(r["scu_sell"], 1),
               round(r["scu_sell_avg"], 1), r["status_sell"], r["date_modified"]]
              for r in con.execute("SELECT * FROM uex_prices")]
    newest = max((p[6] for p in prices), default=0)
    stand = dt.datetime.fromtimestamp(newest).strftime("%d.%m.%Y %H:%M") if newest else "unbekannt"

    def js(x):
        return json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = (PAGE.replace("__TERMINALS__", js(terms)).replace("__COMMODITIES__", js(coms))
            .replace("__PRICES__", js(prices)).replace("__UEXSTAND__", stand)
            .replace("__STAND__", dt.datetime.now().strftime("%d.%m.%Y %H:%M")))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, target)
    return len(prices)
