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
  html { font-size:115%; }   /* alle Schriftgrößen sind in rem: hier zentral skalieren */
  body { background:#f5f7fa; color:#1a2030; font-family:'Exo 2',sans-serif; padding:28px 28px 48px; max-width:none; }
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
  .meta b { color:#1c2733; font-size:.84rem; }
  .stop { border-top:1px solid #edf1f6; padding:9px 0 3px; }
  .sname { font-weight:600; } .sloc { font-size:.74rem; color:#6b7a90; }
  .line { display:flex; justify-content:space-between; gap:14px; font-size:.84rem; padding:2px 0 2px 12px; flex-wrap:wrap; }
  .line .a { font-variant-numeric:tabular-nums; white-space:nowrap; }
  .note { font-size:.7rem; color:#b45309; }
  .warn { background:#fef3c7; border:1px solid #f0d58a; color:#7a4b00; border-radius:8px; padding:7px 12px; font-size:.8rem; margin-bottom:10px; }
  .empty { color:#6b7a90; font-size:.9rem; padding:8px 0; }
  details summary { cursor:pointer; font-size:.8rem; color:#4a5a70; margin-top:4px; }
  details.adv { margin-top:10px; }
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
    <span class="syl">Zielsysteme (Verkauf) <span id="os"></span></span>
    <label>Startpunkt <select id="st"></select></label>
    <label>Optimieren nach <select id="om"><option value="profit" selected>Gewinn je Stunde</option><option value="net">Netto-Erlös</option><option value="time">Kürzeste Zeit</option></select></label>
    <label>Streckenkosten <input type="number" id="oc" min="0" step="1" placeholder="auto" style="width:120px"> aUEC je Gm</label>
  </div>
  <div class="opts" style="margin-top:10px">
    <label>Reisedaten <select id="qm"><option value="avg" selected>Durchschnitt aller Quantum Drives</option><option value="ship">Mein Schiff (Standard-Quantum-Drive)</option><option value="drive">Mein Schiff mit gewähltem Quantum Drive</option></select></label>
    <label id="qsl" style="display:none">Schiff <select id="qs"></select></label>
    <label id="qdl" style="display:none">Quantum Drive <span id="qdsz"></span> <select id="qd"></select></label>
  </div>
  <div class="sum" id="qinfo"></div>
  <div class="opts" style="margin-top:10px">
    <label><input type="checkbox" id="od" checked> Nachfrage der Terminals berücksichtigen</label>
    <label><input type="checkbox" id="oi"> illegale Waren und No-Questions-Asked-Terminals einbeziehen</label>
    <label>Preise ignorieren, die älter sind als
      <select id="oa"><option value="0">(egal)</option><option value="3">3 Tage</option><option value="7">7 Tage</option><option value="14" selected>14 Tage</option><option value="30">30 Tage</option></select></label>
  </div>
  <details class="adv"><summary>Zeit-Annahmen (für die Reisezeit)</summary>
    <div class="opts" style="margin-top:8px">
      <label>Quantum-Geschwindigkeit <input type="number" id="oq" min="20" step="10" placeholder="aus Reisedaten" style="width:110px"> Mm/s</label>
      <label>Zuschlag je Flug (zusätzlich zur Spool-Zeit) <input type="number" id="ov" min="0" step="0.5" value="0.8" style="width:70px"> Min</label>
      <label>Dauer Sprungtunnel <input type="number" id="ot" min="0" step="0.5" value="5" style="width:70px"> Min</label>
      <label>„Netto-Erlös“: gleichwertig bis <input type="number" id="ont" min="0" max="50" step="1" value="5" style="width:70px"> % unter dem besten Erlös (dann gewinnt die kürzere Route)</label>
      <label>„Kürzeste Zeit“: mindestens <input type="number" id="omr" min="0" max="100" step="5" value="90" style="width:70px"> % des möglichen Erlöses</label>
      <label>Treibstoff je Sprungtunnel <input type="number" id="of" min="0" max="100" step="1" value="5" style="width:70px"> % des Quantum-Tanks</label>
      <label>Zeit je Verkaufsstopp <input type="number" id="ow" min="0" step="1" value="5" style="width:70px"> Min</label>
    </div>
  </details>
  <div class="hint">Als Startpunkt kannst du einen Himmelskörper (z. B. ArcCorp) oder einen Ort in jedem System wählen, unabhängig von den Zielsystemen; diese bestimmen nur, wo verkauft wird. Die Route läuft vom Startpunkt über die Verkaufsstopps, ein Rückweg ist nicht eingerechnet. Stopps im selben System werden zusammen angefahren, die Reihenfolge ist die mit der kürzesten Zeit.
  <b>Optimieren nach</b>: „Gewinn je Stunde“ vergleicht Erlös und Reisezeit, „Netto-Erlös“ zieht nur die Streckenkosten ab, „Kürzeste Zeit“ sucht die schnellste Route, die mindestens den eingestellten Anteil (Standard 90 %, unter „Zeit-Annahmen“) des überhaupt möglichen Erlöses erreicht; ein paar übrig gebliebene SCU billiger Ware zählen dabei nicht.
  <b>Reisedaten</b>: „Durchschnitt“ rechnet mit den Mittelwerten aller Quantum Drives (Geschwindigkeit, Spool-Zeit, Treibstoffverbrauch), ohne dass du etwas eingeben musst. Mit „Mein Schiff“ nimmt der Rechner den Quantum Drive, den das Schiff ab Werk hat, und mit „gewähltem Quantum Drive“ genau den Drive, den du eingebaut hast. Bei einem gewählten Schiff prüft der Rechner auch, ob der Quantum-Tank für die Etappen reicht. Deine Auswahl wird im Browser gemerkt.
  Die <b>Streckenkosten</b> sind die Treibstoffkosten je Gigameter (Verbrauch des Quantum Drives × Preis für Quantum Fuel laut UEX: __QFTXT__). Lässt du das Feld leer, rechnet die Seite damit; trägst du einen Wert ein, gilt dein Wert (z. B. um Risiko mit einzupreisen). Je höher der Wert, desto eher wählt der Rechner nahe Stopps, bei 0 zählt nur der Erlös.
  Ein „Stopp“ ist ein Ort (Station, Stadt oder Außenposten); mehrere Terminals am selben Ort zählen als ein Stopp. Bei den Zielsystemen (Verkauf) kannst du mehrere gleichzeitig anhaken; die Entfernungen innerhalb eines Systems sind UEX-Schätzungen (geladen: __DTXT__). Bei einem Systemwechsel fliegt der Rechner zum Jump Point (Gateway-Station), springt und fliegt vom Gateway im Zielsystem zum Stopp.
  Die <b>Reisezeit</b> ist eine grobe Schätzung aus Entfernung, Quantum-Geschwindigkeit, Spool-Zeit des Drives plus einem Zuschlag je Flug, der Tunnelzeit und der Zeit je Verkaufsstopp; die Werte kannst du unter „Zeit-Annahmen“ anpassen. Fehlt UEX eine Entfernung, rechnet der Rechner mit dem Mittelwert und markiert die Etappe als „geschätzt“.</div>
</div>

<div id="res"></div>

<div class="footer">Quelle: UEX Corp (Community-Preise je Terminal, stündlich aktualisiert, Fehler möglich). Preise in aUEC je SCU, Entfernungen in Gigametern (UEX-Schätzung). Die Preise ändern sich im Spiel mit Angebot und Nachfrage; die Berechnung ist eine Orientierung, keine Garantie. Seite erzeugt __STAND__.</div>

<script>
const T = __TERMINALS__;
const PL = __PLACES__;
const C = __COMMODITIES__;
const P = __PRICES__;
const DT = __DISTS__;
const GWT = __GATEWAYS__;
const QD = __QD__;     // [Klasse, Name, Größe, Grade, Klasse, SCU je Gm, Mm/s, Spool s, Cooldown s]
const SH = __SHIPS__;  // [Schiff, Tank SCU, Klasse des Standard-Drives]
const QFP = __QFP__;   // aUEC je SCU Quantum Fuel (UEX), 0 = unbekannt
const TM={}, CM={}, CBN={};
T.forEach(t=>TM[t.id]=t); C.forEach(c=>{CM[c.id]=c;CBN[c.n.toLowerCase()]=c;});
const N=PL.length, DM=new Float32Array(N*N).fill(-1);
for(let i=0;i<N;i++)DM[i*N+i]=0;
DT.forEach(([i,j,d])=>{DM[i*N+j]=d;DM[j*N+i]=d;});
// Notwert für unbekannte Strecken ohne Anhaltspunkt: Median aller bekannten Entfernungen
let MED=10;{const a=DT.map(x=>x[2]).filter(d=>d>0).sort((x,y)=>x-y);if(a.length)MED=a[a.length>>1];}
let M={speed:262,ovh:1,tun:5,dwell:5};   // QT-Geschwindigkeit Mm/s, Zuschlag je Flug, Tunnelzeit (Standard 5), Zeit je Verkaufsstopp (Minuten)
let DX=DM,TX=DM,EX=DM;
const QDM={};QD.forEach(q=>QDM[q[0]]=q);
const SHM={};SH.forEach(x=>SHM[x[0]]=x);
const med=a=>{a=a.filter(x=>x!=null&&x>0).sort((x,y)=>x-y);if(!a.length)return null;const h=a.length>>1;return a.length%2?a[h]:(a[h-1]+a[h])/2;};
// Durchschnittswerte (Median aller Quantum Drives); Rückfall, falls die Tabelle noch leer ist
const QAVG={speed:med(QD.map(q=>q[6]))||262,fuel:med(QD.map(q=>q[5]))||0.0167,spool:med(QD.map(q=>q[7]))||6.6};
const FP=QFP>0?QFP:1760;
const TKAVG=med(SH.map(x=>x[1]));   // mittlere Tankgröße aller bekannten Schiffe (SCU), für die Stufe „Durchschnitt“
const legT=d=>d>0?M.ovh+d*1000/M.speed/60:0;
// Schätzung einer fehlenden Entfernung über bekannte dritte Orte (Dreiecksungleichung: Mitte zwischen Unter- und Obergrenze)
function estD(i,j){
  let lo=0,hi=Infinity;
  for(let k=0;k<N;k++){if(k===i||k===j)continue;const a=DM[i*N+k],b=DM[k*N+j];if(a<0||b<0)continue;lo=Math.max(lo,Math.abs(a-b));hi=Math.min(hi,a+b);}
  return hi<Infinity?(lo+hi)/2:MED;
}
// Etappe von Ort i nach Ort j: Entfernung (Gm), Zeit (Min), e=1 wenn geschätzt; bei Systemwechsel über die Gateways beider Systeme
function legInfo(i,j){
  if(i===j)return {d:0,m:0,t:0,e:0};
  const a=PL[i].s,b=PL[j].s;
  if(a===b){const d=DM[i*N+j];if(d>=0)return {d,m:d,t:legT(d),e:0};const x=estD(i,j);return {d:x,m:x,t:legT(x),e:1};}
  const g1=GWT[a+'>'+b],g2=GWT[b+'>'+a];let e=0,d1=-1,d2=-1;
  if(g1!=null)d1=DM[i*N+g1];
  if(g2!=null)d2=DM[g2*N+j];
  if(d1<0){d1=g1!=null?estD(i,g1):MED;e=1;}
  if(d2<0){d2=g2!=null?estD(g2,j):MED;e=1;}
  return {d:d1+d2,m:Math.max(d1,d2),t:legT(d1)+M.tun+legT(d2),e,cross:true,g1,g2};
}
function buildLegs(){
  DX=new Float32Array(N*N);TX=new Float32Array(N*N);EX=new Uint8Array(N*N);
  for(let i=0;i<N;i++)for(let j=0;j<N;j++){const l=legInfo(i,j);DX[i*N+j]=l.d;TX[i*N+j]=l.t;EX[i*N+j]=l.e;}
}
const $=id=>document.getElementById(id);
const nf=(n,d=0)=>Number(n).toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});
const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const LS='sc_fracht_v3',LS_OLD='sc_fracht_v2';
const SYS=[...new Set(T.map(t=>t.s))].sort((a,b)=>['Stanton','Pyro','Nyx'].indexOf(a)-['Stanton','Pyro','Nyx'].indexOf(b));

// ---- Oberfläche -------------------------------------------------------
$('cl').innerHTML=C.map(c=>`<option value="${esc(c.n)}">`).join('');
$('os').innerHTML=SYS.map((x,i)=>`<label class="sy"><input type="checkbox" value="${esc(x)}"${i===0?' checked':''}> ${esc(x)}</label>`).join(' ');
const selSys=()=>[...document.querySelectorAll('#os input:checked')].map(i=>i.value);
function fillStart(sel){
  // Startpunkte: alle Systeme, unabhängig von den gewählten Zielsystemen
  const sy=SYS,multi=sy.length>1;let h='<option value="">(kein Startpunkt)</option>';
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
const dlabel=q=>`${q[1]} · S${q[2]}${q[3]?' '+q[3]:''}${q[4]&&q[4]!=='None'?' '+q[4]:''} · ${nf(q[6])} Mm/s`;
$('qs').innerHTML=SH.slice().sort((a,b)=>a[0].localeCompare(b[0],'de')).map(x=>`<option value="${esc(x[0])}">${esc(x[0])}</option>`).join('');
// Quantum-Drive-Auswahl: nur Drives in der Größe des Standard-Drives des gewählten Schiffs (andere passen nicht hinein)
function fillDrives(keep){
  const sh=SHM[$('qs').value],std=sh&&QDM[sh[2]]?QDM[sh[2]]:null;
  const list=QD.filter(q=>!std||q[2]===std[2]).sort((a,b)=>a[2]-b[2]||a[6]-b[6]||a[1].localeCompare(b[1]));
  $('qd').innerHTML=list.map(q=>`<option value="${esc(q[0])}">${esc(dlabel(q))}</option>`).join('');
  const ok=c=>c&&list.some(q=>q[0]===c);
  $('qd').value=ok(keep)?keep:(std&&ok(std[0])?std[0]:(list[0]?list[0][0]:''));
  $('qdsz').textContent=std?`(nur Größe ${std[2]}, passend zu ${$('qs').value})`:'';
}
fillDrives();
[...$('qm').options].forEach(op=>{if(op.value==='ship'&&!SH.length)op.disabled=true;if(op.value==='drive'&&!QD.length)op.disabled=true;});
function qmode(){const v=$('qm').value;return (v==='ship'&&!SH.length)||(v==='drive'&&!QD.length)?'avg':v;}
// gewählte Reisedaten: Geschwindigkeit (Mm/s), Treibstoff (SCU je Gm), Spool (s), Tankgröße (SCU, null = unbekannt)
function qdSel(){
  const m=qmode(),ship=(m!=='avg'&&SHM[$('qs').value])||null;
  let d=null,label='Durchschnitt aller Quantum Drives';
  if(m==='ship'&&ship)d=QDM[ship[2]];
  if(m==='drive')d=QDM[$('qd').value]||null;
  if(d)label=`${d[1]} (Größe ${d[2]}${d[3]?', '+d[3]:''})`;
  return {m,ship,drive:d,label,speed:d?d[6]:QAVG.speed,fuel:d?d[5]:QAVG.fuel,spool:d?(d[7]||QAVG.spool):QAVG.spool,tank:ship?ship[1]:null};
}
function showQ(){
  const m=qmode();$('qsl').style.display=m==='avg'?'none':'';$('qdl').style.display=m==='drive'?'':'none';
  const q=qdSel(),auto=q.fuel*FP;
  $('oc').placeholder='auto: '+nf(auto,auto<10?1:0);$('oq').placeholder=nf(q.speed);
  let t=`Rechnet mit: ${q.label}${q.m==='avg'?' (Mittelwert)':''} · ${nf(q.speed)} Mm/s · Spool ${nf(q.spool,1)} s · Verbrauch ${nf(q.fuel,4)} SCU/Gm`
    +` · Treibstoffkosten ca. ${nf(auto,auto<10?1:0)} aUEC/Gm${QFP>0?'':' (Preis geschätzt)'}`;
  if(q.tank)t+=` · Tank ${nf(q.tank,1)} SCU, Reichweite ca. ${nf(q.tank/q.fuel)} Gm`;
  if(m==='ship'&&!q.drive)t+=' · für dieses Schiff ist kein Quantum Drive bekannt, es gelten die Durchschnittswerte';
  {const tk=q.tank||TKAVG,pc=+$('of').value||0;if(tk&&pc>0)t+=` · Sprungtunnel: ${nf(pc)} % des Tanks = ${nf(tk*pc/100,2)} SCU${q.tank?'':' (mittlere Tankgröße)'}`;else if(pc>0)t+=' · Der Sprungtunnel-Verbrauch ist nicht eingerechnet, die Tankgröße ist noch unbekannt';}
  if(!SH.length)t+=' · Die Zuordnung Schiff → Quantum Drive wird noch geladen (der Updater holt je Lauf nur einen Teil).';
  $('qinfo').textContent=t;
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
$('os').addEventListener('change',schedule);
['od','oi','oa','oc','om','oq','ov','ot','of','omr','ont','ow','st','qm','qs','qd'].forEach(i=>$(i).addEventListener('input',schedule));
// Schiff gewechselt: im Modus „gewählter Drive“ zuerst dessen Standard-Drive vorwählen
$('qs').addEventListener('input',()=>fillDrives());
$('qm').addEventListener('input',()=>{if($('qm').value==='drive')fillDrives();});
['qm','qs','qd'].forEach(i=>$(i).addEventListener('input',showQ));
document.addEventListener('input',e=>{if(e.target.matches('.cn,.cs'))schedule();});

const numIn=(id,def,min)=>{const v=parseFloat($(id).value);return isNaN(v)?def:Math.max(min,v);};
function getOpts(){const q=qdSel(),oc=$('oc').value.trim();
  return {sys:selSys(),demand:$('od').checked,illegal:$('oi').checked,age:+$('oa').value,start:$('st').value,q,
  cost:oc===''?q.fuel*FP:Math.max(0,+oc||0),
  mode:$('om').value,speed:numIn('oq',q.speed,20),ovh:numIn('ov',0.8,0)+q.spool/60,tun:numIn('ot',5,0),tf:(q.tank||TKAVG||0)*numIn('of',5,0)/100,mr:Math.min(100,numIn('omr',90,0))/100,nt:Math.min(50,numIn('ont',5,0))/100,dwell:numIn('ow',5,0)};}
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
  od:o.demand,oi:o.illegal,oa:$('oa').value,os:o.sys,st:o.start,oc:$('oc').value,om:$('om').value,oq:$('oq').value,ov:$('ov').value,ot:$('ot').value,op:$('of').value,omr:$('omr').value,ont:$('ont').value,ow:$('ow').value,qm:$('qm').value,qs:$('qs').value,qd:$('qd').value}));}catch(e){}}
function load(){try{let s=JSON.parse(localStorage.getItem(LS)||'null'),old=false;
  if(!s){s=JSON.parse(localStorage.getItem(LS_OLD)||'null');old=true;}   // alte Version: Waren, Systeme, Startpunkt übernehmen; Kosten und Geschwindigkeit gelten neu
  if(!s)return false;
  (s.rows||[]).forEach(r=>addRow(r[0],r[1]));$('od').checked=s.od!==false;$('oi').checked=!!s.oi;if(s.oa!=null)$('oa').value=s.oa;
  if(!old&&s.oc!=null&&s.oc!=='')$('oc').value=s.oc;
  if(!old){if(['avg','ship','drive'].includes(s.qm)&&!$('qm').querySelector(`option[value=${s.qm}]`).disabled)$('qm').value=s.qm;
    if(s.qs&&SHM[s.qs])$('qs').value=s.qs;fillDrives(s.qd);}
  if(['profit','net','time'].includes(s.om))$('om').value=s.om;
  (old?['ow']:['oq','ov','ot','ow']).forEach(k=>{if(k==='ot'&&s[k]==='3')return;   // 3 Min war der frühere Standardwert
    if(s[k]!=null&&s[k]!=='')$(k).value=s[k];});
  if(!old&&s.op!=null&&s.op!=='')$('of').value=s.op;
  if(!old&&s.omr!=null&&s.omr!=='')$('omr').value=s.omr;
  if(!old&&s.ont!=null&&s.ont!=='')$('ont').value=s.ont;
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
    if(o.demand){if(scu>0)cap=scu;else{est=true;if(avg>0)cap=avg;}}
    const full=st===7;   // UEX: Lager voll, evtl. keine Nachfrage; Spieler können dort trotzdem noch verkaufen -> nur Hinweis
    const m=res[cid],cur=m.get(t.pi);
    if(!cur||price>cur.price)m.set(t.pi,{tid,price,cap,est,mod,full});
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
// Start: je Ort Entfernung (Gm), Zeit (Min), geschätzt? und der Ausgangsort q; null = kein Startpunkt
function startVec(o){
  if(!o.start)return null;
  let qs;
  if(o.start.startsWith('p:'))qs=[+o.start.slice(2)];
  else{const [sy,b]=o.start.slice(2).split('|');qs=[];PL.forEach((p,i)=>{if(p.s===sy&&p.b===b)qs.push(i);});}
  if(!qs.length)return null;
  const d=new Float32Array(N),t=new Float32Array(N),e=new Uint8Array(N),q=new Int32Array(N);
  for(let j=0;j<N;j++){let bi=qs[0];for(const x of qs)if(TX[x*N+j]<TX[bi*N+j])bi=x;
    q[j]=bi;d[j]=DX[bi*N+j];t[j]=TX[bi*N+j];e[j]=EX[bi*N+j];}
  return {d,t,e,q};
}
function startSys(o){if(!o.start)return null;if(o.start.startsWith('p:'))return PL[+o.start.slice(2)].s;return o.start.slice(2).split('|')[0];}
const PIX={};function permIdx(n){return PIX[n]||(PIX[n]=perms([...Array(n).keys()]));}
// Strecke, Zeit (inkl. Zeit je Verkaufsstopp) und Zahl der Systemwechsel einer Reihenfolge
function pathStats(order,st,s0){
  let d=0,t=0,e=0,ch=0,prev=-1;
  for(const p of order){
    if(prev<0){if(st){d+=st.d[p];t+=st.t[p];e|=st.e[p];if(s0&&s0!==PL[p].s)ch++;}}
    else{const k=prev*N+p;d+=DX[k];t+=TX[k];e|=EX[k];if(PL[prev].s!==PL[p].s)ch++;}
    prev=p;
  }
  return {d,t:t+M.dwell*order.length,e,ch};
}
// beste Reihenfolge: erst wenigste Systemwechsel (Stopps im selben System zusammen), dann kürzeste Zeit, dann kürzeste Strecke
function bestRoute(S,st,s0){
  let best=null;
  for(const ix of permIdx(S.length)){
    const order=ix.map(i=>S[i]),r=pathStats(order,st,s0);
    if(!best||r.ch<best.ch||(r.ch===best.ch&&(r.t<best.t-1e-9||(Math.abs(r.t-best.t)<=1e-9&&r.d<best.d))))best={order,...r};
  }
  return best;
}
// Zielwert je nach Modus: Gewinn je Stunde, Netto-Erlös oder (bei kürzester Zeit) erst möglichst alles verkaufen, dann Zeit
function score(rev,rest,r,o){
  const net=rev-o.cost*r.d-r.ch*o.tf*FP,hrs=Math.max(r.t,1)/60;
  // Kürzeste Zeit: zählt nur, was mindestens den Mindest-Erlös (Anteil am Maximum) erreicht; darunter wird stark bestraft
  if(o.mode==='time'){const pen=o.mxRev>0?Math.max(0,o.mr-rev/o.mxRev):0;return -pen*1e12-r.t+rev*1e-9;}
  // Netto-Erlös mit Toleranz: Routen bis nt unter dem besten Netto gelten als gleichwertig, dann gewinnt die kürzere
  if(o.mode==='nettol'){const pen=o.netM>0?Math.max(0,(1-o.nt)*o.netM-net)/o.netM:0;return -pen*1e12-r.t+net*1e-9;}
  return o.mode==='net'?net:net/hrs;
}
function candidates(need,off,o,st){
  const set=new Set(),all=new Set();
  for(const cid in need){
    const arr=[...off[cid].entries()].map(([pk,x])=>{
      const v=x.price*Math.min(need[cid],x.cap)-(o.cost>0&&st?o.cost*st.d[pk]:0);return [pk,v];}).sort((a,b)=>b[1]-a[1]);
    arr.slice(0,12).forEach(([pk])=>set.add(pk));
    arr.forEach(([pk])=>all.add(pk));
  }
  const single=[...all].map(pk=>[pk,evalSet([pk],need,off,false)]);
  single.map(([pk,r])=>[pk,r-(st&&o.cost>0?o.cost*st.d[pk]:0)]).sort((a,b)=>b[1]-a[1]).slice(0,30).forEach(([pk])=>set.add(pk));
  if(o.mode!=='net'){   // auch bei 'nettol': schnelle und gut bezahlte Orte zusätzlich prüfen
    single.map(([pk,r])=>[pk,(r-(st?o.cost*st.d[pk]:0))/((st?st.t[pk]:0)+M.dwell+1)]).sort((a,b)=>b[1]-a[1]).slice(0,12).forEach(([pk])=>set.add(pk));
    if(st)[...all].sort((a,b)=>st.t[a]-st.t[b]).slice(0,10).forEach(pk=>set.add(pk));
  }
  return {cands:[...set],all:[...all]};
}
// bestes Bündel mit genau k Orten (alle besucht); Ziel je nach Modus
function evalUsed(S,need,off){
  let rev=0,rest=0;const used=new Set();
  for(const cid in need){
    const list=[];
    for(const pk of S){const o=off[cid].get(pk);if(o)list.push({pk,price:o.price,cap:o.cap});}
    list.sort((a,b)=>b.price-a.price);
    let left=need[cid];
    for(const o of list){if(left<=0)break;const take=Math.min(left,o.cap);if(!(take>0))continue;rev+=take*o.price;left-=take;used.add(o.pk);}
    rest+=Math.max(left,0);
  }
  return {rev,rest,used:[...used]};
}
function bestExact(k,cands,need,off,o,st,s0){
  const kk=Math.min(k,cands.length);let bestV=-Infinity,bestS=null;
  const simple=o.mode==='net'&&!(o.cost>0)&&!(o.tf>0);
  combos(cands,kk,S=>{
    const e=evalUsed(S,need,off);let v;
    if(simple)v=e.rev;else v=score(e.rev,e.rest,bestRoute(e.used,st,s0),o);
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
function fmtT(m){m=Math.round(m);if(m<1)return 'unter 1 Min';if(m<60)return `ca. ${m} Min`;return `ca. ${Math.floor(m/60)} Std ${m%60} Min`;}
function legTxt(L,i,o){
  if(!L)return '';
  let s;
  if(L.cross)s=` · <b>Systemwechsel</b> über ${esc(L.g1!=null?PL[L.g1].pl:'den Jump Point')} · <b>${nf(L.d)} Gm</b>, ${fmtT(L.t)} (davon Sprungtunnel ${nf(M.tun,M.tun%1?1:0)} Min${o&&o.tf>0?`, ${nf(o.tf,2)} SCU Treibstoff`:''})`;
  else if(L.d===0)s=i===0?' · am Startpunkt':' · am selben Ort';
  else s=` · <b>${nf(L.d)} Gm</b>, ${fmtT(L.t)} ${i===0?'vom Startpunkt':'vom vorherigen Stopp'}`;
  return s+(L.e?' <span class="note">(geschätzt)</span>':'');
}
function stopsHtml(plan,order,legs,o){
  const byPlace={};
  plan.det.forEach(({cid,f})=>f.asg.forEach(a=>{(byPlace[a.o.pk]=byPlace[a.o.pk]||[]).push({cid,take:a.take,o:a.o.o});}));
  const seq=order&&order.length?order:Object.keys(byPlace).map(Number).sort((a,b)=>sum(byPlace[b])-sum(byPlace[a]));
  function sum(lines){return lines.reduce((s,l)=>s+l.take*l.o.price,0);}
  const seqF=seq.filter(pk=>byPlace[pk]);
  return seqF.map((pk,i)=>{
    const lines=byPlace[pk].slice().sort((a,b)=>b.take*b.o.price-a.take*a.o.price),pl=PL[pk];
    const terms=[...new Set(lines.map(l=>TM[l.o.tid].tn))].join(', ');
    const leg=legTxt(legs&&legs[i],i,o);
    return `<div class="stop"><div class="sname">${order&&order.length?`${i+1}. `:''}${esc(pl.pl)} <span class="sloc">· ${esc(pl.lc)} · Terminal: ${esc(terms)}${leg}</span></div>`+
      lines.map(l=>`<div class="line"><span>${esc(CM[l.cid].n)}: ${nf(l.take,l.take%1?1:0)} SCU × ${nf(l.o.price)} aUEC`+
        `${l.o.est?' <span class="note">· Nachfrage geschätzt</span>':''}${l.o.full?' <span class="note">· laut UEX Lager voll, evtl. keine Nachfrage</span>':''}${(Date.now()/1000-l.o.mod)>7*86400?` <span class="note">· Preis von ${ageTxt(l.o.mod)}</span>`:''}</span>`+
        `<span class="a">${nf(l.take*l.o.price)} aUEC</span></div>`).join('')+
      `<div class="line" style="font-weight:600"><span>Summe an diesem Stopp</span><span class="a">${nf(sum(lines))} aUEC</span></div></div>`;
  }).join('');
}
// Reichweite: ein einzelner Quantum-Flug darf nicht weiter sein, als der Tank hergibt; die ganze Route evtl. mit Tankstopp
function rangeWarn(c,o){
  const q=o.q;if(!q.tank||!(q.fuel>0))return '';
  const range=q.tank/q.fuel,far=c.legs.filter(l=>l&&l.m>range);
  if(far.length)return `<div class="warn">Mit dem Quantum-Tank von ${nf(q.tank,1)} SCU kommst du etwa ${nf(range)} Gm weit, mindestens ein Flug dieser Route ist länger (bis ca. ${nf(Math.max(...far.map(l=>l.m)))} Gm). Du brauchst dafür einen Drive mit geringerem Verbrauch, einen größeren Tank oder einen Zwischenstopp.</div>`;
  const fuel=c.r.d*q.fuel+c.r.ch*o.tf;
  if(fuel>q.tank)return `<div class="warn">Die ganze Route braucht ca. ${nf(fuel,1)} SCU Treibstoff, dein Quantum-Tank fasst ${nf(q.tank,1)} SCU: unterwegs tanken.</div>`;
  return '';
}
function compute(){
  const out=$('res');const {need,bad}=getNeed();const o=getOpts();
  M={speed:o.speed,ovh:o.ovh,tun:o.tun,dwell:o.dwell};buildLegs();showQ();
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
  const st=startVec(o),s0=startSys(o);
  let oo=o;
  // Keine Entfernungsdaten da? Dann nur nach Erlös rechnen und das sagen
  if(!DM.some(v=>v>0)&&(o.cost>0||o.mode!=='net')){warns.push('Die Entfernungsdaten sind noch nicht geladen, deshalb zählt vorerst nur der Erlös.');oo={...o,cost:0,mode:'net'};}
  // Alternativen mit 1 bis 3 Stopps (nach Netto-Erlös) und, falls anders gewählt, die besten Pläne nach dem gewählten Ziel
  const mx=maxPlan(need2,off);oo={...oo,mxRev:mx.rev};
  const ooN={...oo,mode:'net'};
  const best3=(oc,ov)=>{const {cands,all}=candidates(need2,off,oc,st);return [1,2,3].map(k=>k>all.length&&k>1?null:bestExact(k,cands,need2,off,oc,st,s0));};
  const exN=best3(ooN);
  // Netto-Erlös: erst bester Netto-Wert M, dann gilt alles ab (1 - Toleranz) x M als gleichwertig und die kürzeste Route gewinnt
  const useTol=oo.mode==='net'&&oo.nt>0&&DM.some(v=>v>0);
  if(useTol){const M0=Math.max(...exN.filter(Boolean).map(x=>x.v));oo={...oo,mode:'nettol',netM:M0};}
  const exM=oo.mode==='net'?null:best3(oo);
  const cards=[],seen=new Set();
  function addCard(pick){
    const plan=evalSet(pick.S,need2,off,true);
    const usedSet=new Set();plan.det.forEach(d=>d.f.asg.forEach(a=>usedSet.add(a.o.pk)));
    const used=[...usedSet],sig=[...used].sort((a,b)=>a-b).join();
    if(seen.has(sig))return;seen.add(sig);
    const r=bestRoute(used,st,s0);
    const order=r.order;
    const legs=order.map((p,i)=>i===0?(st?legInfo(st.q[p],p):null):legInfo(order[i-1],p));
    const cost=oo.cost*r.d+r.ch*oo.tf*FP;
    cards.push({plan,used,order,r,legs,cost,net:plan.rev-cost,v:score(plan.rev,plan.rest,r,oo),sig});
  }
  for(let k=1;k<=3;k++){
    for(const ex of [exN,exM]){
      if(!ex)continue;
      const pool=ex.slice(0,k).filter(Boolean);
      if(pool.length)addCard(pool.reduce((a,b)=>b.v>a.v?b:a));
    }
  }
  const shown=cards.sort((a,b)=>a.used.length-b.used.length||b.v-a.v);
  const bestV=Math.max(...shown.map(c=>c.v));
  html+=warns.map(w=>`<div class="warn">${w}</div>`).join('');
  const useCost=oo.cost>0||oo.tf>0;
  shown.forEach((c,i)=>{
    const unsold=c.plan.det.filter(d=>d.f.rest>0.0001).map(d=>`${nf(d.f.rest,d.f.rest%1?1:0)} SCU ${esc(CM[d.cid].n)}`);
    const rec=shown.length>1&&c.v===bestV;
    const pct=mx.rev>0?c.plan.rev/mx.rev*100:100;
    const meta=[`<b>Erlös ${nf(c.plan.rev)} aUEC</b> (${nf(pct,1)} % des Maximums)`,`<b>Strecke ${nf(c.r.d)} Gm</b>${o.start?' ab Startpunkt':''}`,`<b>Zeit ${fmtT(c.r.t)}</b> (Flug ${fmtT(c.r.t-M.dwell*c.order.length-M.tun*c.r.ch)} + Verkauf ${nf(M.dwell*c.order.length)} Min${c.r.ch>0?` + Sprungtunnel ${nf(M.tun*c.r.ch,M.tun%1?1:0)} Min`:''})`];
    if(oo.mode!=='net'||oo.cost>0||DM.some(v=>v>0))meta.push(`${nf(Math.round(c.net/(Math.max(c.r.t,1)/60)))} aUEC je Stunde`);
    if(useCost)meta.push(`Streckenkosten ${nf(c.cost)} aUEC`);
    if(o.q.tank)meta.push(`Treibstoff ca. ${nf(c.r.d*o.q.fuel+c.r.ch*o.tf,2)} SCU`);
    if(c.r.e)meta.push('Strecke teilweise geschätzt');
    html+=`<div class="card${rec?' best':''}"><div class="chead"><div class="ctitle">${c.used.length} Stopp${c.used.length>1?'s':''}${rec?' · Empfehlung':''}${i===0&&!rec?' · wenigste Stopps':''}</div>`+
      `<div class="total">${nf(useCost?c.net:c.plan.rev)} aUEC${useCost?' <span class="sloc">netto</span>':''}</div></div>`+
      `<div class="meta">${meta.join(' · ')}</div>`+
      rangeWarn(c,o)+
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
    # Gateway-Stationen: "Quellsystem>Zielsystem" -> Ortsindex, z. B. "Stanton>Pyro" = Pyro Gateway (Stanton)
    gateways = {}
    for r in con.execute("SELECT * FROM uex_terminals ORDER BY id"):
        to = uex.gateway_target(r)
        if to:
            gateways.setdefault(f"{r['star_system']}>{to}", place_idx[(r["star_system"], uex.place_name(r))])
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

    # Quantum Drives, Schiff -> Standard-Drive, Treibstoffpreis
    qd = [[r["class_name"], r["name"], r["size"], r["grade"] or "", r["class"] or "", r["fuel_scu_per_gm"],
           round(r["speed_mms"], 1), r["spool_s"], r["cooldown_s"]]
          for r in con.execute("SELECT * FROM quantum_drives ORDER BY size, speed_mms, name")]
    ships, seen = [], set()
    sql = ("SELECT v.name, v.qtank_scu, s.qd_class FROM vehicles v JOIN ship_qd s ON s.slug = v.slug "
           "JOIN quantum_drives q ON q.class_name = s.qd_class "
           "WHERE v.is_spaceship = 1 AND v.slug NOT LIKE '%-display' AND v.qtank_scu > 0 "
           "ORDER BY v.name, v.msrp_usd DESC")
    for r in con.execute(sql):
        if r["name"] not in seen:
            seen.add(r["name"])
            ships.append([r["name"], r["qtank_scu"], r["qd_class"]])
    row = con.execute("SELECT value FROM settings WHERE key='qfuel_price'").fetchone()
    try:
        qfp = float(row[0]) if row else 0.0
    except (TypeError, ValueError):
        qfp = 0.0
    qftxt = f"aktuell {qfp:,.0f} aUEC je SCU".replace(",", ".") if qfp else "Preis unbekannt, Näherungswert 1.760 aUEC je SCU"

    def js(x):
        return json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    html = (PAGE.replace("__TERMINALS__", js(terms)).replace("__PLACES__", js(places))
            .replace("__COMMODITIES__", js(coms)).replace("__PRICES__", js(prices)).replace("__DISTS__", js(dist)).replace("__GATEWAYS__", js(gateways))
            .replace("__QD__", js(qd)).replace("__SHIPS__", js(ships)).replace("__QFP__", js(qfp)).replace("__QFTXT__", qftxt)
            .replace("__UEXSTAND__", stand).replace("__DTXT__", dtxt)
            .replace("__STAND__", dt.datetime.now().strftime("%d.%m.%Y %H:%M")))
    import stale
    html = stale.inject(html, 12)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, target)
    return len(prices)
