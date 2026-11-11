"""NEXORA Nexus: persistent platform systems, separate from individual games."""
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

TITLES = [
    ("first-arrival", "First Arrival", 1),
    ("pathfinder", "Pathfinder", 2),
    ("vanguard", "Vanguard", 5),
    ("starborn", "Starborn", 10),
    ("legend", "Living Legend", 20),
]
MISSIONS = [
    ("first-signal", "First Signal", "Claim a daily transmission", "daily", 35, 12),
    ("spark-hunter", "Spark Hunter", "Earn 100 lifetime XP", "milestone", 65, 20),
    ("rising-star", "Rising Star", "Reach network level 3", "milestone", 100, 35),
    ("social-orbit", "Social Orbit", "Make your first friend", "milestone", 70, 25),
    ("the-long-climb", "The Long Climb", "Earn 1,000 lifetime XP", "legendary", 250, 100),
]
EVENTS = [
    ("Founders Era", "The opening chapter of NEXORA. Build your identity and earn your first achievements.", "FOUNDING EVENT"),
    ("Stellar Frontier", "The first playable world is in development. Follow its launch from the Worlds portal.", "COMING SOON"),
]
def install(app, db, get_user, valid_csrf, page_context, templates, ensure_progression, grant_progression, progression_snapshot, social_dashboard_data):
    def now():
        return datetime.now(timezone.utc).isoformat()
    def init():
        with db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS nexus_identity (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                equipped_title TEXT NOT NULL DEFAULT 'first-arrival',
                profile_frame TEXT NOT NULL DEFAULT 'origin',
                privacy_messages TEXT NOT NULL DEFAULT 'friends' CHECK(privacy_messages IN ('friends','off')),
                show_leaderboard INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS nexus_mission_claims (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                mission_key TEXT NOT NULL, period_key TEXT NOT NULL,
                claimed_at TEXT NOT NULL, PRIMARY KEY(user_id,mission_key,period_key)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS nexus_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 500),
                created_at TEXT NOT NULL
            )""")
            c.execute("CREATE INDEX IF NOT EXISTS nexus_messages_inbox ON nexus_messages(recipient_id,id DESC)")
            c.execute("""CREATE TABLE IF NOT EXISTS nexus_blocks (
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                blocked_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                PRIMARY KEY(user_id,blocked_id)
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS nexus_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reported_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                reason TEXT NOT NULL, created_at TEXT NOT NULL
            )""")
    init()
    def identity(user_id):
        with db() as c:
            c.execute("INSERT OR IGNORE INTO nexus_identity(user_id,updated_at) VALUES (?,?)",(user_id,now()))
            return dict(c.execute("SELECT * FROM nexus_identity WHERE user_id=?",(user_id,)).fetchone())
    def mission_status(user_id,progress,friend_count):
        today = datetime.now(timezone.utc).date().isoformat()
        with db() as c:
            claimed = {(r["mission_key"],r["period_key"]) for r in c.execute("SELECT mission_key,period_key FROM nexus_mission_claims WHERE user_id=?",(user_id,))}
        conditions = {
            "first-signal":progress["daily_claimed"],
            "spark-hunter":progress["lifetime_xp"] >= 100,
            "rising-star":progress["level"] >= 3,
            "social-orbit":friend_count >= 1,
            "the-long-climb":progress["lifetime_xp"] >= 1000,
        }
        result=[]
        for key,name,description,kind,xp,shards in MISSIONS:
            period=today if kind=="daily" else "lifetime"
            result.append(dict(key=key,name=name,description=description,kind=kind,xp=xp,shards=shards,
                               period=period,ready=conditions[key],claimed=(key,period) in claimed))
        return result
    def require_user(request):
        user=get_user(request.session.get("user_id"))
        if not user:
            return None
        ensure_progression(user["id"])
        return user
    async def verify(request):
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(400,"Security check expired. Reload and try again.")
        return form
    def redirect(section,notice="saved"):
        return RedirectResponse("/nexus?notice="+notice+"#"+section,status_code=303)
    @app.get("/nexus")
    async def nexus(request:Request):
        user=require_user(request)
        if not user:
            return RedirectResponse("/login",status_code=303)
        uid=user["id"]
        progress=progression_snapshot(uid)
        social=social_dashboard_data(uid)
        settings=identity(uid)
        missions=mission_status(uid,progress,social["friend_count"])
        with db() as c:
            rankings=[dict(r) for r in c.execute("""SELECT u.username,p.level,p.lifetime_xp,
                (SELECT COUNT(*) FROM player_achievements a WHERE a.user_id=u.id) AS medals
                FROM player_progress p JOIN users u ON u.id=p.user_id
                LEFT JOIN nexus_identity n ON n.user_id=u.id
                WHERE COALESCE(n.show_leaderboard,1)=1 ORDER BY p.lifetime_xp DESC,u.id LIMIT 20""")]
            inbox=[dict(r) for r in c.execute("""SELECT m.id,m.body,m.created_at,u.username AS sender
                FROM nexus_messages m JOIN users u ON u.id=m.sender_id
                WHERE m.recipient_id=? ORDER BY m.id DESC LIMIT 20""",(uid,))]
            sent=[dict(r) for r in c.execute("""SELECT m.body,m.created_at,u.username AS recipient
                FROM nexus_messages m JOIN users u ON u.id=m.recipient_id
                WHERE m.sender_id=? ORDER BY m.id DESC LIMIT 8""",(uid,))]
            chronicle=[dict(r) for r in c.execute("""SELECT source,xp_delta,shard_delta,created_at
                FROM progression_events WHERE user_id=? ORDER BY id DESC LIMIT 30""",(uid,))]
            medals=[dict(r) for r in c.execute("SELECT achievement_key,unlocked_at FROM player_achievements WHERE user_id=? ORDER BY unlocked_at DESC",(uid,))]
            friends=[dict(r) for r in c.execute("""SELECT u.id,u.username FROM player_friends f JOIN users u
                ON u.id=CASE WHEN f.requester_id=? THEN f.addressee_id ELSE f.requester_id END
                WHERE f.status='accepted' AND (f.requester_id=? OR f.addressee_id=?) ORDER BY u.username""",(uid,uid,uid))]
            blocked={r[0] for r in c.execute("SELECT blocked_id FROM nexus_blocks WHERE user_id=?",(uid,))}
        unlocked_titles=[dict(key=k,name=n,level=l,unlocked=progress["level"]>=l) for k,n,l in TITLES]
        season={"name":"CHAPTER ZERO — ORIGIN","description":"The founding era of NEXORA. A permanent record of your first steps.","status":"FOUNDING CHAPTER"}
        return templates.TemplateResponse(request=request,name="nexus.html",context=page_context(
            request,progress=progress,settings=settings,missions=missions,rankings=rankings,
            inbox=inbox,sent=sent,chronicle=chronicle,medals=medals,friends=friends,blocked=blocked,
            titles=unlocked_titles,events=EVENTS,season=season,notice=request.query_params.get("notice",""),
            account_id=f"NX-{uid:06d}"))
    @app.post("/nexus/missions/{mission_key}")
    async def claim_mission(request:Request,mission_key:str):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        await verify(request)
        progress=progression_snapshot(user["id"])
        friends=social_dashboard_data(user["id"])["friend_count"]
        item=next((m for m in mission_status(user["id"],progress,friends) if m["key"]==mission_key),None)
        if not item or not item["ready"] or item["claimed"]:
            return redirect("operations","unavailable")
        with db() as c:
            inserted=c.execute("""INSERT OR IGNORE INTO nexus_mission_claims(user_id,mission_key,period_key,claimed_at)
                VALUES (?,?,?,?)""",(user["id"],item["key"],item["period"],now())).rowcount
            if inserted:
                grant_progression(c,user["id"],f"mission:{item['key']}:{item['period']}",f"Operation: {item['name']}",item["xp"],item["shards"])
        return redirect("operations","reward")
    @app.post("/nexus/identity")
    async def update_identity(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await verify(request)
        title=str(form.get("title","first-arrival"))
        frame=str(form.get("frame","origin"))
        if frame not in ("origin","nebula","aurora"):raise HTTPException(400,"Invalid frame")
        progress=progression_snapshot(user["id"])
        allowed={k for k,n,l in TITLES if progress["level"]>=l}
        if title not in allowed:raise HTTPException(400,"Title not unlocked")
        if frame=="nebula" and progress["level"]<3:raise HTTPException(400,"Frame not unlocked")
        if frame=="aurora" and progress["level"]<7:raise HTTPException(400,"Frame not unlocked")
        identity(user["id"])
        with db() as c:
            c.execute("UPDATE nexus_identity SET equipped_title=?,profile_frame=?,updated_at=? WHERE user_id=?",
                      (title,frame,now(),user["id"]))
        return redirect("identity")
    @app.post("/nexus/preferences")
    async def preferences(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await verify(request)
        privacy=str(form.get("messages","friends"))
        if privacy not in ("friends","off"):raise HTTPException(400,"Invalid preference")
        visible=1 if form.get("leaderboard")=="on" else 0
        identity(user["id"])
        with db() as c:
            c.execute("UPDATE nexus_identity SET privacy_messages=?,show_leaderboard=?,updated_at=? WHERE user_id=?",
                      (privacy,visible,now(),user["id"]))
        return redirect("security")
    @app.post("/nexus/messages")
    async def send_message(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await verify(request)
        try:recipient=int(form.get("recipient","0"))
        except (ValueError,TypeError):raise HTTPException(400,"Invalid recipient")
        body=str(form.get("body","")).strip()
        if not 1<=len(body)<=500:raise HTTPException(400,"Message must be 1–500 characters")
        if recipient==user["id"]:raise HTTPException(400,"Cannot message yourself")
        with db() as c:
            friend=c.execute("""SELECT 1 FROM player_friends WHERE status='accepted' AND
                ((requester_id=? AND addressee_id=?) OR (requester_id=? AND addressee_id=?))""",
                (user["id"],recipient,recipient,user["id"])).fetchone()
            blocked=c.execute("""SELECT 1 FROM nexus_blocks WHERE
                (user_id=? AND blocked_id=?) OR (user_id=? AND blocked_id=?)""",
                (user["id"],recipient,recipient,user["id"])).fetchone()
            recipient_settings=c.execute("SELECT privacy_messages FROM nexus_identity WHERE user_id=?",(recipient,)).fetchone()
            if not friend or blocked or (recipient_settings and recipient_settings["privacy_messages"]=="off"):
                raise HTTPException(403,"Messaging is unavailable for this player")
            c.execute("INSERT INTO nexus_messages(sender_id,recipient_id,body,created_at) VALUES (?,?,?,?)",
                      (user["id"],recipient,body,now()))
            c.execute("""INSERT INTO player_notifications(user_id,actor_id,kind,message,target_url,created_at)
                VALUES (?,?,'message',?,'/nexus#comms',?)""",
                (recipient,user["id"],"New message from "+user["username"],now()))
        return redirect("comms","sent")
    @app.post("/nexus/block/{target_id}")
    async def block_player(request:Request,target_id:int):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        await verify(request)
        if target_id==user["id"]:raise HTTPException(400,"Invalid player")
        with db() as c:
            if not c.execute("SELECT 1 FROM users WHERE id=?",(target_id,)).fetchone():raise HTTPException(404,"Player not found")
            c.execute("INSERT OR IGNORE INTO nexus_blocks(user_id,blocked_id) VALUES (?,?)",(user["id"],target_id))
        return redirect("comms","blocked")
    @app.post("/nexus/report/{target_id}")
    async def report_player(request:Request,target_id:int):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await verify(request)
        reason=str(form.get("reason","")).strip()[:500]
        if len(reason)<10 or target_id==user["id"]:raise HTTPException(400,"Provide at least 10 characters")
        with db() as c:
            if not c.execute("SELECT 1 FROM users WHERE id=?",(target_id,)).fetchone():raise HTTPException(404,"Player not found")
            c.execute("INSERT INTO nexus_reports(reporter_id,reported_id,reason,created_at) VALUES (?,?,?,?)",
                      (user["id"],target_id,reason,now()))
        return redirect("comms","reported")
