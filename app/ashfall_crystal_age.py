"""ASHFALL Crystal Age progression: 30 conventional + 25 crystal building levels."""
import math
import time

NORMAL_CAP = 30
CRYSTAL_CAP = 25
MAX_LEVEL = NORMAL_CAP + CRYSTAL_CAP
RARE_MATERIALS = ("crystal_shards", "ancient_cores", "prismatic_essence")

def stage(level):
    return {"era": "crystal" if level > NORMAL_CAP else "survival",
            "crystal_level": max(0, level - NORMAL_CAP),
            "max_level": MAX_LEVEL}

def crystal_cost(level):
    """Cost of advancing from level 30 to 31, ... 54 to 55."""
    if not NORMAL_CAP <= level < MAX_LEVEL:
        return {}
    n = level - NORMAL_CAP + 1
    return {
        "crystal_shards": 8 + 4 * n + n * n,
        "ancient_cores": 1 + (n // 3),
        "prismatic_essence": 0 if n <= 4 else 1 + (n - 5) // 4,
    }

def conventional_cost(base_cost, level, initial_level):
    if level < NORMAL_CAP:
        return {r: int(v * 1.6 ** max(0, level - initial_level)) for r,v in base_cost.items()}
    # Crystal-era conventional requirements are deliberately bounded to avoid
    # integer overflow and to make rare materials the primary bottleneck.
    return {r: int(v * 1.6 ** (NORMAL_CAP - initial_level) * (1 + (level - NORMAL_CAP) * .12))
            for r,v in base_cost.items()}

def construction_seconds(base_seconds, level, initial_level):
    if level < NORMAL_CAP:
        return int(base_seconds * 1.45 ** max(0, level - initial_level))
    return int(base_seconds * 1.45 ** (NORMAL_CAP - initial_level) * (1 + (level - NORMAL_CAP) * .08))

def initialize(db):
    db.execute("""CREATE TABLE IF NOT EXISTS ashfall_crystal_balances(
      haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id) ON DELETE CASCADE,
      crystal_shards INTEGER NOT NULL DEFAULT 0 CHECK(crystal_shards >= 0),
      ancient_cores INTEGER NOT NULL DEFAULT 0 CHECK(ancient_cores >= 0),
      prismatic_essence INTEGER NOT NULL DEFAULT 0 CHECK(prismatic_essence >= 0),
      last_salvage_at REAL NOT NULL DEFAULT 0)""")
    # Older SQLite tables have CHECK(level BETWEEN 0 AND 30). Rebuild safely,
    # preserving existing building levels and the original table's foreign key.
    row = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='ashfall_building_levels'").fetchone()
    ddl = row[0] if row else ""
    if "BETWEEN 0 AND 30" in ddl.upper():
        db.execute("""CREATE TABLE ashfall_building_levels_crystal_migration(
          haven_id INTEGER NOT NULL REFERENCES ashfall_havens(id) ON DELETE CASCADE,
          building_key TEXT NOT NULL,
          level INTEGER NOT NULL DEFAULT 0 CHECK(level BETWEEN 0 AND 55),
          PRIMARY KEY(haven_id,building_key))""")
        db.execute("""INSERT INTO ashfall_building_levels_crystal_migration(haven_id,building_key,level)
          SELECT haven_id,building_key,level FROM ashfall_building_levels""")
        db.execute("DROP TABLE ashfall_building_levels")
        db.execute("ALTER TABLE ashfall_building_levels_crystal_migration RENAME TO ashfall_building_levels")

def prepare(db,haven_id):
    db.execute("INSERT OR IGNORE INTO ashfall_crystal_balances(haven_id) VALUES(?)",(haven_id,))

def balance(db,haven_id):
    prepare(db,haven_id)
    return dict(db.execute("SELECT crystal_shards,ancient_cores,prismatic_essence,last_salvage_at FROM ashfall_crystal_balances WHERE haven_id=?",(haven_id,)).fetchone())

def salvage(db,haven_id,now=None):
    """A once-per-24-hour crystal salvage mission, unlocked at HQ level 30."""
    now = time.time() if now is None else now
    row = db.execute("SELECT level FROM ashfall_building_levels WHERE haven_id=? AND building_key='hq'",(haven_id,)).fetchone()
    if not row or row[0] < NORMAL_CAP:
        raise ValueError("Reach Command Center level 30 to unlock Crystal Salvage")
    current=balance(db,haven_id)
    if now-current["last_salvage_at"] < 86400:
        raise ValueError("Crystal Salvage is still recovering")
    # Predictable, non-random baseline source of rare materials.
    reward={"crystal_shards":45,"ancient_cores":3,"prismatic_essence":2}
    db.execute("""UPDATE ashfall_crystal_balances SET crystal_shards=crystal_shards+?,
      ancient_cores=ancient_cores+?,prismatic_essence=prismatic_essence+?,
      last_salvage_at=? WHERE haven_id=?""",(*reward.values(),now,haven_id))
    return reward
