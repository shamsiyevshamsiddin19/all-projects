"""Umumiy dizayn — subtitr master admin bilan bir xil uslub (OpenAI monoxrom).

Uslub aynan master paneldan olingan; kino paneli xuddi shu ko'rinishda bo'ladi."""

_STYLE = """
:root{--bg:#fff;--subtle:#f7f7f8;--border:#e5e5e5;--text:#0d0d0d;--muted:#6e6e80;
  --accent:#0d0d0d;--ok:#10a37f;--bad:#ef4444;--warn:#d97706}
*{box-sizing:border-box}
body{margin:0;background:var(--subtle);color:var(--text);
  font:15px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:inherit}
.navtoggle{display:none}
.layout{display:flex;min-height:100vh}
.sidebar{width:230px;flex:0 0 230px;background:var(--bg);
  border-right:1px solid var(--border);padding:18px 14px;position:fixed;
  top:0;left:0;bottom:0;overflow-y:auto;z-index:30;transition:transform .2s ease}
.brand{font-weight:600;font-size:16px;padding:6px 10px 16px;display:flex;
  align-items:center;gap:9px}
.brand .dot{width:22px;height:22px;border-radius:7px;background:var(--accent);
  color:#fff;display:inline-flex;align-items:center;justify-content:center;
  font-size:13px}
.nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:8px;
  color:var(--muted);text-decoration:none;font-size:14px;margin-bottom:2px}
.nav a:hover{background:var(--subtle);color:var(--text)}
.nav a.active{background:var(--subtle);color:var(--text);font-weight:500}
.nav svg{width:18px;height:18px;flex:0 0 18px}
.content{margin-left:230px;flex:1;padding:26px 28px 64px;min-width:0;width:100%}
.topbar{display:none}
.overlay{display:none}
.hamburger{display:none}
.pagehead{display:flex;align-items:baseline;justify-content:space-between;
  gap:10px;margin-bottom:22px;flex-wrap:wrap}
.pagehead h1{font-size:21px;font-weight:600;margin:0}
.pagehead .sub{color:var(--muted);font-size:13px}
.btn{color:var(--muted);text-decoration:none;font-size:13px;border:1px solid var(--border);
  padding:6px 12px;border-radius:8px;background:var(--bg);cursor:pointer;font:inherit}
.btn:hover{color:var(--text)}
.btn.solid{background:var(--accent);color:#fff;border-color:var(--accent)}
.btn.danger{color:var(--bad);border-color:#f5c2c2;background:var(--bg)}
.btn.ok{color:var(--ok);border-color:#bde9da;background:var(--bg)}
.statbar{display:flex;background:var(--bg);border:1px solid var(--border);
  border-radius:12px;overflow-x:auto;margin-bottom:28px}
.stat{flex:1 0 auto;min-width:122px;padding:15px 18px;
  border-right:1px solid var(--border)}
.stat:last-child{border-right:none}
.stat .label{color:var(--muted);font-size:13px;margin-bottom:5px;white-space:nowrap}
.stat .num{font-size:24px;font-weight:600;letter-spacing:-.5px}
.stat .note{color:var(--muted);font-size:12px;margin-top:3px;white-space:nowrap}
h2{font-size:15px;font-weight:600;margin:0 0 12px}
.panel{background:var(--bg);border:1px solid var(--border);border-radius:12px;
  overflow:hidden;margin-bottom:26px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:520px}
th,td{text-align:left;padding:11px 16px;border-bottom:1px solid var(--border);
  white-space:nowrap}
th{color:var(--muted);font-weight:500;font-size:12px;text-transform:uppercase;
  letter-spacing:.04em}
tr:last-child td{border-bottom:none}
td.muted,.muted{color:var(--muted)}
.badge{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px;
  border:1px solid var(--border);white-space:nowrap}
.badge.ok{color:var(--ok);border-color:#bde9da}
.badge.bad{color:var(--bad);border-color:#f5c2c2}
.badge.warn{color:var(--warn);border-color:#f0d6a8}
.badge.muted{color:var(--muted)}
.badge.accentbadge{color:#fff;background:var(--accent);border-color:var(--accent)}
.empty{padding:22px 16px;color:var(--muted);font-size:14px}
.note{color:var(--muted);font-size:12px;margin:6px 2px 24px}
.chart{display:flex;align-items:flex-end;gap:5px;padding:18px 16px 12px}
.bar{flex:1;display:flex;flex-direction:column;align-items:center;gap:5px;min-width:0}
.bar .val{font-size:10px;color:var(--muted);height:13px}
.bar .barinner{width:100%;height:140px;display:flex;align-items:flex-end;
  justify-content:center}
.bar .fill{width:100%;max-width:30px;background:var(--accent);
  border-radius:5px 5px 0 0;min-height:2px}
.bar .lbl{font-size:10px;color:var(--muted)}
.search{display:flex;gap:8px;margin-bottom:18px}
.search input{flex:1;max-width:320px;padding:8px 12px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text)}
.search button{padding:8px 16px;border:1px solid var(--accent);background:var(--accent);
  color:#fff;border-radius:8px;font-size:14px;cursor:pointer}
.actbar{display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end;padding:16px}
.field{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--muted)}
.field select,.field input,.field textarea{padding:8px 10px;border:1px solid var(--border);
  border-radius:8px;font-size:14px;background:var(--bg);color:var(--text);min-width:120px}
form.inline{display:flex;gap:8px;align-items:flex-end;margin:0}
.pager{display:flex;gap:6px;margin:8px 0 24px;flex-wrap:wrap}
.pager a{font-size:13px;padding:6px 12px;border:1px solid var(--border);
  border-radius:8px;text-decoration:none;color:var(--muted);background:var(--bg)}
.pager a.on{color:var(--text);border-color:var(--accent)}
.foot{color:var(--muted);font-size:12px;text-align:center;margin-top:8px}
@media(max-width:820px){
  .sidebar{transform:translateX(-100%)}
  #navtoggle:checked ~ .sidebar{transform:translateX(0)}
  #navtoggle:checked ~ .overlay{display:block;position:fixed;inset:0;
    background:rgba(0,0,0,.35);z-index:25}
  .content{margin-left:0;padding:0 16px 56px}
  .topbar{display:flex;align-items:center;gap:12px;position:sticky;top:0;z-index:20;
    margin:0 -16px 18px;padding:13px 16px;background:var(--bg);
    border-bottom:1px solid var(--border)}
  .topbar .ttl{font-weight:600;font-size:16px}
  .hamburger{display:inline-flex;align-items:center;justify-content:center;
    width:38px;height:38px;border:1px solid var(--border);border-radius:9px;
    cursor:pointer;color:var(--text);font-size:18px;background:var(--bg)}
  .statbar{display:flex;overflow:hidden}
  .stat{flex:1 1 0;min-width:0;padding:8px 4px;text-align:center}
  .stat .label{font-size:8.5px;line-height:1.15;white-space:normal;
    overflow-wrap:anywhere;margin-bottom:2px}
  .stat .num{font-size:15px}
  .stat .note{font-size:8px;white-space:normal;line-height:1.15}
  .scroll{overflow-x:auto}
}
"""


def icon(name: str) -> str:
    paths = {
        "dash": "<rect x='3' y='3' width='7' height='7' rx='1'/><rect x='14' y='3' "
                "width='7' height='7' rx='1'/><rect x='3' y='14' width='7' height='7' "
                "rx='1'/><rect x='14' y='14' width='7' height='7' rx='1'/>",
        "movie": "<rect x='2' y='2' width='20' height='20' rx='2'/><path d='M7 2v20'/>"
                 "<path d='M17 2v20'/><path d='M2 12h20'/><path d='M2 7h5'/><path d='M2 17h5'/>"
                 "<path d='M17 17h5'/><path d='M17 7h5'/>",
        "series": "<rect x='2' y='7' width='20' height='15' rx='2'/>"
                  "<polyline points='17 2 12 7 7 2'/>",
        "channel": "<path d='M4 11a9 9 0 0 1 9 9'/><path d='M4 4a16 16 0 0 1 16 16'/>"
                   "<circle cx='5' cy='19' r='1'/>",
        "social": "<circle cx='18' cy='5' r='3'/><circle cx='6' cy='12' r='3'/>"
                  "<circle cx='18' cy='19' r='3'/><line x1='8.6' y1='13.5' x2='15.4' y2='17.5'/>"
                  "<line x1='15.4' y1='6.5' x2='8.6' y2='10.5'/>",
        "settings": "<circle cx='12' cy='12' r='3'/><path d='M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z'/>",
        "broadcast": "<line x1='22' y1='2' x2='11' y2='13'/><polygon points='22 2 15 22 11 13 2 9 22 2'/>",
    }
    return (
        "<svg viewBox='0 0 24 24' fill='none' stroke='currentColor' "
        "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>"
        + paths.get(name, "") + "</svg>"
    )


def bot_switcher(current_prefix: str = "") -> str:
    """Bot tanlagich — master (subtitr) panel bilan AYNAN bir xil chiroyli dropdown.
    Kino paneli ochilganda 'Kino bot' faol bo'ladi."""
    def sv(inner):
        return ("<svg viewBox='0 0 24 24' width='20' height='20' fill='none' stroke='currentColor' "
                "stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'>" + inner + "</svg>")
    film = sv("<rect x='2' y='4' width='20' height='16' rx='2'/><path d='M2 9h20M2 15h20M7 4v16M17 4v16'/>")
    book = sv("<path d='M4 19.5A2.5 2.5 0 0 1 6.5 17H20'/>"
              "<path d='M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z'/>")
    pencil = sv("<path d='M12 20h9'/><path d='M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z'/>")
    cap = sv("<path d='M22 10 12 5 2 10l10 5 10-5Z'/>"
             "<path d='M6 12v5c0 1 2.7 2.5 6 2.5s6-1.5 6-2.5v-5'/>")
    quiz = sv("<circle cx='12' cy='12' r='10'/>"
              "<path d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'/><line x1='12' y1='17' x2='12.01' y2='17'/>")
    cart = sv("<circle cx='9' cy='21' r='1'/><circle cx='20' cy='21' r='1'/>"
              "<path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6'/>")
    chart = sv("<line x1='18' y1='20' x2='18' y2='10'/><line x1='12' y1='20' x2='12' y2='4'/><line x1='6' y1='20' x2='6' y2='14'/>")
    clap = sv("<path d='M20.2 6 3 11l-.9-2.4c-.3-.8.1-1.7.9-2l12.2-4.5c.8-.3 1.7.1 2 .9Z'/>"
              "<path d='M2.1 8.6 21 4M5.5 3.2 7 7M11 1.5 12.5 5.4M16.5 0 18 3.8'/>"
              "<rect x='2' y='11' width='20' height='11' rx='2'/>")
    bots = [
        ("/admin", film, "Subtitr bot", False),
        ("/sessiya/admin", book, "Sessiya bot", False),
        ("/mustaqil/admin", pencil, "Mustaqil bot", False),
        ("/tatulms/admin", cap, "TATU LMS bot", False),
        ("/quiz/admin", quiz, "Quiz bot", False),
        ("/wstore/admin", cart, "wstore market", False),
        ("/site/admin", chart, "Portfolio", False),
        ("/kino/admin", clap, "Kino bot", True),
    ]
    cur = next((b for b in bots if b[3]), bots[0])
    opts = "".join("<a class='botopt%s' href='%s'>%s<span class='botnm'>%s</span></a>" % (
        " active" if act else "", url, svg, label) for url, svg, label, act in bots)
    chev = ("<svg class='botchev' viewBox='0 0 24 24' fill='none' stroke='currentColor' "
            "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'>"
            "<polyline points='6 9 12 15 18 9'/></svg>")
    return (
        "<style>.botdd{position:relative;flex:1;min-width:0}"
        ".botcur{list-style:none;display:flex;align-items:center;gap:9px;padding:9px 11px;"
        "border:1px solid #e5e5e5;border-radius:10px;background:#fff;cursor:pointer;color:#0d0d0d;"
        "font-size:13.5px;font-weight:600;user-select:none}"
        ".botcur::-webkit-details-marker{display:none}.botcur:hover{background:#f7f7f8}"
        ".botcur svg,.botopt svg{width:18px;height:18px;flex:0 0 18px}"
        ".botnm{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
        ".botcur .botchev{width:15px;height:15px;flex:0 0 15px;color:#6e6e80;transition:transform .2s}"
        ".botdd[open] .botchev{transform:rotate(180deg)}"
        ".botmenu{position:absolute;top:calc(100% + 6px);left:0;right:0;z-index:60;background:#fff;"
        "border:1px solid #e5e5e5;border-radius:12px;box-shadow:0 14px 34px rgba(0,0,0,.13);padding:6px}"
        ".botopt{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:8px;"
        "color:#6e6e80;text-decoration:none;font-size:13.5px;font-weight:500;margin-bottom:2px}"
        ".botopt:last-child{margin-bottom:0}.botopt:hover{background:#f7f7f8;color:#0d0d0d}"
        ".botopt.active{background:#0d0d0d;color:#fff}</style>"
        "<details class='botdd'><summary class='botcur'>" + cur[1] +
        "<span class='botnm'>" + cur[2] + "</span>" + chev + "</summary>"
        "<div class='botmenu'>" + opts + "</div></details>"
        "<script>document.addEventListener('click',function(e){"
        "document.querySelectorAll('details.botdd[open]').forEach(function(d){"
        "if(!d.contains(e.target))d.removeAttribute('open');});});</script>"
    )
