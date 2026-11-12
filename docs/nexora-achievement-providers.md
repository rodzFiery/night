# NEXORA Universal Achievement Providers (Milestone 70)

NEXORA displays a **read-only projection** of server-earned achievements. A game retains ownership of its ledger, award conditions, reward economy and privacy rules.

## Provider contract

Each provider is registered as a pair `("WORLD_CODE", callback)`. The callback is invoked with `(db, authenticated_user_id)` and returns a list or tuple of earned achievement mappings. Never accept a user ID or earned-achievement list from a browser request. Providers must filter by the authenticated account and must not award achievements while building the projection.

Each mapping contains:

- `id`: stable, lowercase source-owned key (e.g. `ashfall:42:15`).
- `world`: the exact registered world code.
- `title`: nonempty display name (up to 120 characters).
- `description`: short display description (up to 500 characters).
- `earned_at`: trusted Unix timestamp or ISO-8601 date/time.
- `prestige`: optional nonnegative integer, **world-specific** and **non-spendable**.

The aggregator normalizes timestamps to UTC, rejects malformed data, detects duplicate provider registrations and duplicate achievement identities, and sorts by timestamp, world and ID. Provider results are not persisted in NEXORA's platform achievement ledger.

## Adding a future world

1. Build the game's own persistent achievement ledger and enforce award conditions on the server.
2. Implement a read-only provider that joins the ledger to the authenticated account.
3. Register its world code and callback in `app/nexora_universal_chronicle.py`.
4. Add tests for ownership isolation, idempotency, invalid payloads, ordering and zero mutation.
5. Design world-specific rewards separately. Do not sum currencies or grant NEXORA XP merely because an event appears in the Chronicle.

Currently registered: **NEXORA** and **ASHFALL**. Other game worlds are not yet integrated.

## Validation

Run from the repository root:

```bash
python tests/check_nexora_achievement_providers.py
python tests/check_nexora_universal_chronicle.py
python tests/check_ashfall_settlement_achievements.py
```

The GitHub Actions ASHFALL quality workflow includes these suites. A successful workflow run must be confirmed before release.
