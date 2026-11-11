import hmac
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
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
    return templates.TemplateResponse(request=request, name="dashboard.html",
        context=page_context(request, games=GAMES, member_since=joined, profile=player_profile(user['id']), account_id=f"NX-{user['id']:06d}"))

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

@app.get("/health", name="health_check")
async def health_check():
    return {"status":"ok","platform":"NEXORA","version":app.version}
