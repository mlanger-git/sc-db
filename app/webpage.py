"""Erzeugt die statische Seite SC_Schiffspreise.html im Stil der Star-Citizen-Seiten."""
import json
import os
import datetime as dt

PAGE = r'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SC Schiffspreise · Star Citizen</title>
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@600;700&family=Exo+2:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background:#f5f7fa; color:#1a2030; font-family:'Exo 2',sans-serif; padding:28px 28px 48px; max-width:1400px; }
  .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:22px; padding-bottom:16px; border-bottom:1px solid #d8e2ec; }
  .back-btn { display:inline-flex; gap:6px; font-size:.76rem; font-weight:600; color:#4a5a70; text-decoration:none; padding:5px 12px; border:1px solid #d0d8e4; border-radius:7px; background:#fff; }
  .back-btn:hover { background:#e8eef5; color:#1a2030; }
  h1 { font-family:'Rajdhani',sans-serif; font-size:1.5rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:3px; }
  .subtitle { font-size:.72rem; color:#8090a8; letter-spacing:.08em; text-transform:uppercase; margin-bottom:22px; }
  .panel { background:#fff; border:1px solid #d0d8e4; border-radius:12px; padding:16px 20px; margin-bottom:18px; box-shadow:0 1px 4px rgba(0,0,0,.05); display:flex; flex-wrap:wrap; gap:14px; align-items:end; }
  .panel label { display:block; font-family:'Rajdhani',sans-serif; font-size:.68rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; color:#6080a0; margin-bottom:5px; }
  .panel input[type=text], .panel select { font-family:'Exo 2',sans-serif; font-size:.85rem; color:#1a2030; background:#f4f7fa; border:1px solid #c8d4e4; border-radius:8px; padding:7px 12px; min-width:170px; }
  .chk { display:flex; align-items:center; gap:6px; font-size:.82rem; padding-bottom:7px; cursor:pointer; }
  .count { font-family:'Rajdhani',sans-serif; font-size:.8rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#6080a0; margin-bottom:10px; }
  .count b { color:#1a2030; font-size:1rem; }
  .wrap { overflow-x:auto; background:#fff; border:1px solid #d0d8e4; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,.05); }
  table { border-collapse:collapse; width:100%; font-size:.8rem; }
  th { position:sticky; top:0; background:#1a2030; color:#fff; font-family:'Rajdhani',sans-serif; letter-spacing:.06em; text-transform:uppercase; font-size:.72rem; padding:9px 8px; text-align:left; cursor:pointer; white-space:normal; line-height:1.25; vertical-align:bottom; min-width:64px; max-width:96px; }
  th.sorted::after { content:' ▲'; } th.sorted.desc::after { content:' ▼'; }
  td { padding:7px 10px; border-top:1px solid #edf1f6; vertical-align:top; }
  td.c { text-align:center; }
  table.hide-shops .shop { display:none; }
  td.n { text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap; }
  tr:hover td { background:#f4f7fa; }
  tr.concept td { background:#eceff3; color:#6b7280; }
  .footer { margin-top:20px; font-size:.62rem; color:#a0b0c0; letter-spacing:.07em; text-transform:uppercase; border-top:1px solid #e0e8f0; padding-top:10px; line-height:1.7; }
</style>
</head>
<body>
<div class="topbar"><a href="./" class="back-btn">← Star Citizen</a></div>
<h1>SC Schiffspreise</h1>
<div class="subtitle">Ingame-Preise (aUEC) und Echtgeld-Preise (EUR inkl. MwSt.) · Stand __STAND__</div>

<div class="panel">
  <div><label>Suche</label><input type="text" id="q" placeholder="Schiff oder Hersteller"></div>
  <div><label>Hersteller</label><select id="fh"><option value="">Alle</option></select></div>
  <div><label>Typ</label><select id="ft"><option value="">Alle</option></select></div>
  <div><label>Kategorie</label><select id="fk"><option value="">Alle</option></select></div>
  <div><label>Sub-Kategorie</label><select id="fr"><option value="">Alle</option></select></div>
  <div><label>Größe</label><select id="fg"><option value="">Alle</option></select></div>
  <div><label>Händler</label><select id="fs"><option value="">Alle</option></select></div>
  <div><label>Status</label><select id="fz"><option value="">Alle</option><option value="k">Nur Konzept / nicht geprüft</option><option value="n">Ohne Konzept</option></select></div>
  <label class="chk"><input type="checkbox" id="fi"> nur ingame kaufbar</label>
  <label class="chk"><input type="checkbox" id="fv"> Händler-Spalten anzeigen</label>
</div>
<div class="count"><b id="cnt">0</b> Einträge</div>
<div class="wrap"><table id="tbl" class="hide-shops">
<thead><tr id="head"></tr></thead><tbody id="body"></tbody></table></div>
<div class="footer">Quellen: Star Citizen Wiki (aUEC-Preise, Händler), Star Citizen Wiki API (USD-Preise, Rollen), EZB-Referenzkurs __KURS__ USD je EUR (__KURSTAG__), MwSt. __MWST__.<br>
Grau hinterlegt: Schiff noch im Konzept bzw. Status nicht geprüft (nicht in der API; USD-Preis evtl. veraltet). Automatisch aktualisiert; Daten ohne Gewähr.</div>

<script>
const DATA = __DATA__;
const SHOPS = [["Astro Armada","Astro Armada (Area18)"],["Crusader Showroom","Crusader Showroom (Orison)"],["New Deal","New Deal (Lorville)"],["Teach's","Teach's (Levski)"],["Buy & Fly","Buy & Fly (Ruin Station)"]];
DATA.forEach(r=>{const h=(r.haendler||'').split(', ');SHOPS.forEach(([k],i)=>{r['shop'+i]=h.includes(k)?'x':'';});});
const COLS = [["hersteller","Hersteller"],["kuerzel","Kürzel"],["schiff","Name"],["preis_auec","Ingame-Preis (aUEC)","n"],["preis_usd","Echtgeld","n"],
  ["preis_eur_inkl_mwst","Echtgeld (inkl. MwSt.)","n"],["auec_pro_eur","aUEC pro EUR","n"],
  ...SHOPS.map((s,i)=>["shop"+i,s[1],"c shop"]),
  ["ingame_kaufbar","Ingame kaufbar?","c"],["status","Status"],["typ","Typ"],["kategorie","Kategorie"],["subkategorie","Sub-Kategorie"],["groesse","Größe"],["anmerkung","Anmerkung"]];
let sortKey="hersteller", desc=false;
const $=id=>document.getElementById(id);
function fill(sel,key){[...new Set(DATA.map(r=>r[key]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'de')).forEach(v=>{const o=document.createElement('option');o.value=o.textContent=v;$(sel).appendChild(o);});}
fill('fh','hersteller');SHOPS.forEach(([k])=>{const o=document.createElement('option');o.value=o.textContent=k;$('fs').appendChild(o);});fill('ft','typ');fill('fk','kategorie');fill('fr','subkategorie');fill('fg','groesse');
$('head').innerHTML=COLS.map(c=>`<th data-k="${c[0]}" class="${(c[2]||'').replace(/\b[nc]\b/,'').trim()}">${c[1]}</th>`).join('');
$('head').onclick=e=>{const k=e.target.dataset.k;if(!k)return;desc=(sortKey===k)?!desc:false;sortKey=k;render();};
['q','fh','ft','fk','fr','fg','fs','fz','fi'].forEach(i=>$(i).addEventListener('input',render));
$('fv').addEventListener('input',()=>$('tbl').classList.toggle('hide-shops',!$('fv').checked));
const fmt=(v,k)=>{if(v==null||v==='')return '';if(typeof v==='number'){const d=(k==='preis_eur_inkl_mwst'||k==='preis_usd')?2:0;let s=v.toLocaleString('de-DE',{minimumFractionDigits:d,maximumFractionDigits:d});if(k==='preis_usd')s+=' $';if(k==='preis_eur_inkl_mwst')s+=' €';return s;}return String(v).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));};
function render(){
  const q=$('q').value.toLowerCase();
  let rows=DATA.filter(r=>(!q||(r.schiff+' '+r.hersteller).toLowerCase().includes(q))&&(!$('fh').value||r.hersteller===$('fh').value)
    &&(!$('ft').value||r.typ===$('ft').value)&&(!$('fk').value||r.kategorie===$('fk').value)&&(!$('fr').value||r.subkategorie===$('fr').value)&&(!$('fg').value||r.groesse===$('fg').value)
    &&(!$('fs').value||(r.haendler||'').split(', ').includes($('fs').value))
    &&(!$('fz').value||($('fz').value==='k')===!!r.konzept)
    &&(!$('fi').checked||r.ingame_kaufbar==='Ja'));
  rows.sort((a,b)=>{const x=a[sortKey],y=b[sortKey];if(x==null||x==='')return 1;if(y==null||y==='')return -1;
    const c=(typeof x==='number'&&typeof y==='number')?x-y:String(x).localeCompare(String(y),'de');return desc?-c:c;});
  $('cnt').textContent=rows.length;
  $('body').innerHTML=rows.map(r=>`<tr class="${r.konzept?'concept':''}">`+COLS.map(c=>`<td class="${c[2]||''}">${fmt(r[c[0]],c[0])}</td>`).join('')+'</tr>').join('');
  [...$('head').children].forEach(th=>{th.classList.toggle('sorted',th.dataset.k===sortKey);th.classList.toggle('desc',th.dataset.k===sortKey&&desc);});
}
render();
</script>
</body>
</html>
'''


def build(con, target):
    cur = con.execute("SELECT * FROM ship_prices ORDER BY lower(hersteller), lower(schiff)")
    cols = [d[0] for d in cur.description]
    rows = []
    for r in cur:
        d = dict(zip(cols, r))
        d["konzept"] = bool(d.get("konzept"))
        d["anmerkung"] = ""
        if d["konzept"]:
            d["status"] = "Concept"
        rows.append(d)
    fx = con.execute("SELECT day, usd_per_eur FROM fx ORDER BY day DESC LIMIT 1").fetchone()
    vat = con.execute("SELECT value FROM settings WHERE key='vat_rate'").fetchone()
    html = (PAGE.replace("__DATA__", json.dumps(rows, ensure_ascii=False).replace("</", "<\\/"))
            .replace("__STAND__", dt.datetime.now().strftime("%d.%m.%Y %H:%M"))
            .replace("__KURS__", str(fx[1]) if fx else "?")
            .replace("__KURSTAG__", str(fx[0]) if fx else "?")
            .replace("__MWST__", f"{float(vat[0]) * 100:.0f} %" if vat else "19 %"))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    os.replace(tmp, target)
    return len(rows)
