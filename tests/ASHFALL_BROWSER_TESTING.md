# ASHFALL browser quality checks

## Prerequisites

- Python 3.10 or newer
- Node.js for JavaScript syntax validation
- Chromium via Playwright for browser checks

From the repository root:

```powershell
python -m pip install playwright==1.56.0
python -m playwright install chromium
```

## Available checks

```powershell
python tests/check_ashfall.py
python tests/browser_ashfall.py
python tests/browser_ashfall_page.py
```

- `check_ashfall.py` checks HTML integration, referenced static files, six facility SVGs, and JS syntax.
- `browser_ashfall.py` tests the preview and construction modules in an isolated browser harness.
- `browser_ashfall_page.py` loads the **actual** `app/ashfall_world.html` using an isolated local server and mocked world/economy endpoints.

The full-page diagnostic writes screenshots and JSON results into `artifacts/ashfall-diagnostics/` at 1440×900 and 390×844.

## Interpretation

A passing full-page diagnostic means that the mocked settlement loaded and the tested preview interactions succeeded. It **does not** establish that live authentication, economy persistence, actual upgrade transactions, responsive visual quality, or production performance are correct.

Other endpoints intentionally return 404 fixture responses; corresponding unavailable-panel messages are expected. Uncaught JavaScript exceptions fail the diagnostic.

**Review the screenshots manually**. The script captures images but does not automatically judge their composition or artistic quality.

The full-page diagnostic is intentionally **not** part of the required GitHub Actions gate until its first successful local run and fixture validation. The existing isolated browser tests remain in CI.

Do not commit generated screenshots if they contain personal account data. This diagnostic uses synthetic data.

## ASHFALL 42 — settlement stress scenarios

The full-page diagnostic now exercises both 1440×900 and 390×844 viewports.

- All four development command views are captured separately.
- Each view must fit its available width without horizontal overflow.
- Keyboard ArrowRight and End switch between command tabs.
- The server-shaped economy fixture is temporarily varied to simulate an occupied construction slot, insufficient wood and a maximum-level Barracks.
- Assertions check that a busy slot blocks readiness, shortages remain visible, the maximum-level facility is labelled correctly, and strategy recommendations exclude that facility.
- The original fixture is restored before inspector close/Escape checks.

The scenarios are **isolated frontend tests**, not authenticated production transactions.
The workflow uploads diagnostic screenshots for inspection; screenshots do not by themselves certify visual quality.

Run locally:

```powershell
python -m pip install playwright==1.56.0
python -m playwright install chromium
python tests/browser_ashfall_page.py
```

Screenshots and JSON diagnostics are written to `artifacts/ashfall-diagnostics/`.
