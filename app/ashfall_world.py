"""ASHFALL 0.2 — persistent world coordinates and authenticated world-state API."""
import hashlib
import time
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
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_expedition_chronicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
            state_id INTEGER NOT NULL,
            sector_x INTEGER NOT NULL,
            sector_y INTEGER NOT NULL,
            started_at REAL NOT NULL,
            completed_at REAL NOT NULL,
            UNIQUE(haven_id,sector_x,sector_y))""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_ashfall_chronicle_haven ON ashfall_expedition_chronicle(haven_id,completed_at DESC)")
        db.execute("""CREATE TABLE IF NOT EXISTS ashfall_scout_missions (haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,state_id INTEGER NOT NULL,sector_x INTEGER NOT NULL,sector_y INTEGER NOT NULL,started_at REAL NOT NULL,finishes_at REAL NOT NULL)""")

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
    async def world_atlas(request: Request, state_id: int = 1, view_x: int | None = None, view_y: int | None = None):
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
            mission_row = db.execute("SELECT sector_x,sector_y,started_at,finishes_at FROM ashfall_scout_missions WHERE haven_id=?",(own["id"],)).fetchone()
            mission = dict(mission_row) if mission_row else None
            from app.ashfall_cartography import mastery_snapshot
            mastery = mastery_snapshot(state_id,center_x,center_y,discovered)
            chronicle_rows = db.execute("""SELECT sector_x,sector_y,started_at,completed_at
                FROM ashfall_expedition_chronicle
                WHERE haven_id=? AND state_id=?
                ORDER BY completed_at DESC, id DESC LIMIT 30""",
                (own["id"],state_id)).fetchall()
            chronicle = []
            for entry in chronicle_rows:
                profile = sector_profile(state_id,entry["sector_x"],entry["sector_y"])
                chronicle.append({"sector_x":entry["sector_x"],"sector_y":entry["sector_y"],
                    "started_at":entry["started_at"],"completed_at":entry["completed_at"],
                    "name":profile["name"],"biome":profile["biome"],
                    "threat":profile["threat"],"resource_focus":profile["resource_focus"]})
            from app.ashfall_campaigns import campaign_snapshot
            all_missions = db.execute("""SELECT sector_x,sector_y
                FROM ashfall_expedition_chronicle WHERE haven_id=? AND state_id=?""",
                (own["id"],state_id)).fetchall()
            campaigns = campaign_snapshot(state_id,center_x,center_y,discovered,
                [(row["sector_x"],row["sector_y"]) for row in all_missions])
            from app.ashfall_legacy import legacy_snapshot
            legacy = legacy_snapshot((center_x, center_y), discovered, len(all_missions))
            from app.ashfall_intelligence import frontier_intelligence
            known_cells = discovered | {(center_x, center_y)}
            known_profiles = {cell: sector_profile(state_id, *cell) for cell in known_cells}
            intelligence = frontier_intelligence((center_x, center_y), discovered, known_profiles)
            from app.ashfall_theaters import theater_snapshot
            theaters = theater_snapshot((center_x, center_y), discovered, known_profiles)
            from app.ashfall_theater_development import theater_development
            development = theater_development(theaters["theaters"])
            from app.ashfall_frontier_orders import frontier_orders
            objective_row = db.execute(
                "SELECT target_x,target_y FROM ashfall_expedition_plans WHERE haven_id=? AND state_id=?",
                (own["id"], state_id)).fetchone()
            objective = (objective_row["target_x"], objective_row["target_y"]) if objective_row else None
            orders = frontier_orders((center_x, center_y), discovered, known_profiles, mission, objective)
            from app.ashfall_frontier import frontier_state, atlas_viewport
            if view_x is None: view_x = center_x
            if view_y is None: view_y = center_y
            if not (0 <= view_x < 16 and 0 <= view_y < 16):
                raise HTTPException(400, "Atlas camera outside world bounds")
            sectors = []
            for x, y in atlas_viewport(view_x, view_y):
                sector = sector_profile(state_id, x, y)
                sector["is_home"] = x == center_x and y == center_y
                sector["frontier_status"] = frontier_state((center_x,center_y),discovered,(x,y))
                sector["discovered"] = sector["is_home"] or (x,y) in discovered
                if not sector["discovered"]:
                    sector["name"] = None
                    sector["biome"] = None
                    sector["threat"] = None
                    sector["resource_focus"] = None
                    sector["terrain_index"] = None
                sector["haven_count"] = db.execute(
                    """SELECT COUNT(*) FROM ashfall_world_positions
                       WHERE state_id=? AND x BETWEEN ? AND ? AND y BETWEEN ? AND ?""",
                    (state_id, sector["bounds"]["x_min"], sector["bounds"]["x_max"],
                     sector["bounds"]["y_min"], sector["bounds"]["y_max"])
                ).fetchone()[0]
                if not sector["discovered"]:
                    sector["haven_count"] = None
                sectors.append(sector)
        return {"state_id": state_id, "sector_size": SECTOR_SIZE,
                "home_sector": {"x": center_x, "y": center_y},
                "atlas_radius": 3,
                "view_center": {"x": view_x, "y": view_y},
                "server_time": time.time(), "scout_mission": mission,
                "frontier_intelligence": intelligence,
                "frontier_legacy": legacy,
                "frontier_orders": orders,
                "regional_theaters": theaters,
                "theater_development": development,
                "cartography": mastery,
                "chronicle": chronicle,
                "campaigns": campaigns,
                "sectors": sectors,
                "note": "Regional terrain, threat and resource focus are deterministic intelligence previews. They do not yet modify combat, harvesting or movement."}

    @app.get("/ashfall/api/atlas/route")
    async def atlas_route(request: Request, state_id: int = 1,
                          target_x: int = -1, target_y: int = -1):
        user = get_user(request.session.get("user_id"))
        if not user:
            raise HTTPException(401, "Sign in required")
        if not (0 <= target_x < 16 and 0 <= target_y < 16):
            raise HTTPException(400, "Target outside world bounds")
        with database() as db:
            own = db.execute("""SELECT p.x,p.y,h.id FROM ashfall_havens h
                JOIN ashfall_world_positions p ON p.haven_id=h.id
                WHERE h.user_id=? AND h.state_id=?""",
                (user["id"],state_id)).fetchone()
            if not own:
                raise HTTPException(404, "Haven not found in this state")
            discovered = {(row["sector_x"],row["sector_y"]) for row in db.execute(
                "SELECT sector_x,sector_y FROM ashfall_sector_discoveries WHERE haven_id=? AND state_id=?",
                (own["id"],state_id))}
        from app.ashfall_routes import plan_route
        home = (own["x"]//SECTOR_SIZE,own["y"]//SECTOR_SIZE)
        plan = plan_route(home,(target_x,target_y),discovered)
        return {"state_id":state_id,"home":{"x":home[0],"y":home[1]},
                "target":{"x":target_x,"y":target_y},**plan,
                "note":"Advisory route only. Estimates are threat-dependent ranges, not promises. Dispatch each reachable scout mission separately."}

    from app.ashfall_scouting import register_scouting
    register_scouting(app, database, get_user, valid_csrf)

    from app.ashfall_plans import register_expedition_plans
    register_expedition_plans(app, database, get_user, valid_csrf)
