from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="NEXORA",
    description="One identity. Independent worlds. A universe of browser games.",
    version="0.2.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", name="homepage")
async def homepage(request: Request):
    games = [
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
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"games": games},
    )


@app.get("/health", name="health_check")
async def health_check():
    return {"status": "ok", "platform": "NEXORA", "version": app.version}
