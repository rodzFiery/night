from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="NEXORA",
    description="One identity. Independent worlds. A universe of browser games.",
    version="0.3.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


# Each world is defined independently from the page routes.
# This keeps the platform easy to expand as the games become real projects.
GAMES = [
    {
        "slug": "stellar-frontier",
        "name": "Stellar Frontier",
        "genre": "SPACE STRATEGY",
        "description": "Build beyond the edge of known space. Expand your reach, command fleets and shape a galactic empire.",
        "icon": "✦",
        "status": "IN DEVELOPMENT",
        "theme": "space",
        "number": "01",
        "tagline": "THE FINAL FRONTIER",
        "intro": "The galaxy is not waiting to be discovered. It is waiting to be claimed.",
        "features": ["Explore an evolving galaxy", "Develop planets and colonies", "Build and command a fleet"],
        "accent": "blue",
    },
    {
        "slug": "arena-eternum",
        "name": "Arena Eternum",
        "genre": "GLADIATOR RPG",
        "description": "Enter the arena as an unknown contender. Train, compete and earn your place among legends.",
        "icon": "⚔",
        "status": "IN DEVELOPMENT",
        "theme": "arena",
        "number": "02",
        "tagline": "GLORY IS EARNED",
        "intro": "Every contender begins as a name nobody knows. What happens next is up to you.",
        "features": ["Create your contender", "Train skills and equipment", "Climb the competitive rankings"],
        "accent": "ember",
    },
    {
        "slug": "crown-and-kingdom",
        "name": "Crown & Kingdom",
        "genre": "MEDIEVAL STRATEGY",
        "description": "Raise a settlement into a kingdom. Master diplomacy, build your strength and defend your crown.",
        "icon": "♜",
        "status": "IN DEVELOPMENT",
        "theme": "kingdom",
        "number": "03",
        "tagline": "RULE YOUR LEGACY",
        "intro": "A small settlement can become a kingdom. A wise ruler decides what it becomes after that.",
        "features": ["Build and develop your realm", "Manage resources and alliances", "Defend your borders"],
        "accent": "steel",
    },
    {
        "slug": "imperium",
        "name": "Imperium",
        "genre": "ANCIENT CIVILISATIONS",
        "description": "Guide a civilisation through the ages, balance its ambitions and leave a mark on history.",
        "icon": "⌂",
        "status": "IN DEVELOPMENT",
        "theme": "imperium",
        "number": "04",
        "tagline": "BUILD AN EMPIRE",
        "intro": "History remembers the civilisations that dared to shape their own future.",
        "features": ["Lead a growing civilisation", "Advance through historical eras", "Balance culture, economy and power"],
        "accent": "gold",
    },
    {
        "slug": "nightfall",
        "name": "Nightfall",
        "genre": "DARK FANTASY RPG",
        "description": "Cross into a realm of forgotten powers, dangerous quests and choices that shape your path.",
        "icon": "☾",
        "status": "IN DEVELOPMENT",
        "theme": "nightfall",
        "number": "05",
        "tagline": "BEYOND THE VEIL",
        "intro": "Beyond the veil lies a world shaped by old magic, lost kingdoms and difficult choices.",
        "features": ["Discover a dark fantasy world", "Follow quests and storylines", "Shape a character through progression"],
        "accent": "violet",
    },
    {
        "slug": "uncharted",
        "name": "Uncharted",
        "genre": "EXPLORATION & SURVIVAL",
        "description": "Set out into an untamed world. Discover what lies beyond the map and make the unknown yours.",
        "icon": "◇",
        "status": "IN CONCEPT",
        "theme": "uncharted",
        "number": "06",
        "tagline": "THE UNKNOWN AWAITS",
        "intro": "The map ends somewhere. Your story begins just beyond it.",
        "features": ["Explore an untamed world", "Discover locations and resources", "Build a path through the unknown"],
        "accent": "teal",
    },
]


@app.get("/", name="homepage")
async def homepage(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"games": GAMES},
    )


@app.get("/worlds/{slug}", name="world_portal")
async def world_portal(request: Request, slug: str):
    game = next((item for item in GAMES if item["slug"] == slug), None)

    if game is None:
        raise HTTPException(status_code=404, detail="World not found")

    return templates.TemplateResponse(
        request=request,
        name="world.html",
        context={
            "game": game,
            "previous_world": GAMES[(int(game["number"]) - 2) % len(GAMES)],
            "next_world": GAMES[int(game["number"]) % len(GAMES)],
        },
    )


@app.get("/health", name="health_check")
async def health_check():
    return {"status": "ok", "platform": "NEXORA", "version": app.version}
