"""Warnleiste fuer die erzeugten Seiten: erscheint, wenn die Seite nicht mehr regelmaessig neu geschrieben wird."""
import time

_SNIPPET = """<script>
(function(){
  var built=__BUILT__*1000,limit=__HOURS__*3600000,age=Date.now()-built;
  if(!(age>limit))return;
  var h=Math.floor(age/3600000),t=h>=48?Math.floor(h/24)+' Tagen':h+' Stunden';
  var d=document.createElement('div');
  d.setAttribute('role','alert');
  d.style.cssText='background:#fdecea;color:#7a1c14;border:1px solid #d9534f;border-radius:6px;padding:10px 14px;margin:10px 0;font-weight:600';
  d.textContent='Achtung: Diese Seite wurde zuletzt vor '+t+' erzeugt (erwartet: spätestens alle __HOURS__ Stunden). Der Updater scheint nicht zu laufen. Bitte im Container Manager unter sc-updater → Protokoll nachsehen.';
  document.body.insertBefore(d,document.body.firstChild);
})();
</script>
"""


def inject(html, max_hours):
    """Haengt die Warnleiste vor </body>; max_hours = Alter, ab dem gewarnt wird."""
    s = _SNIPPET.replace("__BUILT__", str(int(time.time()))).replace("__HOURS__", str(max_hours))
    if "</body>" in html:
        return html.replace("</body>", s + "</body>", 1)
    return html + s
