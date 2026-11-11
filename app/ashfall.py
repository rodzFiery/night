"""ASHFALL World 01: persistent state membership and canonical stat foundation."""
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

POWER = ["Chief Battle Power","Troop Battle Power","Building Battle Power","Tech Battle Power","Gear Battle Power","Hero Gear Power","Hero Power","Aircraft Power","Behemoth Power"]
MILITARY = ["March Slots","March Capacity","Training Capacity","Training Speed","March Speed","Troop Attack","Troop Defense","Troop Lethality","Troop Health","Troop Load"]
COMBAT = ["Hero Final Damage","Hero Final Damage Taken Reduction","Combat Morale","Extra Damage from Combat Morale","Extra Damage Taken Reduction from Combat Morale"]
DEFENSE = ["Settlement Army Attack","Settlement Army Defense","Settlement Troop Lethality","Settlement Troop Health"]
RESOURCES = [f"{resource} {effect}" for resource in ("Food","Wood","Metal","Gas") for effect in ("Production","Gathering Speed")]
DEVELOPMENT = ["Construction Speed","Research Speed","Troop Load","Infected March Speed","Stamina Recovery","Trade Load","Trade Fee"]
RECORDS = ["Battles Won","Battles Lost","Attacks Won","Attacks Lost","Defenses Won","Win Rate","Recon Count","Killed","Lost"]
CLASSES = [f"{unit} {attribute}" for unit in ("Infantry","Rider","Hunter") for attribute in ("Attack","Defense","Lethality","Health")]
CATEGORIES = {"Battle Power":POWER,"Military":MILITARY,"Troop Classes":CLASSES,"Combat":COMBAT,"Settlement Defense":DEFENSE,"Resources":RESOURCES,"Development":DEVELOPMENT,"Combat Records":RECORDS}
# Canonical keys eliminate duplicate Troop Load across categories.
def key_for(label):
    return label.lower().replace(" ","_")

def initialize(connection):
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_states (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, status TEXT NOT NULL DEFAULT 'open',
      created_at TEXT NOT NULL)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_havens (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      state_id INTEGER NOT NULL REFERENCES ashfall_states(id),
      name TEXT NOT NULL, command_center_level INTEGER NOT NULL DEFAULT 1,
      created_at TEXT NOT NULL, UNIQUE(user_id,state_id))""")
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_stat_definitions (
      stat_key TEXT PRIMARY KEY, display_name TEXT NOT NULL, category TEXT NOT NULL,
      value_type TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1)""")
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_modifier_definitions (
      id TEXT PRIMARY KEY, stat_key TEXT NOT NULL REFERENCES ashfall_stat_definitions(stat_key),
      source_type TEXT NOT NULL, operation TEXT NOT NULL,
      amount REAL NOT NULL, stacking_group TEXT NOT NULL DEFAULT 'default')""")
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_active_modifiers (
      id INTEGER PRIMARY KEY AUTOINCREMENT, haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      modifier_id TEXT NOT NULL REFERENCES ashfall_modifier_definitions(id),
      expires_at TEXT, UNIQUE(haven_id,modifier_id))""")
    connection.execute("""CREATE TABLE IF NOT EXISTS ashfall_stat_ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT, haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      stat_key TEXT NOT NULL, delta INTEGER NOT NULL, event_key TEXT NOT NULL,
      created_at TEXT NOT NULL, UNIQUE(haven_id,event_key,stat_key))""")
    connection.execute("INSERT OR IGNORE INTO ashfall_states(id,name,created_at) VALUES (1,'State 001',?)",(datetime.now(timezone.utc).isoformat(),))
    for category, labels in CATEGORIES.items():
        for label in labels:
            key=key_for(label)
            value_type="counter" if category=="Combat Records" else "rating" if category=="Battle Power" else "modifier"
            connection.execute("""INSERT OR IGNORE INTO ashfall_stat_definitions
              (stat_key,display_name,category,value_type) VALUES (?,?,?,?)""",(key,label,category,value_type))

def resolve_modifier(base, modifiers):
    """Pure stat resolver. All modifiers must be trusted server-side definitions."""
    flat=sum(m["amount"] for m in modifiers if m["operation"]=="add_flat")
    percent=sum(m["amount"] for m in modifiers if m["operation"]=="add_percent")
    return max(0.0,(base+flat)*(1.0+percent))

def register_ashfall(app, database, get_user, valid_csrf):
    with database() as db:
        initialize(db)

    def context(request):
        user=get_user(request.session.get("user_id"))
        with database() as db:
            states=[dict(r) for r in db.execute("SELECT id,name,status FROM ashfall_states ORDER BY id")]
            havens=[dict(r) for r in db.execute("SELECT h.*,s.name AS state_name FROM ashfall_havens h JOIN ashfall_states s ON s.id=h.state_id WHERE h.user_id=?",(user["id"],))] if user else []
            count=db.execute("SELECT COUNT(*) FROM ashfall_stat_definitions").fetchone()[0]
        return user,states,havens,count

    @app.get("/ashfall")
    async def ashfall_portal(request:Request):
        user,states,havens,count=context(request)
        csrf=request.session.get("csrf_token","")
        if not csrf:
            import secrets
            csrf=secrets.token_urlsafe(32)
            request.session["csrf_token"]=csrf
        options="".join(f'<option value="{s["id"]}">{s["name"]}</option>' for s in states if s["status"]=="open")
        havens_html="".join(f'<article class="tile"><small>{h["state_name"]}</small><h3>{h["name"]}</h3><p>Command Center · Level {h["command_center_level"]}</p></article>' for h in havens)
        join=f'<form method="post" action="/ashfall/join"><input type="hidden" name="csrf_token" value="{csrf}"><label>Choose your state <select name="state_id">{options}</select></label><button type="submit">Establish my Haven →</button></form>' if user else '<a class="button" href="/login">Sign in with NEXORA →</a>'
        if havens:
            join += '<p class="muted">One Haven per player per state. Your existing Haven is preserved.</p>'
        cards="".join(f'<div class="tile"><small>{category.upper()}</small><strong>{len(labels)} entries</strong></div>' for category,labels in CATEGORIES.items())
        html="""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ASHFALL — NEXORA World 01</title><style>
        :root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b0d10;color:#f4f0e9;font-family:system-ui,Segoe UI,sans-serif}
        .hero{min-height:390px;padding:32px max(24px,calc((100vw - 1100px)/2));background:radial-gradient(ellipse at 80% 35%,#7a3827 0%,transparent 50%),linear-gradient(140deg,#20232a,#0b0d10 70%);border-bottom:1px solid #5a3d32}
        a{color:#efb08b}nav{display:flex;justify-content:space-between;gap:15px}nav a{text-decoration:none;font-size:13px;letter-spacing:2px}h1{font-size:clamp(68px,13vw,160px);letter-spacing:-.09em;line-height:.9;margin:80px 0 20px;font-weight:900}h1 span{color:#e38b60}.tag{letter-spacing:3px;font-size:12px;color:#edab88}p{color:#bdb6ae;line-height:1.7;max-width:690px}
        main{max-width:1100px;margin:auto;padding:40px 24px 100px}h2{font-size:30px;margin-top:40px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.tile{padding:22px;border:1px solid #423630;background:linear-gradient(145deg,#23201f,#121417);border-radius:12px}.tile small{display:block;color:#d58f69;letter-spacing:2px;margin-bottom:12px}.tile strong{font-size:23px}button,.button{display:inline-block;border:0;border-radius:8px;background:#e18c62;color:#18110d;padding:14px 22px;font-weight:800;cursor:pointer;text-decoration:none}select{background:#191b1e;color:white;border:1px solid #685044;padding:13px;margin:10px}form{padding:20px;border:1px solid #45332a;border-radius:12px}.muted{font-size:13px}
        </style></head><body><header class="hero"><nav><a href="/">NEXORA / WORLD 01</a><a href="/dashboard">PLAYER HUB ↗</a></nav><div class="tag" style="margin-top:40px">PERSISTENT SURVIVAL STRATEGY · FOUNDATION BUILD</div><h1>ASH<span>FALL</span></h1><p>Civilization collapsed. Humanity must rebuild. Surviving isn't enough. Establish a Haven, build powerful territories and compete for dominance.</p></header><main><div class="tag">WORLD 01 / FIRST ARRIVAL</div><h2>Enter the wasteland</h2>__JOIN__<h2>Your Havens</h2><div class="grid">__HAVENS__</div><h2>Systems under construction</h2><p>The stat registry and state membership are real and persistent. Resource production, battles, troops, research and their modifiers are not yet active. No fabricated power scores.</p><div class="grid">__CARDS__</div><p class="muted">__COUNT__ unique canonical stat definitions. Independent states; shared NEXORA identity. Foundation 0.1.</p></main></body></html>"""
        from fastapi.responses import HTMLResponse
        return HTMLResponse(html.replace("__JOIN__",join).replace("__HAVENS__",havens_html or '<p>No Haven established yet.</p>').replace("__CARDS__",cards).replace("__COUNT__",str(count)))

    @app.post("/ashfall/join")
    async def ashfall_join(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:return RedirectResponse("/login",status_code=303)
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(status_code=400,detail="Security check expired. Reload and try again.")
        try:state_id=int(form.get("state_id","0"))
        except (TypeError,ValueError):raise HTTPException(status_code=400,detail="Invalid state.")
        with database() as db:
            state=db.execute("SELECT id FROM ashfall_states WHERE id=? AND status='open'",(state_id,)).fetchone()
            if not state:raise HTTPException(status_code=404,detail="State unavailable.")
            db.execute("""INSERT OR IGNORE INTO ashfall_havens(user_id,state_id,name,created_at)
              VALUES(?,?,?,?)""",(user["id"],state_id,user["username"]+"'s Haven",datetime.now(timezone.utc).isoformat()))
        return RedirectResponse("/ashfall",status_code=303)
