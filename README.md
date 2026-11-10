# NEXORA Platform

**One identity. Infinite worlds.**

NEXORA is a browser-first gaming platform bringing independent, persistent game worlds together under one player identity.

## Current milestone: v0.3 — World portals

The current foundation includes:

- Responsive NEXORA homepage and six world previews
- A dedicated portal page for each of the six worlds
- Shared FastAPI application and reusable Jinja templates
- Distinct world descriptions, planned features and visual themes
- Health-check endpoint at `/health`

The portals are currently previews. The game engines, player accounts, registration, login, profiles, databases and social features are not implemented yet.

## Project structure

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── templates/
│   │   ├── index.html
│   │   └── world.html
│   └── static/
│       ├── css/
│       │   ├── style.css
│       │   └── portal.css
│       └── js/
│           └── main.js
├── requirements.txt
└── .gitignore
```

## Run locally

Python 3.11 or newer is recommended.

1. Open a terminal in the project folder.
2. Create and activate a virtual environment.
3. Install dependencies.
4. Start the development server.

### Windows PowerShell

```powershell
py -3 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

The six world portals are available from the homepage. For example:
- http://127.0.0.1:8000/worlds/stellar-frontier
- http://127.0.0.1:8000/worlds/nightfall

The health endpoint is available at http://127.0.0.1:8000/health.

## Development principles

- Keep platform services and individual game systems separated.
- Give each game its own progression, economy and gameplay systems.
- Use a shared platform identity rather than separate accounts for each game.
- Build in complete, testable milestones.
- Never commit secrets, API keys or production credentials.
