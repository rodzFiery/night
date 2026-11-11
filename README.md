# NEXORA Platform

**One identity. Infinite worlds.**

NEXORA is a browser-first gaming platform bringing independent, persistent game worlds together under one player identity.

## Current milestone: v0.4 — Player accounts & founding counters

The current foundation includes:

- Responsive NEXORA homepage and six world previews
- A dedicated portal page for each of the six worlds
- Shared FastAPI application and reusable Jinja templates
- Distinct world descriptions, planned features and visual themes
- Player registration, login, logout and a private player hub
- SQLite storage for accounts and homepage-view statistics
- Argon2 password hashing, signed sessions, CSRF checks and basic in-memory rate limits
- Live registered-player and homepage-view counters, counting from the first database initialisation
- Health-check endpoint at `/health`

The six game portals are previews and remain locked. Game engines, email verification, password-reset emails, social features, payments and the marketplace are not implemented yet. The account system is an early functional foundation and needs a security/privacy review before public production launch.

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


## Accounts, counters and local data

The first time the app starts with a new database, NEXORA stores the counter start timestamp. Homepage views count homepage loads (not unique visitors); registered players count successfully created accounts. Both values are stored in SQLite and survive restarts as long as the database file is kept.

By default, the database is created at `data/nexora.db`. Set `NEXORA_DB_PATH` to use a persistent deployment volume, for example `/data/nexora.db`.

Before public deployment, set a unique `NEXORA_SECRET_KEY` and set `NEXORA_HTTPS_ONLY=1` behind HTTPS. Generate a key with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

For local development, the app has a development-only fallback secret. Do not use that fallback on a public server.
