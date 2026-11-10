from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="Genesis",
    description="One platform. Multiple worlds. Your next adventure starts here.",
    version="0.1.0",
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
            "description": "Build your empire among the stars. Explore, expand and command your fleet.",
            "icon": "✦",
            "status": "COMING SOON",
            "theme": "space",
        },
        {
            "slug": "arena-eternum",
            "name": "Arena Eternum",
            "genre": "GLADIATOR RPG",
            "description": "Forge your legend in the arena. Train, equip and rise through the ranks.",
            "icon": "⚔",
            "status": "COMING SOON",
            "theme": "arena",
        },
        {
            "slug": "crown-and-kingdom",
            "name": "Crown & Kingdom",
            "genre": "MEDIEVAL STRATEGY",
            "description": "Raise your banners, develop your lands and shape a kingdom worth remembering.",
            "icon": "♜",
            "status": "COMING SOON",
            "theme": "kingdom",
        },
        {
            "slug": "imperium",
            "name": "Imperium",
            "genre": "ANCIENT CIVILISATIONS",
            "description": "Lead a civilisation from a humble settlement to a powerful empire.",
            "icon": "⌂",
            "status": "COMING SOON",
            "theme": "imperium",
        },
        {
            "slug": "nightfall",
            "name": "Nightfall",
            "genre": "DARK FANTASY RPG",
            "description": "Enter a world of forgotten legends, dangerous quests and ancient powers.",
            "icon": "☾",
            "status": "COMING SOON",
            "theme": "nightfall",
        },
        {
            "slug": "uncharted",
            "name": "Uncharted",
            "genre": "NEW WORLD",
            "description": "A new adventure is taking shape. Its world will be revealed in time.",
            "icon": "◇",
            "status": "IN DEVELOPMENT",
            "theme": "uncharted",
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"games": games},
    )


@app.get("/health", name="health_check")
async def health_check():
    return {"status": "ok", "platform": "Genesis", "version": app.version}
