"""NEXORA 75 — read-only ASHFALL milestone development intelligence.

Reads only Havens owned by the authenticated player. Does not accrue resources,
complete queues, grant milestones, or modify the game ledger.
"""
from app.ashfall_settlement_achievements import FACILITIES, TIERS, CHRONICLE


def settlement_milestone_intelligence(db, user_id):
    havens = db.execute(
        "SELECT id FROM ashfall_havens WHERE user_id=? ORDER BY id", (user_id,)
    ).fetchall()
    reports = []
    for haven in havens:
        haven_id = int(haven["id"])
        rows = db.execute(
            """SELECT building_key,level FROM ashfall_building_levels
               WHERE haven_id=?""", (haven_id,)
        ).fetchall()
        levels = {row["building_key"]: max(0, int(row["level"]))
                  for row in rows if row["building_key"] in FACILITIES}
        # Uninitialized building rows count as zero, never as a completed facility.
        levels = {key: levels.get(key, 0) for key in FACILITIES}
        earned = {int(row["milestone_level"]) for row in db.execute(
            """SELECT milestone_level FROM ashfall_settlement_achievements
               WHERE haven_id=?""", (haven_id,)
        )}
        target = next((tier for tier in TIERS if tier not in earned), None)
        if target is None:
            reports.append({
                "haven_id": haven_id, "complete": True,
                "title": "Eternal Bastion", "target_level": None,
                "reached": len(FACILITIES), "total": len(FACILITIES),
                "remaining_levels": 0, "facilities": [],
            })
            continue
        facilities = [{
            "key": key, "level": levels[key],
            "required": target, "remaining": max(0, target - levels[key]),
            "ready": levels[key] >= target,
        } for key in FACILITIES]
        reports.append({
            "haven_id": haven_id, "complete": False,
            "title": CHRONICLE[target][0], "target_level": target,
            "reached": sum(item["ready"] for item in facilities),
            "total": len(FACILITIES),
            "remaining_levels": sum(item["remaining"] for item in facilities),
            "facilities": facilities,
        })
    reports.sort(key=lambda report: (
        report["complete"],
        report["remaining_levels"],
        report["haven_id"],
    ))
    return {
        "havens": reports,
        "haven_count": len(reports),
        "recommended_haven": next((report["haven_id"] for report in reports
                                   if not report["complete"]), None),
        "read_only": True,
    }
