"""ASHFALL 0.2 — persistent world coordinates and authenticated world-state API."""
import hashlib
from pathlib import Path
from fastapi import HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

WORLD_SIZE = 2048


SECTOR_SIZE = 128
BIOMES = ("Ash Wastes", "Ironwood", "Glass Barrens", "Frostline", "Broken Lowlands", "Ember Fields")
RESOURCE_FOCUS = ("food", "wood", "metal", "gas")

def sector_profile(state_id, sector_x, sector_y):
    """Stable regional intelligence; informational, not a harvestable encounter."""
    if not (0 <= sector_x < WORLD_SIZE // SECTOR_SIZE and
            0 <= sector_y < WORLD_SIZE // SECTOR_SIZE):
        raise ValueError("Sector outside world bounds")
    digest = hashlib.sha256(
        f"ashfall:region:v1:{state_id}:{sector_x}:{sector_y}".encode()
    ).digest()
    return {
        "x": sector_x, "y": sector_y,
        "name": f"{BIOMES[digest[0] % len(BIOMES)]} · {sector_x:02d}-{sector_y:02d}",
        "biome": BIOMES[digest[0] % len(BIOMES)],
        "threat": 1 + digest[1] % 5,
        "resource_focus": RESOURCE_FOCUS[digest[2] % len(RESOURCE_FOCUS)],
        "terrain_index": digest[3] % 4,
        "bounds": {"x_min": sector_x * SECTOR_SIZE,
                   "y_min": sector_y * SECTOR_SIZE,
                   "x_max": (sector_x + 1) * SECTOR_SIZE - 1,
                   "y_max": (sector_y + 1) * SECTOR_SIZE - 1},
    }

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

def register_world(app,database,get_user,valid_csrf):
    with database() as db:
        initialize_world(db)
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_sector_discoveries (
            haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            sector_x INTEGER NOT NULL CHECK(sector_x BETWEEN 0 AND 15),
            sector_y INTEGER NOT NULL CHECK(sector_y BETWEEN 0 AND 15),
            discovered_at REAL NOT NULL,
            PRIMARY KEY(haven_id,sector_x,sector_y))""")

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

    @app.get("/ashfall/api/atlas")
    async def world_atlas(request: Request, state_id: int = 1):
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        with database() as db:
            own = db.execute("""SELECT p.x,p.y,h.id FROM ashfall_havens h
                JOIN ashfall_world_positions p ON p.haven_id=h.id
                WHERE h.user_id=? AND h.state_id=?""",
                (user["id"], state_id)).fetchone()
            if not own:
                raise HTTPException(404, "Haven not found in this state")
            center_x, center_y = own["x"] // SECTOR_SIZE, own["y"] // SECTOR_SIZE
            discovered = {(row["sector_x"], row["sector_y"]) for row in db.execute(
                "SELECT sector_x,sector_y FROM ashfall_sector_discoveries WHERE haven_id=? AND state_id=?",
                (own["id"],state_id))}
            sectors = []
            for y in range(max(0, center_y - 1), min(15, center_y + 1) + 1):
                for x in range(max(0, center_x - 1), min(15, center_x + 1) + 1):
                    sector = sector_profile(state_id, x, y)
                    sector["is_home"] = x == center_x and y == center_y
                    sector["discovered"] = sector["is_home"] or (x,y) in discovered
                    sector["haven_count"] = db.execute(
                        """SELECT COUNT(*) FROM ashfall_world_positions
                           WHERE state_id=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ?""",
                        (state_id, sector["bounds"]["x_min"], sector["bounds"]["x_max"],
                         sector["bounds"]["y_min"], sector["bounds"]["y_max"])
                    ).fetchone()[0]
                    sectors.append(sector)
        return {"state_id": state_id, "sector_size": SECTOR_SIZE,
                "home_sector": {"x": center_x, "y": center_y},
                "sectors": sectors,
                "note": "Regional terrain, threat and resource focus are deterministic intelligence previews. They do not yet modify combat, harvesting or movement."}

    @app.post("/ashfall/api/atlas/discover")
    async def discover_sector(request: Request):
        import time
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        form = await request.form()
        if not valid_csrf(request, str(form.get("csrf_token", ""))):
            raise HTTPException(400, "Invalid security token")
        try:
            state_id = int(form.get("state_id", "1"))
            x = int(form.get("sector_x", "-1"))
            y = int(form.get("sector_y", "-1"))
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid sector coordinates")
        if not (0 <= x < 16 and 0 <= y < 16):
            raise HTTPException(400, "Sector outside world bounds")
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            own = db.execute("""SELECT h.id,p.x,p.y FROM ashfall_havens h
                JOIN ashfall_world_positions p ON p.haven_id=h.id
                WHERE h.user_id=? AND h.state_id=?""",
                (user["id"],state_id)).fetchone()
            if not own:
                raise HTTPException(404, "Haven not found")
            hx, hy = own["x"] // SECTOR_SIZE, own["y"] // SECTOR_SIZE
            if max(abs(x-hx), abs(y-hy)) > 1:
                raise HTTPException(403, "Only sectors adjacent to your Haven can be surveyed")
            existing = db.execute(
                "SELECT 1 FROM ashfall_sector_discoveries WHERE haven_id=? AND sector_x=? AND sector_y=?",
                (own["id"],x,y)).fetchone()
            if not existing:
                db.execute("""INSERT INTO ashfall_sector_discoveries
                    (haven_id,state_id,sector_x,sector_y,discovered_at)
                    VALUES(?,?,?,?,?)""",(own["id"],state_id,x,y,time.time()))
        return {"sector":sector_profile(state_id,x,y),
                "discovered":True,"first_discovery":not bool(existing),
                "note":"Surveying records persistent discovery. No rewards, travel or combat are triggered."}
