"""Userbot uchun minimalist web boshqaruv paneli.

Sozlamalarni (data/state_<acc>.json) brauzer orqali yoqib/o'chirish.
Ishga tushirish: venv/bin/python webpanel.py
Kirish: http://<server>:8080/?token=<PANEL_TOKEN>
"""
import json
import os

from aiohttp import web
from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))
DATA = os.path.join(BASE, "data")

TOKEN = os.getenv("PANEL_TOKEN", "")
PORT = int(os.getenv("PANEL_PORT", "8080"))

ACCOUNTS = [
    ("acc1", "@Shamsiyevshamsiddin"),
    ("acc2", "@shamsiyev_shamsiddin"),
    ("acc3", "@scarpiont"),
]
FEATURES = [
    ("autoreply", "Avto-javob"),
    ("autodraft", "Qoralama (shaxsiy)"),
    ("autoread", "Avto-o'qish"),
    ("autoai", "Yarim-avto taklif"),
]
FEAT_KEYS = {k for k, _ in FEATURES}
ACC_KEYS = {a for a, _ in ACCOUNTS}


def _sfile(acc):
    return os.path.join(DATA, f"state_{acc}.json")


def read_state(acc):
    try:
        with open(_sfile(acc), encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def write_state(acc, d):
    os.makedirs(DATA, exist_ok=True)
    tmp = _sfile(acc) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    os.replace(tmp, _sfile(acc))


def feature_on(d, feat):
    if feat == "autoread":
        k = d.get("autoread_kinds")
        if k is not None:
            return len(k) > 0
        return bool(d.get("autoread"))
    return bool(d.get(feat))


def set_feature(acc, feat, value):
    d = read_state(acc)
    if feat == "autoread":
        d["autoread"] = value
        d["autoread_kinds"] = ["group", "channel", "bot"] if value else []
    else:
        d[feat] = value
    write_state(acc, d)


def _ok(req):
    return bool(TOKEN) and req.query.get("token") == TOKEN


async def api_state(req):
    if not _ok(req):
        return web.json_response({"error": "token"}, status=403)
    out = {}
    for acc, _ in ACCOUNTS:
        d = read_state(acc)
        out[acc] = {f: feature_on(d, f) for f, _ in FEATURES}
    return web.json_response(out)


async def api_toggle(req):
    if not _ok(req):
        return web.json_response({"error": "token"}, status=403)
    try:
        body = await req.json()
    except Exception:  # noqa: BLE001
        return web.json_response({"error": "bad json"}, status=400)
    acc = body.get("account")
    feat = body.get("feature")
    val = bool(body.get("value"))
    if acc not in ACC_KEYS or feat not in FEAT_KEYS:
        return web.json_response({"error": "bad"}, status=400)
    set_feature(acc, feat, val)
    return web.json_response({"ok": True})


async def index(req):
    if not _ok(req):
        return web.Response(text="Token noto'g'ri yoki yo'q.", status=403)
    return web.Response(text=PAGE.replace("__TOKEN__", TOKEN), content_type="text/html")


PAGE = """<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Userbot</title>
<style>
  :root { --line:#ececec; --muted:#8a8a8a; --on:#111; }
  * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; }
  body {
    margin:0; background:#fff; color:#111;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    font-size:16px; line-height:1.4;
  }
  .wrap { max-width:520px; margin:0 auto; padding:40px 22px 80px; }
  h1 { font-size:22px; font-weight:600; margin:0 0 4px; letter-spacing:-.02em; }
  .sub { color:var(--muted); font-size:13px; margin-bottom:36px; }
  .acc { font-size:13px; font-weight:600; text-transform:uppercase;
         letter-spacing:.06em; color:var(--muted); margin:34px 0 4px; }
  .row { display:flex; align-items:center; justify-content:space-between;
         padding:15px 2px; border-bottom:1px solid var(--line); }
  .row .name { font-size:16px; }
  .sw { position:relative; width:46px; height:28px; flex:0 0 auto; }
  .sw input { opacity:0; width:0; height:0; }
  .sl { position:absolute; inset:0; background:#e4e4e4; border-radius:999px;
        transition:.22s; cursor:pointer; }
  .sl:before { content:""; position:absolute; width:22px; height:22px; left:3px; top:3px;
        background:#fff; border-radius:50%; transition:.22s;
        box-shadow:0 1px 3px rgba(0,0,0,.2); }
  input:checked + .sl { background:var(--on); }
  input:checked + .sl:before { transform:translateX(18px); }
  .foot { color:var(--muted); font-size:12px; margin-top:40px; text-align:center; }
  .toast { position:fixed; left:50%; bottom:26px; transform:translateX(-50%) translateY(20px);
    background:#111; color:#fff; padding:9px 16px; border-radius:999px; font-size:13px;
    opacity:0; transition:.25s; pointer-events:none; }
  .toast.show { opacity:1; transform:translateX(-50%) translateY(0); }
  @media (prefers-color-scheme: dark) {
    body { background:#fff; color:#111; }  /* foydalanuvchi oq fon so'radi */
  }
</style>
</head>
<body>
<div class="wrap">
  <h1>Userbot</h1>
  <div class="sub">Boshqaruv paneli</div>
  <div id="app">Yuklanmoqda…</div>
  <div class="foot">O'zgarishlar bir necha soniyada qo'llanadi.</div>
</div>
<div class="toast" id="toast"></div>
<script>
const TOKEN="__TOKEN__";
const FEATURES=[["autoreply","Avto-javob"],["autodraft","Qoralama (shaxsiy)"],["autoread","Avto-o'qish"],["autoai","Yarim-avto taklif"]];
const ACCOUNTS=[["acc1","@Shamsiyevshamsiddin"],["acc2","@shamsiyev_shamsiddin"],["acc3","@scarpiont"]];
const app=document.getElementById("app"), toast=document.getElementById("toast");
let T;
function showToast(t){toast.textContent=t;toast.classList.add("show");clearTimeout(T);T=setTimeout(()=>toast.classList.remove("show"),1400);}
async function load(){
  const r=await fetch("/api/state?token="+encodeURIComponent(TOKEN));
  if(!r.ok){app.textContent="Token noto'g'ri.";return;}
  const st=await r.json();
  app.innerHTML="";
  for(const [acc,uname] of ACCOUNTS){
    const h=document.createElement("div");h.className="acc";h.textContent=acc+" · "+uname;app.appendChild(h);
    for(const [f,label] of FEATURES){
      const row=document.createElement("div");row.className="row";
      const nm=document.createElement("div");nm.className="name";nm.textContent=label;
      const sw=document.createElement("label");sw.className="sw";
      const cb=document.createElement("input");cb.type="checkbox";cb.checked=!!(st[acc]&&st[acc][f]);
      const sl=document.createElement("span");sl.className="sl";
      cb.addEventListener("change",()=>toggle(acc,f,cb.checked,label));
      sw.appendChild(cb);sw.appendChild(sl);
      row.appendChild(nm);row.appendChild(sw);app.appendChild(row);
    }
  }
}
async function toggle(acc,feat,val,label){
  const r=await fetch("/api/toggle?token="+encodeURIComponent(TOKEN),{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({account:acc,feature:feat,value:val})});
  if(r.ok) showToast(label+(val?" yoqildi":" o'chirildi"));
  else showToast("Xato");
}
load();
</script>
</body>
</html>"""


def main():
    if not TOKEN:
        print("PANEL_TOKEN sozlanmagan (.env). Panel ishga tushmaydi.")
        raise SystemExit(1)
    app = web.Application()
    app.add_routes([
        web.get("/", index),
        web.get("/api/state", api_state),
        web.post("/api/toggle", api_toggle),
    ])
    print(f"Web panel: http://0.0.0.0:{PORT}/?token=***")
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)


if __name__ == "__main__":
    main()
