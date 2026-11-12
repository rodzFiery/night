"""NEXORA 70 — validated, read-only achievement provider contract.

Provider callbacks receive a database connection and authenticated account ID.
Only server-owned sources are registered. Never accept client-submitted events.
"""
import re
from datetime import datetime, timezone

WORLD_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,31}$")
KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9:_-]{0,127}$")
MAX_EVENTS_PER_PROVIDER = 10000


def normalize_timestamp(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not an achievement timestamp")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    raise ValueError("Unsupported achievement timestamp")


def validate_event(event, expected_world):
    """Validate provider output and return a detached, canonical event."""
    if not isinstance(event, dict):
        raise ValueError("Achievement event must be a mapping")
    world = event.get("world")
    if world != expected_world:
        raise ValueError("Achievement provider cannot impersonate another world")
    key = event.get("id")
    if not isinstance(key, str) or not KEY_PATTERN.fullmatch(key):
        raise ValueError("Invalid achievement identifier")
    title, description = event.get("title"), event.get("description")
    if not isinstance(title, str) or not title.strip() or len(title) > 120:
        raise ValueError("Invalid achievement title")
    if not isinstance(description, str) or len(description) > 500:
        raise ValueError("Invalid achievement description")
    prestige = event.get("prestige", 0)
    if type(prestige) is not int or prestige < 0 or prestige > 1000000:
        raise ValueError("Invalid prestige value")
    return {
        "id": key,
        "world": world,
        "title": title,
        "description": description,
        "earned_at": normalize_timestamp(event.get("earned_at")),
        "prestige": prestige,
    }


def compose_chronicle(db, user_id, providers):
    """Compose independent provider results with deterministic collision checks.

    providers: iterable of (world_code, callable(db, authenticated_user_id)).
    Any invalid provider result fails closed instead of publishing partial claims.
    """
    events, seen, worlds = [], set(), set()
    for world, provider in providers:
        if not isinstance(world, str) or not WORLD_PATTERN.fullmatch(world):
            raise ValueError("Invalid provider world code")
        if world in worlds:
            raise ValueError("Duplicate achievement provider")
        worlds.add(world)
        if not callable(provider):
            raise ValueError("Achievement provider must be callable")
        supplied = provider(db, user_id)
        if not isinstance(supplied, (list, tuple)) or len(supplied) > MAX_EVENTS_PER_PROVIDER:
            raise ValueError("Invalid achievement provider result")
        for raw in supplied:
            event = validate_event(raw, world)
            identity = (event["world"], event["id"])
            if identity in seen:
                raise ValueError("Duplicate achievement identity")
            seen.add(identity)
            events.append(event)
    events.sort(key=lambda item: (item["earned_at"], item["world"], item["id"]))
    return events
