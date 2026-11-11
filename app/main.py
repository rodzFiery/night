import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi import UploadFile, File
from PIL import Image
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATA_DIR = Path(os.getenv("NEXORA_DATA_DIR", PROJECT_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR = DATA_DIR / "profile_media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv("NEXORA_DB_PATH", DATA_DIR / "nexora.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv("NEXORA_SECRET_KEY", "development-only-change-this-before-deployment")
HTTPS_ONLY = os.getenv("NEXORA_HTTPS_ONLY", "0") == "1"
password_hasher = PasswordHasher()
RATE_LIMITS = {}

@contextmanager
def database():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

def initialize_database():
    with database() as connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            email TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_profiles (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            display_name TEXT NOT NULL DEFAULT '',
            bio TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            favourite_world TEXT NOT NULL DEFAULT '',
            avatar_file TEXT NOT NULL DEFAULT '',
            banner_file TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            achievement_key TEXT NOT NULL,
            unlocked_at TEXT NOT NULL,
            UNIQUE(user_id, achievement_key)
        )""")
        profile_columns = {row["name"] for row in connection.execute("PRAGMA table_info(player_profiles)")}
        if "public_visibility" not in profile_columns:
            connection.execute("ALTER TABLE player_profiles ADD COLUMN public_visibility TEXT NOT NULL DEFAULT 'private'")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_progress (
            user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
            xp INTEGER NOT NULL DEFAULT 0 CHECK(xp >= 0),
            lifetime_xp INTEGER NOT NULL DEFAULT 0 CHECK(lifetime_xp >= 0),
            level INTEGER NOT NULL DEFAULT 1 CHECK(level >= 1),
            shards INTEGER NOT NULL DEFAULT 0 CHECK(shards >= 0),
            updated_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS progression_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_key TEXT NOT NULL,
            source TEXT NOT NULL,
            xp_delta INTEGER NOT NULL DEFAULT 0,
            shard_delta INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, event_key)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS currency_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            event_key TEXT NOT NULL,
            currency TEXT NOT NULL,
            amount INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, event_key, currency)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS daily_claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            claim_date TEXT NOT NULL,
            xp_awarded INTEGER NOT NULL,
            shards_awarded INTEGER NOT NULL,
            streak_day INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(user_id, claim_date)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            addressee_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted')),
            created_at TEXT NOT NULL,
            responded_at TEXT,
            CHECK(requester_id != addressee_id),
            UNIQUE(requester_id, addressee_id)
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            kind TEXT NOT NULL,
            message TEXT NOT NULL,
            target_url TEXT NOT NULL DEFAULT '/dashboard',
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )""")
        connection.execute("""CREATE TABLE IF NOT EXISTS player_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            kind TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_friends_addressee ON player_friends(addressee_id, status)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_friends_requester ON player_friends(requester_id, status)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON player_notifications(user_id, is_read, created_at)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_activity_user ON player_activity(user_id, created_at)")
        connection.execute("""CREATE TABLE IF NOT EXISTS site_stats (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            homepage_views INTEGER NOT NULL DEFAULT 0,
            counting_started_at TEXT NOT NULL
        )""")
        connection.execute(
            "INSERT OR IGNORE INTO site_stats (id, homepage_views, counting_started_at) VALUES (1, 0, ?)",
            (datetime.now(timezone.utc).isoformat(),),
        )

initialize_database()

# Register independent NEXORA Universe systems without altering existing game or account routes.
from app.universe import register_universe
app = FastAPI(title="NEXORA", description="One identity. Independent worlds. A universe of browser games.", version="0.4.0")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, session_cookie="nexora_session",
                   same_site="lax", https_only=HTTPS_ONLY, max_age=60 * 60 * 24 * 14)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

GAMES = [
    {"slug":"stellar-frontier","name":"Stellar Frontier","genre":"SPACE STRATEGY","description":"Build beyond the edge of known space. Expand your reach, command fleets and shape a galactic empire.","icon":"✦","status":"IN DEVELOPMENT","theme":"space","number":"01","tagline":"THE FINAL FRONTIER","intro":"The galaxy is not waiting to be discovered. It is waiting to be claimed.","features":["Explore an evolving galaxy","Develop planets and colonies","Build and command a fleet"],"accent":"blue"},
    {"slug":"arena-eternum","name":"Arena Eternum","genre":"GLADIATOR RPG","description":"Enter the arena as an unknown contender. Train, compete and earn your place among legends.","icon":"⚔","status":"IN DEVELOPMENT","theme":"arena","number":"02","tagline":"GLORY IS EARNED","intro":"Every contender begins as a name nobody knows. What happens next is up to you.","features":["Create your contender","Train skills and equipment","Climb the competitive rankings"],"accent":"ember"},
    {"slug":"crown-and-kingdom","name":"Crown & Kingdom","genre":"MEDIEVAL STRATEGY","description":"Raise a settlement into a kingdom. Master diplomacy, build your strength and defend your crown.","icon":"♜","status":"IN DEVELOPMENT","theme":"kingdom","number":"03","tagline":"RULE YOUR LEGACY","intro":"A small settlement can become a kingdom. A wise ruler decides what it becomes after that.","features":["Build and develop your realm","Manage resources and alliances","Defend your borders"],"accent":"steel"},
    {"slug":"imperium","name":"Imperium","genre":"ANCIENT CIVILISATIONS","description":"Guide a civilisation through the ages, balance its ambitions and leave a mark on history.","icon":"⌂","status":"IN DEVELOPMENT","theme":"imperium","number":"04","tagline":"BUILD AN EMPIRE","intro":"History remembers the civilisations that dared to shape their own future.","features":["Lead a growing civilisation","Advance through historical eras","Balance culture, economy and power"],"accent":"gold"},
    {"slug":"nightfall","name":"Nightfall","genre":"DARK FANTASY RPG","description":"Cross into a realm of forgotten powers, dangerous quests and choices that shape your path.","icon":"☾","status":"IN DEVELOPMENT","theme":"nightfall","number":"05","tagline":"BEYOND THE VEIL","intro":"Beyond the veil lies a world shaped by old magic, lost kingdoms and difficult choices.","features":["Discover a dark fantasy world","Follow quests and storylines","Shape a character through progression"],"accent":"violet"},
    {"slug":"uncharted","name":"Uncharted","genre":"EXPLORATION & SURVIVAL","description":"Set out into an untamed world. Discover what lies beyond the map and make the unknown yours.","icon":"◇","status":"IN CONCEPT","theme":"uncharted","number":"06","tagline":"THE UNKNOWN AWAITS","intro":"The map ends somewhere. Your story begins just beyond it.","features":["Explore an untamed world","Discover locations and resources","Build a path through the unknown"],"accent":"teal"},
]

@contextmanager
def unused_context():
    yield

def get_user(user_id):
    if not user_id:
        return None
    with database() as connection:
        row = connection.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None

def ensure_player_profile(user_id):
    with database() as connection:
        user = connection.execute("SELECT created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return
        connection.execute("INSERT OR IGNORE INTO player_profiles (user_id, updated_at) VALUES (?, ?)",
                           (user_id, datetime.now(timezone.utc).isoformat()))
        connection.execute("INSERT OR IGNORE INTO player_achievements (user_id, achievement_key, unlocked_at) VALUES (?, ?, ?)",
                           (user_id, "first-arrival", user["created_at"]))

def player_profile(user_id):
    ensure_player_profile(user_id)
    with database() as connection:
        row = connection.execute("SELECT * FROM player_profiles WHERE user_id = ?", (user_id,)).fetchone()
        achievements = connection.execute("SELECT achievement_key, unlocked_at FROM player_achievements WHERE user_id = ? ORDER BY unlocked_at", (user_id,)).fetchall()
    result = dict(row)
    result["avatar_url"] = f"/media/{user_id}/avatar.webp" if result["avatar_file"] else ""
    result["banner_url"] = f"/media/{user_id}/banner.webp" if result["banner_file"] else ""
    result["achievements"] = [dict(item) for item in achievements]
    return result

XP_ACHIEVEMENTS = {
    "first-spark": {"name":"First Spark","description":"Earn your first progression XP.","rarity":"COMMON","icon":"✦"},
    "level-five": {"name":"Rising Force","description":"Reach level 5 in the NEXORA network.","rarity":"UNCOMMON","icon":"✧"},
    "level-ten": {"name":"Known Across Worlds","description":"Reach level 10 in the NEXORA network.","rarity":"RARE","icon":"◇"},
    "thousand-xp": {"name":"The Long Climb","description":"Earn 1,000 lifetime XP.","rarity":"RARE","icon":"☄"},
    "daily-seven": {"name":"Seven-Day Signal","description":"Claim rewards on seven consecutive days.","rarity":"EPIC","icon":"♛"},
}

def level_threshold(level):
    return 100 * (level - 1) + 25 * (level - 1) * (level - 2) // 2

def level_from_xp(total_xp):
    level = 1
    while total_xp >= level_threshold(level + 1):
        level += 1
    return level

def ensure_progression(user_id):
    now = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        connection.execute("INSERT OR IGNORE INTO player_progress (user_id, updated_at) VALUES (?, ?)", (user_id, now))

def progression_snapshot(user_id):
    ensure_player_profile(user_id)
    ensure_progression(user_id)
    today = datetime.now(timezone.utc).date()
    with database() as connection:
        row = connection.execute("SELECT * FROM player_progress WHERE user_id = ?", (user_id,)).fetchone()
        achievements = connection.execute("SELECT achievement_key, unlocked_at FROM player_achievements WHERE user_id = ?", (user_id,)).fetchall()
        last_claim = connection.execute("SELECT claim_date, streak_day FROM daily_claims WHERE user_id = ? ORDER BY claim_date DESC LIMIT 1", (user_id,)).fetchone()
        recent = connection.execute("SELECT source, xp_delta, shard_delta, created_at FROM progression_events WHERE user_id = ? ORDER BY id DESC LIMIT 5", (user_id,)).fetchall()
    data = dict(row)
    level = level_from_xp(data["lifetime_xp"])
    current_floor = level_threshold(level)
    next_floor = level_threshold(level + 1)
    data["level"] = level
    data["xp_into_level"] = data["lifetime_xp"] - current_floor
    data["xp_for_next_level"] = next_floor - current_floor
    data["progress_percent"] = min(100, int(data["xp_into_level"] * 100 / max(1, data["xp_for_next_level"])))
    unlocked_map = {item["achievement_key"]: item["unlocked_at"] for item in achievements}
    catalog = [{"key":key,**value,"unlocked_at":unlocked_map.get(key)} for key,value in XP_ACHIEVEMENTS.items()]
    catalog.insert(0,{"key":"first-arrival","name":"First Arrival","description":"Created your NEXORA player identity.","rarity":"COMMON","icon":"✦","unlocked_at":unlocked_map.get("first-arrival")})
    data["achievements"] = catalog
    data["achievement_count"] = len(unlocked_map)
    data["recent_events"] = [dict(item) for item in recent]
    data["daily_claimed"] = bool(last_claim and last_claim["claim_date"] == today.isoformat())
    data["daily_streak"] = last_claim["streak_day"] if last_claim and (today - datetime.fromisoformat(last_claim["claim_date"]).date()).days <= 1 else 0
    return data

def grant_progression(connection, user_id, event_key, source, xp_delta=0, shard_delta=0, now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    inserted = connection.execute("""INSERT OR IGNORE INTO progression_events
        (user_id,event_key,source,xp_delta,shard_delta,created_at) VALUES (?,?,?,?,?,?)""",
        (user_id,event_key,source,xp_delta,shard_delta,now)).rowcount
    if not inserted:
        return False
    total_after = max(0, connection.execute(
        "SELECT lifetime_xp FROM player_progress WHERE user_id=?", (user_id,)).fetchone()[0] + xp_delta)
    new_level = level_from_xp(total_after)
    current_level_xp = total_after - level_threshold(new_level)
    connection.execute("""UPDATE player_progress SET xp=?, lifetime_xp=?,
        shards=MAX(0,shards+?), level=?, updated_at=? WHERE user_id=?""",
        (current_level_xp,total_after,shard_delta,new_level,now,user_id))
    if shard_delta:
        balance=connection.execute("SELECT shards FROM player_progress WHERE user_id=?",(user_id,)).fetchone()[0]
        connection.execute("""INSERT OR IGNORE INTO currency_ledger
            (user_id,event_key,currency,amount,balance_after,reason,created_at) VALUES (?,?,?,?,?,?,?)""",
            (user_id,event_key,"SHARDS",shard_delta,balance,source,now))
    progress=connection.execute("SELECT lifetime_xp,level FROM player_progress WHERE user_id=?",(user_id,)).fetchone()
    unlocked=[]
    checks=[]
    if progress["lifetime_xp"] >= 1: checks.append("first-spark")
    if progress["level"] >= 5: checks.append("level-five")
    if progress["level"] >= 10: checks.append("level-ten")
    if progress["lifetime_xp"] >= 1000: checks.append("thousand-xp")
    for key in checks:
        if key in XP_ACHIEVEMENTS:
            if connection.execute("INSERT OR IGNORE INTO player_achievements (user_id,achievement_key,unlocked_at) VALUES (?,?,?)",
                                  (user_id,key,now)).rowcount:
                unlocked.append(key)
    return unlocked or True

def social_dashboard_data(user_id):
    with database() as connection:
        friends = connection.execute("""SELECT u.id, u.username, p.display_name, p.avatar_file
            FROM player_friends f JOIN users u ON u.id = CASE WHEN f.requester_id = ? THEN f.addressee_id ELSE f.requester_id END
            LEFT JOIN player_profiles p ON p.user_id = u.id
            WHERE f.status = 'accepted' AND (f.requester_id = ? OR f.addressee_id = ?)
            ORDER BY u.username COLLATE NOCASE LIMIT 12""", (user_id, user_id, user_id)).fetchall()
        pending = connection.execute("""SELECT f.id, f.created_at, u.id AS user_id, u.username,
            p.display_name, p.avatar_file FROM player_friends f JOIN users u ON u.id = f.requester_id
            LEFT JOIN player_profiles p ON p.user_id = u.id
            WHERE f.addressee_id = ? AND f.status = 'pending'
            ORDER BY f.created_at DESC LIMIT 10""", (user_id,)).fetchall()
        notifications = connection.execute("""SELECT id, kind, message, target_url, is_read, created_at
            FROM player_notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 8""", (user_id,)).fetchall()
        activity = connection.execute("""SELECT a.kind, a.detail, a.created_at, u.username
            FROM player_activity a JOIN users u ON u.id = a.user_id
            WHERE a.user_id = ? OR a.user_id IN (
                SELECT CASE WHEN requester_id = ? THEN addressee_id ELSE requester_id END
                FROM player_friends WHERE status = 'accepted' AND (requester_id = ? OR addressee_id = ?)
            ) ORDER BY a.created_at DESC LIMIT 12""", (user_id, user_id, user_id, user_id)).fetchall()
        friend_count = connection.execute("""SELECT COUNT(*) FROM player_friends
            WHERE status = 'accepted' AND (requester_id = ? OR addressee_id = ?)""", (user_id, user_id)).fetchone()[0]
        unread = connection.execute("SELECT COUNT(*) FROM player_notifications WHERE user_id = ? AND is_read = 0", (user_id,)).fetchone()[0]
    def decorate_player(row):
        item = dict(row)
        item["avatar_url"] = f"/media/{item['user_id']}/avatar.webp" if item.get("avatar_file") else ""
        return item
    return {
        "friends": [decorate_player(row) for row in friends],
        "friend_count": friend_count,
        "pending_requests": [decorate_player(row) for row in pending],
        "notifications": [dict(row) for row in notifications],
        "activity": [dict(row) for row in activity],
        "unread_notifications": unread,
    }


def player_search_results(user_id, query):
    if not query:
        return []
    with database() as connection:
        rows = connection.execute("""SELECT u.id AS user_id, u.username, p.display_name, p.avatar_file
            FROM users u JOIN player_profiles p ON p.user_id = u.id
            WHERE u.id != ? AND p.public_visibility = 'public'
              AND (u.username LIKE ? ESCAPE '\\' OR p.display_name LIKE ? ESCAPE '\\')
            ORDER BY CASE WHEN u.username = ? COLLATE NOCASE THEN 0 ELSE 1 END, u.username COLLATE NOCASE
            LIMIT 12""", (user_id, f"%{query}%", f"%{query}%", query)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            existing = connection.execute("""SELECT status, requester_id, addressee_id FROM player_friends
                WHERE (requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)
                LIMIT 1""", (user_id, item["user_id"], item["user_id"], user_id)).fetchone()
            item["friend_status"] = existing["status"] if existing else ""
            item["request_sent_by_me"] = bool(existing and existing["requester_id"] == user_id)
            item["avatar_url"] = f"/media/{item['user_id']}/avatar.webp" if item.get("avatar_file") else ""
            results.append(item)
    return results


def save_profile_image(user_id, upload, kind):
    if not upload or not upload.filename:
        return None
    raw = upload.file.read(3 * 1024 * 1024 + 1)
    if len(raw) > 3 * 1024 * 1024:
        raise ValueError("Images must be 3 MB or smaller.")
    try:
        import io
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image = image.convert("RGB")
            image.thumbnail((1200, 1200))
            folder = MEDIA_DIR / str(user_id)
            folder.mkdir(parents=True, exist_ok=True)
            image.save(folder / f"{kind}.webp", "WEBP", quality=88, method=6)
    except Exception as exc:
        raise ValueError("Please upload a valid JPG, PNG, WEBP or GIF image.") from exc
    return f"{kind}.webp"

def csrf_token(request):
    token = request.session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token

def page_context(request, **extra):
    data = {"request":request, "user":get_user(request.session.get("user_id")), "csrf_token":csrf_token(request)}
    data.update(extra)
    return data

def valid_csrf(request, submitted):
    expected = request.session.get("csrf_token", "")
    return bool(expected and submitted and hmac.compare_digest(expected, submitted))

def rate_limited(request, action, maximum, window=900):
    host = request.client.host if request.client else "unknown"
    key = f"{action}:{host}"
    now = time.time()
    recent = [stamp for stamp in RATE_LIMITS.get(key, []) if now - stamp < window]
    if len(recent) >= maximum:
        RATE_LIMITS[key] = recent
        return True
    recent.append(now)
    RATE_LIMITS[key] = recent
    return False

def homepage_statistics():
    with database() as connection:
        connection.execute("UPDATE site_stats SET homepage_views = homepage_views + 1 WHERE id = 1")
        row = connection.execute("""SELECT homepage_views, counting_started_at,
            (SELECT COUNT(*) FROM users) AS registered_players FROM site_stats WHERE id = 1""").fetchone()
    started = datetime.fromisoformat(row["counting_started_at"])
    return {"homepage_views":row["homepage_views"], "registered_players":row["registered_players"],
            "counting_started":started.strftime("%d %B %Y")}

@app.get("/", name="homepage")
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="index.html",
        context=page_context(request, games=GAMES, stats=homepage_statistics()))

@app.get("/register", name="register")
async def register_page(request: Request):
    if get_user(request.session.get("user_id")):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="account.html",
        context=page_context(request, mode="register", error=None))

@app.post("/register", name="register_submit")
async def register_submit(request: Request):
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    if rate_limited(request, "register", 5):
        return templates.TemplateResponse(request=request, name="account.html",
            context=page_context(request, mode="register", error="Too many attempts. Please wait 15 minutes and try again."),
            status_code=429)
    username = str(form.get("username", "")).strip()
    email = str(form.get("email", "")).strip().lower()
    password = str(form.get("password", ""))
    confirm = str(form.get("confirm_password", ""))
    error = None
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        error = "Choose a username of 3–20 characters using letters, numbers or underscores."
    elif len(email) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        error = "Enter a valid email address."
    elif len(password) < 12:
        error = "Your password must contain at least 12 characters."
    elif len(password) > 128:
        error = "Your password must be no longer than 128 characters."
    elif password != confirm:
        error = "Your passwords do not match."
    if error:
        return templates.TemplateResponse(request=request, name="account.html",
            context=page_context(request, mode="register", error=error, username=username, email=email), status_code=400)
    password_hash = password_hasher.hash(password)
    try:
        with database() as connection:
            cursor = connection.execute(
                "INSERT INTO users (username,email,password_hash,created_at) VALUES (?,?,?,?)",
                (username,email,password_hash,datetime.now(timezone.utc).isoformat()))
            user_id = cursor.lastrowid
            connection.execute("INSERT INTO player_profiles (user_id, updated_at) VALUES (?, ?)", (user_id, datetime.now(timezone.utc).isoformat()))
            connection.execute("INSERT INTO player_achievements (user_id, achievement_key, unlocked_at) VALUES (?, ?, ?)", (user_id, "first-arrival", datetime.now(timezone.utc).isoformat()))
    except sqlite3.IntegrityError:
        return templates.TemplateResponse(request=request, name="account.html",
            context=page_context(request, mode="register", error="That username or email is already registered.",
                                 username=username, email=email), status_code=409)
    request.session.clear()
    request.session["user_id"] = user_id
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/login", name="login")
async def login_page(request: Request):
    if get_user(request.session.get("user_id")):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="account.html",
        context=page_context(request, mode="login", error=None))

@app.post("/login", name="login_submit")
async def login_submit(request: Request):
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    if rate_limited(request, "login", 8):
        return templates.TemplateResponse(request=request, name="account.html",
            context=page_context(request, mode="login", error="Too many attempts. Please wait 15 minutes and try again."),
            status_code=429)
    identity = str(form.get("identity", "")).strip()
    password = str(form.get("password", ""))
    with database() as connection:
        row = connection.execute("SELECT id,password_hash FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
                                 (identity,identity)).fetchone()
    authenticated = False
    if row:
        try:
            authenticated = password_hasher.verify(row["password_hash"], password)
        except (VerifyMismatchError, InvalidHashError):
            authenticated = False
    if not authenticated:
        return templates.TemplateResponse(request=request, name="account.html",
            context=page_context(request, mode="login", error="Those login details weren't recognised."), status_code=401)
    request.session.clear()
    request.session["user_id"] = row["id"]
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/dashboard", name="dashboard")
async def dashboard(request: Request):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    joined = datetime.fromisoformat(user["created_at"]).strftime("%d %B %Y")
    search_query = str(request.query_params.get("q", "")).strip()[:32]
    progression = progression_snapshot(user["id"])
    social = social_dashboard_data(user["id"])
    search_results = player_search_results(user["id"], search_query)
    social_message = {"requested": "Friend request sent.", "updated": "Friend request updated.",
                      "exists": "A friendship or request already exists."}.get(request.query_params.get("social"), "")
    return templates.TemplateResponse(request=request, name="dashboard.html",
        context=page_context(request, games=GAMES, member_since=joined, profile=player_profile(user['id']),
            account_id=f"NX-{user['id']:06d}", social=social, progression=progression, search_query=search_query,
            search_results=search_results, social_message=social_message))

@app.post("/progression/daily-claim", name="daily_claim")
async def daily_claim(request: Request):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    ensure_progression(user["id"])
    now_dt = datetime.now(timezone.utc)
    today = now_dt.date().isoformat()
    now = now_dt.isoformat()
    with database() as connection:
        previous = connection.execute("SELECT claim_date, streak_day FROM daily_claims WHERE user_id=? ORDER BY claim_date DESC LIMIT 1",(user["id"],)).fetchone()
        if previous and previous["claim_date"] == today:
            return RedirectResponse("/dashboard?progression=claimed#progression",status_code=303)
        yesterday = (now_dt.date() - timedelta(days=1)).isoformat()
        streak = previous["streak_day"] + 1 if previous and previous["claim_date"] == yesterday else 1
        xp_reward = 35 + min(streak - 1, 6) * 5
        shard_reward = 15 + min(streak - 1, 6) * 2
        connection.execute("""INSERT INTO daily_claims (user_id,claim_date,xp_awarded,shards_awarded,streak_day,created_at)
            VALUES (?,?,?,?,?,?)""",(user["id"],today,xp_reward,shard_reward,streak,now))
        grant_progression(connection,user["id"],f"daily:{today}","Daily login reward",xp_reward,shard_reward,now)
        if streak >= 7:
            connection.execute("INSERT OR IGNORE INTO player_achievements (user_id,achievement_key,unlocked_at) VALUES (?,?,?)",
                               (user["id"],"daily-seven",now))
    return RedirectResponse("/dashboard?progression=claimed#progression",status_code=303)

@app.post("/friends/request/{target_id}", name="friend_request")
async def friend_request(request: Request, target_id: int):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    if target_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot add yourself.")
    now = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        target = connection.execute("""SELECT u.username FROM users u JOIN player_profiles p ON p.user_id = u.id
            WHERE u.id = ? AND p.public_visibility = 'public'""", (target_id,)).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Player not found or profile is private.")
        existing = connection.execute("""SELECT id, status FROM player_friends
            WHERE (requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)""",
            (user["id"], target_id, target_id, user["id"])).fetchone()
        if existing:
            return RedirectResponse("/dashboard?social=exists#community", status_code=303)
        connection.execute("INSERT INTO player_friends (requester_id, addressee_id, status, created_at) VALUES (?, ?, 'pending', ?)",
                           (user["id"], target_id, now))
        connection.execute("""INSERT INTO player_notifications (user_id, actor_id, kind, message, target_url, created_at)
            VALUES (?, ?, 'friend_request', ?, '/dashboard#community', ?)""",
            (target_id, user["id"], f"{user['username']} sent you a friend request.", now))
        connection.execute("INSERT INTO player_activity (user_id, kind, detail, created_at) VALUES (?, 'social', ?, ?)",
                           (user["id"], f"Sent a friend request to {target['username']}.", now))
    return RedirectResponse("/dashboard?social=requested#community", status_code=303)


@app.post("/friends/respond/{friendship_id}", name="friend_respond")
async def friend_respond(request: Request, friendship_id: int):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    decision = str(form.get("decision", "")).lower()
    if decision not in {"accept", "decline"}:
        raise HTTPException(status_code=400, detail="Invalid friend request action.")
    now = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        friendship = connection.execute("""SELECT f.requester_id, u.username FROM player_friends f
            JOIN users u ON u.id = f.addressee_id
            WHERE f.id = ? AND f.addressee_id = ? AND f.status = 'pending'""",
            (friendship_id, user["id"])).fetchone()
        if not friendship:
            raise HTTPException(status_code=404, detail="Friend request not found.")
        if decision == "accept":
            connection.execute("UPDATE player_friends SET status = 'accepted', responded_at = ? WHERE id = ?",
                               (now, friendship_id))
            connection.execute("""INSERT INTO player_notifications (user_id, actor_id, kind, message, target_url, created_at)
                VALUES (?, ?, 'friend_accepted', ?, '/dashboard#community', ?)""",
                (friendship["requester_id"], user["id"], f"{user['username']} accepted your friend request.", now))
            connection.execute("INSERT INTO player_activity (user_id, kind, detail, created_at) VALUES (?, 'social', ?, ?)",
                               (user["id"], f"Became friends with {friendship['username']}.", now))
            connection.execute("INSERT INTO player_activity (user_id, kind, detail, created_at) VALUES (?, 'social', ?, ?)",
                               (friendship["requester_id"], f"Became friends with {user['username']}.", now))
        else:
            connection.execute("DELETE FROM player_friends WHERE id = ?", (friendship_id,))
    return RedirectResponse("/dashboard?social=updated#community", status_code=303)


@app.get("/profile", name="profile")
async def profile_page(request: Request):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    profile = player_profile(user["id"])
    joined = datetime.fromisoformat(user["created_at"]).strftime("%d %B %Y")
    return templates.TemplateResponse(request=request, name="profile.html",
        context=page_context(request, profile=profile, games=GAMES, member_since=joined,
            account_id=f"NX-{user['id']:06d}", error=None,
            success="Your player identity has been updated." if request.query_params.get("saved") else None))

@app.post("/profile", name="profile_update")
async def profile_update(request: Request, avatar: UploadFile | None = File(default=None),
                         banner: UploadFile | None = File(default=None)):
    user = get_user(request.session.get("user_id"))
    if not user:
        return RedirectResponse("/login", status_code=303)
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    display_name = str(form.get("display_name", "")).strip()[:32]
    bio = str(form.get("bio", "")).strip()[:240]
    location = str(form.get("location", "")).strip()[:60]
    favourite_world = str(form.get("favourite_world", "")).strip()[:40]
    public_visibility = str(form.get("public_visibility", "private")).strip().lower()
    if public_visibility not in {"public", "private"}:
        public_visibility = "private"
    try:
        avatar_name = save_profile_image(user["id"], avatar, "avatar") if avatar else None
        banner_name = save_profile_image(user["id"], banner, "banner") if banner else None
    except ValueError as exc:
        joined = datetime.fromisoformat(user["created_at"]).strftime("%d %B %Y")
        return templates.TemplateResponse(request=request, name="profile.html",
            context=page_context(request, profile=player_profile(user["id"]), games=GAMES, member_since=joined,
                account_id=f"NX-{user['id']:06d}", error=str(exc), success=None), status_code=400)
    with database() as connection:
        connection.execute("""UPDATE player_profiles SET display_name=?, bio=?, location=?,
            favourite_world=?, public_visibility=?, avatar_file=CASE WHEN ? IS NULL THEN avatar_file ELSE ? END,
            banner_file=CASE WHEN ? IS NULL THEN banner_file ELSE ? END, updated_at=? WHERE user_id=?""",
            (display_name,bio,location,favourite_world,public_visibility,avatar_name,avatar_name,banner_name,banner_name,
             datetime.now(timezone.utc).isoformat(),user["id"]))
    return RedirectResponse("/profile?saved=1", status_code=303)

@app.get("/players/{username}", name="public_player_profile")
async def public_player_profile(request: Request, username: str):
    with database() as connection:
        row = connection.execute(
            "SELECT id, username, created_at FROM users WHERE username = ? COLLATE NOCASE",
            (username,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    profile = player_profile(row["id"])
    if profile.get("public_visibility") != "public":
        raise HTTPException(status_code=404, detail="This player profile is private")
    joined = datetime.fromisoformat(row["created_at"]).strftime("%d %B %Y")
    return templates.TemplateResponse(request=request, name="public_profile.html",
        context={"request": request, "player": dict(row), "profile": profile,
                 "member_since": joined, "account_id": f"NX-{row['id']:06d}",
                 "achievement_count": len(profile["achievements"])})

@app.post("/logout", name="logout")
async def logout(request: Request):
    form = await request.form()
    if not valid_csrf(request, str(form.get("csrf_token", ""))):
        raise HTTPException(status_code=400, detail="Security check expired. Please reload and try again.")
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/worlds/{slug}", name="world_portal")
async def world_portal(request: Request, slug: str):
    game = next((item for item in GAMES if item["slug"] == slug), None)
    if game is None:
        raise HTTPException(status_code=404, detail="World not found")
    return templates.TemplateResponse(request=request, name="world.html", context={
        "request":request, "game":game,
        "previous_world":GAMES[(int(game["number"])-2) % len(GAMES)],
        "next_world":GAMES[int(game["number"]) % len(GAMES)],
        "user":get_user(request.session.get("user_id")),
    })

register_universe(app, database, get_user, page_context, templates, progression_snapshot, grant_progression, ensure_progression, valid_csrf, password_hasher)

@app.get("/health", name="health_check")
async def health_check():
    return {"status":"ok","platform":"NEXORA","version":app.version}
