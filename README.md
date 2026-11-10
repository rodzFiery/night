# Genesis Platform

**One platform. Multiple worlds.**

Genesis is a browser-first gaming platform concept bringing multiple independent, persistent browser games together under one player identity.

## Current milestone: v0.1

This first milestone establishes the public-facing platform homepage:

- Responsive Genesis landing page
- Six initial game portal cards
- Shared visual direction: charcoal, electric blue and violet
- FastAPI application foundation
- Health-check endpoint

The game cards are currently portals/placeholders. Game engines, player accounts, registration, login, profiles and database-backed features are not implemented yet.

## Project structure

```text
.
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── requirements.txt
└── .gitignore
```

## Run locally

Python 3.11 or newer is recommended.

1. Clone the repository.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment.
4. Install dependencies.
5. Start the development server.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

The health endpoint is available at http://127.0.0.1:8000/health.

## Development principles

- Keep platform services and individual game systems separated.
- Give each game its own progression, economy and gameplay systems.
- Use a shared platform identity rather than separate accounts for each game.
- Build in complete, testable milestones.
- Never commit secrets, API keys or production credentials.
