"""ASHFALL 0.2 — persistent world coordinates and authenticated world-state API."""
import hashlib
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

WORLD_SIZE = 2048

def initialize_world(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_world_positions (
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      state_id INTEGER NOT NULL REFERENCES ashfall_states(id),
      x INTEGER NOT NULL CHECK(x BETWEEN 0 AND 2047),
      y INTEGER NOT NULL CHECK(y BETWEEN 0 AND 2047),
      UNIQUE(state_id,x,y))""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_positions ON ashfall_world_positions(state_id,x,y)")
    # Migrate all existing havens; do not alter their progress or identities.
    havens=db.execute("""SELECT h.id,h.state_id FROM ashfall_havens h
      LEFT JOIN ashfall_world_positions p ON p.haven_id=h.id WHERE p.haven_id IS NULL ORDER BY h.id""").fetchall()
    for h in havens:
        seed=int.from_bytes(hashlib.sha256(f'ashfall:{h["state_id"]}:{h["id"]}'.encode()).digest()[:8],"big")
        for attempt in range(WORLD_SIZE*WORLD_SIZE):
            x=100+(seed+attempt*53)%1848
            y=100+((seed//1848)+attempt*97)%1848
            if not db.execute("SELECT 1 FROM ashfall_world_positions WHERE state_id=? AND x=? AND y=?",(h["state_id"],x,y)).fetchone():
                db.execute("INSERT INTO ashfall_world_positions(haven_id,state_id,x,y) VALUES(?,?,?,?)",(h["id"],h["state_id"],x,y))
                break

def register_world(app,database,get_user):
    with database() as db:
        initialize_world(db)

    @app.get("/ashfall/play")
    async def world_page(request:Request):
        user=get_user(request.session.get("user_id"))
        if not user:return RedirectResponse("/login",status_code=303)
        with database() as db:
            exists=db.execute("SELECT 1 FROM ashfall_havens WHERE user_id=?",(user["id"],)).fetchone()
        if not exists:return RedirectResponse("/ashfall",status_code=303)
        path=Path(__file__).parent/"ashfall_world.html"
        return HTMLResponse(path.read_text(encoding="utf-8"))

    @app.get("/ashfall/api/world")
    async def world_data(request:Request,state_id:int=1):
        user=get_user(request.session.get("user_id"))
        if not user:raise HTTPException(401,"Sign in required")
        with database() as db:
            initialize_world(db)
            own=db.execute("""SELECT h.id,h.name,h.state_id,h.command_center_level,p.x,p.y
              FROM ashfall_havens h JOIN ashfall_world_positions p ON p.haven_id=h.id
              WHERE h.user_id=? AND h.state_id=?""",(user["id"],state_id)).fetchone()
            if not own:raise HTTPException(404,"Create your Haven in this state first")
            others=db.execute("""SELECT h.id,h.name,h.command_center_level,p.x,p.y FROM ashfall_havens h
              JOIN ashfall_world_positions p ON p.haven_id=h.id
              WHERE h.state_id=? AND h.id!=? ORDER BY h.id LIMIT 500""",(state_id,own["id"])).fetchall()
        return {"state_id":state_id,"world_size":WORLD_SIZE,"haven":dict(own),
                "players":[dict(row) for row in others],
                "note":"Only actual player Havens are returned as players. Wilderness points of interest are deterministic visual previews, not active encounters."}
