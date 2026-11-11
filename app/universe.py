"""NEXORA Universe expansion. Independent platform systems, no game-engine coupling."""
from datetime import datetime, timezone, timedelta
import sqlite3
import hmac
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

TITLES=[
 ("first-arrival","First Arrival",0),("pathfinder","Pathfinder",100),
 ("rising-star","Rising Star",500),("starbound","Starbound",1000),
 ("legend","Living Legend",2000),("celestial","Celestial Vanguard",5000),
 ("eternal","The Eternal",10000),("mythic","Mythic Architect",25000)]
FRAMES=[("standard","Founder's Standard",0),("violet","Violet Signal",100),
 ("cyan","Cyan Pulse",500),("aurora","Aurora Vanguard",2000),("mythic","Mythic Halo",10000)]
MISSIONS=[
 ("daily-signal","Daily Signal","Claim your daily transmission", "daily",1,30,10),
 ("first-steps","First Steps","Earn 100 lifetime XP", "lifetime",100,60,20),
 ("rising-legend","Rising Legend","Earn 500 lifetime XP", "lifetime",500,120,40),
 ("weekly-pulse","Weekly Pulse","Claim 3 daily transmissions this week", "weekly",3,90,30),
 ("daily-operator","Daily Operator","Claim your daily transmission", "daily",1,15,5),
 ("weekend-voyage","Weekly Voyager","Claim 5 daily transmissions this week", "weekly",5,125,45),
 ("veteran-path","Veteran Path","Earn 1,000 lifetime XP", "lifetime",1000,200,75),
 ("celestial-call","Celestial Call","Earn 2,000 lifetime XP", "lifetime",2000,300,100),
 ("mythic-journey","Mythic Journey","Earn 5,000 lifetime XP", "lifetime",5000,500,150),
]
SEASONS=[{"name":"Genesis Chronicle","description":"The first chapter of NEXORA. Every founding player is part of its history.","status":"FOUNDING ERA"}]
EVENTS=[{"name":"The First Arrival","description":"Create your NEXORA identity and claim your first medal.","status":"ONGOING"}]

def register_universe(app, database, get_user, page_context, templates, progression_snapshot, grant_progression, ensure_progression, valid_csrf, password_hasher):
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS universe_identity (
          user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          equipped_title TEXT NOT NULL DEFAULT 'first-arrival',
          equipped_frame TEXT NOT NULL DEFAULT 'standard',
          showcase TEXT NOT NULL DEFAULT '',
          message_privacy TEXT NOT NULL DEFAULT 'friends' CHECK(message_privacy IN ('friends','none')),
          updated_at TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS universe_inventory (
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          item_key TEXT NOT NULL, item_type TEXT NOT NULL,
          acquired_at TEXT NOT NULL, PRIMARY KEY(user_id,item_key))""")
        db.execute("""CREATE TABLE IF NOT EXISTS universe_mission_claims (
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          mission_key TEXT NOT NULL, period_key TEXT NOT NULL,
          claimed_at TEXT NOT NULL, PRIMARY KEY(user_id,mission_key,period_key))""")
        db.execute("""CREATE TABLE IF NOT EXISTS universe_messages (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          recipient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          body TEXT NOT NULL CHECK(length(body) <= 1000),
          created_at TEXT NOT NULL, read_at TEXT)""")
        db.execute("CREATE INDEX IF NOT EXISTS universe_msg_inbox ON universe_messages(recipient_id,created_at)")
        db.execute("""CREATE TABLE IF NOT EXISTS universe_chronicle (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(user_id,kind,detail))""")

    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS universe_notification_preferences (
          user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
          social_enabled INTEGER NOT NULL DEFAULT 1,
          messages_enabled INTEGER NOT NULL DEFAULT 1)""")
        db.execute("""CREATE TABLE IF NOT EXISTS universe_blocked_players (
          blocker_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          blocked_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL,
          PRIMARY KEY(blocker_id,blocked_id))""")

    def require_user(request):
        user=get_user(request.session.get("user_id"))
        if not user: return None
        return user

    def identity(db, uid):
        now=datetime.now(timezone.utc).isoformat()
        db.execute("INSERT OR IGNORE INTO universe_identity (user_id,updated_at) VALUES (?,?)",(uid,now))
        return dict(db.execute("SELECT * FROM universe_identity WHERE user_id=?",(uid,)).fetchone())

    def period(mission, now):
        if mission[3]=="daily": return now.date().isoformat()
        if mission[3]=="weekly": return now.strftime("%G-W%V")
        return "once"

    def mission_progress(db,uid,mission,now,progress):
        kind=mission[3]
        if kind=="daily":
            count=db.execute("SELECT COUNT(*) FROM daily_claims WHERE user_id=? AND claim_date=?",(uid,now.date().isoformat())).fetchone()[0]
        elif kind=="weekly":
            start=(now.date()-timedelta(days=now.weekday())).isoformat()
            count=db.execute("SELECT COUNT(*) FROM daily_claims WHERE user_id=? AND claim_date>=?",(uid,start)).fetchone()[0]
        else: count=progress["lifetime_xp"]
        return min(count,mission[4])

    @app.get("/universe",name="universe")
    async def universe_page(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        uid=user["id"];now=datetime.now(timezone.utc)
        progress=progression_snapshot(uid)
        with database() as db:
            ident=identity(db,uid)
            owned={r["item_key"] for r in db.execute("SELECT item_key FROM universe_inventory WHERE user_id=?",(uid,))}
            unlocked={key for key,name,xp in TITLES if progress["lifetime_xp"]>=xp}
            unlocked.add("first-arrival")
            frames=[dict(key=key,name=name,xp=xp,unlocked=progress["lifetime_xp"]>=xp) for key,name,xp in FRAMES]
            badges=[dict(key=m["key"],name=m["name"],rarity=m["rarity"],unlocked=bool(m["unlocked_at"]),icon=m["icon"]) for m in progress["achievements"]]
            missions=[]
            for m in MISSIONS:
                done=bool(db.execute("SELECT 1 FROM universe_mission_claims WHERE user_id=? AND mission_key=? AND period_key=?",(uid,m[0],period(m,now))).fetchone())
                missions.append(dict(key=m[0],name=m[1],description=m[2],kind=m[3],target=m[4],current=mission_progress(db,uid,m,now,progress),xp=m[5],shards=m[6],claimed=done))
            leaders=[dict(r) for r in db.execute("""SELECT u.username,p.lifetime_xp,p.level,
              (SELECT COUNT(*) FROM player_achievements a WHERE a.user_id=u.id) AS medals
              FROM player_progress p JOIN users u ON u.id=p.user_id
              JOIN player_profiles pr ON pr.user_id=u.id
              WHERE pr.public_visibility='public' OR u.id=?
              ORDER BY p.lifetime_xp DESC,u.id ASC LIMIT 20""",(uid,))]
            ranked_by_xp=[dict(r) for r in db.execute("""SELECT u.username,p.lifetime_xp,p.level,
              (SELECT COUNT(*) FROM player_achievements a WHERE a.user_id=u.id) AS medals
              FROM player_progress p JOIN users u ON u.id=p.user_id
              JOIN player_profiles pr ON pr.user_id=u.id
              WHERE pr.public_visibility='public' OR u.id=?
              ORDER BY medals DESC,p.lifetime_xp DESC,u.id ASC LIMIT 20""",(uid,))]
            notifications=[dict(r) for r in db.execute("""SELECT id,kind,message,is_read,created_at,target_url
              FROM player_notifications WHERE user_id=? ORDER BY id DESC LIMIT 25""",(uid,))]
            unread_count=db.execute("SELECT COUNT(*) FROM player_notifications WHERE user_id=? AND is_read=0",(uid,)).fetchone()[0]
            inbox=[dict(r) for r in db.execute("""SELECT m.id,m.body,m.created_at,m.read_at,u.username AS sender
              FROM universe_messages m JOIN users u ON u.id=m.sender_id
              WHERE m.recipient_id=? ORDER BY m.id DESC LIMIT 20""",(uid,))]
            friends=[dict(r) for r in db.execute("""SELECT u.id,u.username FROM player_friends f
              JOIN users u ON u.id=CASE WHEN f.requester_id=? THEN f.addressee_id ELSE f.requester_id END
              WHERE f.status='accepted' AND (f.requester_id=? OR f.addressee_id=?)
              ORDER BY u.username LIMIT 100""",(uid,uid,uid))]
            history=[dict(r) for r in db.execute("""SELECT kind,detail,created_at FROM universe_chronicle
              WHERE user_id=? ORDER BY id DESC LIMIT 25""",(uid,))]
            ledger=[dict(r) for r in db.execute("""SELECT source,created_at,xp_delta,shard_delta FROM progression_events
              WHERE user_id=? ORDER BY id DESC LIMIT 12""",(uid,))]
            joined=db.execute("SELECT created_at FROM users WHERE id=?",(uid,)).fetchone()["created_at"]
            preferences=db.execute("SELECT social_enabled,messages_enabled FROM universe_notification_preferences WHERE user_id=?",(uid,)).fetchone()
            prefs=dict(preferences) if preferences else {"social_enabled":1,"messages_enabled":1}
            blocked=[dict(r) for r in db.execute("""SELECT u.id,u.username FROM universe_blocked_players b
              JOIN users u ON u.id=b.blocked_id WHERE b.blocker_id=? ORDER BY u.username""",(uid,))]
        return templates.TemplateResponse(request=request,name="universe.html",context=page_context(request,
          identity=ident,progress=progress,missions=missions,titles=TITLES,unlocked=unlocked,owned=owned,
          leaders=leaders,inbox=inbox,friends=friends,history=history,ledger=ledger,
          seasons=SEASONS,events=EVENTS,joined=joined,notice=request.query_params.get("notice","")[:60],
          frames=frames,badges=badges,medal_leaders=ranked_by_xp,notifications=notifications,
          unread_count=unread_count,preferences=prefs,blocked=blocked))

    async def secure_form(request):
        form=await request.form()
        if not valid_csrf(request,str(form.get("csrf_token",""))):
            raise HTTPException(status_code=400,detail="Security check expired. Reload and try again.")
        return form

    @app.post("/universe/mission/{mission_key}")
    async def claim_mission(request:Request,mission_key:str):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        await secure_form(request)
        mission=next((m for m in MISSIONS if m[0]==mission_key),None)
        if not mission:raise HTTPException(status_code=404)
        uid=user["id"];now=datetime.now(timezone.utc);progress=progression_snapshot(uid)
        with database() as db:
            if mission_progress(db,uid,mission,now,progress)<mission[4]:
                raise HTTPException(status_code=400,detail="Mission is not complete.")
            key=period(mission,now)
            inserted=db.execute("""INSERT OR IGNORE INTO universe_mission_claims
              (user_id,mission_key,period_key,claimed_at) VALUES (?,?,?,?)""",
              (uid,mission_key,key,now.isoformat())).rowcount
            if inserted:
                grant_progression(db,uid,f"mission:{mission_key}:{key}",f"Operation: {mission[1]}",mission[5],mission[6],now.isoformat())
                db.execute("INSERT OR IGNORE INTO universe_chronicle(user_id,kind,detail,created_at) VALUES (?,?,?,?)",
                  (uid,"OPERATION",f"Completed {mission[1]}",now.isoformat()))
        return RedirectResponse("/universe?notice=Mission+reward+claimed#operations",status_code=303)

    @app.post("/universe/identity")
    async def save_identity(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await secure_form(request)
        title=str(form.get("title","first-arrival"))
        frame=str(form.get("frame","standard"))
        showcase=str(form.get("showcase",""))[:60]
        privacy=str(form.get("message_privacy","friends"))
        progress=progression_snapshot(user["id"])
        available={k for k,n,xp in TITLES if progress["lifetime_xp"]>=xp}
        available_frames={k for k,n,xp in FRAMES if progress["lifetime_xp"]>=xp}
        if title not in available or frame not in available_frames or privacy not in {"friends","none"}:
            raise HTTPException(status_code=400,detail="Invalid identity selection.")
        with database() as db:
            identity(db,user["id"])
            db.execute("""UPDATE universe_identity SET equipped_title=?,equipped_frame=?,showcase=?,message_privacy=?,updated_at=?
              WHERE user_id=?""",(title,frame,showcase,privacy,datetime.now(timezone.utc).isoformat(),user["id"]))
        return RedirectResponse("/universe?notice=Identity+saved#identity",status_code=303)

    @app.post("/universe/message")
    async def send_message(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await secure_form(request)
        try:target=int(form.get("recipient_id",0))
        except (TypeError,ValueError):raise HTTPException(status_code=400,detail="Invalid recipient")
        body=str(form.get("body","")).strip()
        if not 1<=len(body)<=1000 or target==user["id"]:
            raise HTTPException(status_code=400,detail="Message must contain 1–1000 characters.")
        with database() as db:
            allowed=db.execute("""SELECT 1 FROM player_friends WHERE status='accepted'
              AND ((requester_id=? AND addressee_id=?) OR (requester_id=? AND addressee_id=?))""",
              (user["id"],target,target,user["id"])).fetchone()
            if not allowed:raise HTTPException(status_code=403,detail="Messages are available between friends only.")
            blocked=db.execute("""SELECT 1 FROM universe_blocked_players
              WHERE (blocker_id=? AND blocked_id=?) OR (blocker_id=? AND blocked_id=?)""",
              (user["id"],target,target,user["id"])).fetchone()
            if blocked:raise HTTPException(status_code=403,detail="Messaging is unavailable between these players.")
            recipient=identity(db,target)
            if recipient["message_privacy"]=="none":raise HTTPException(status_code=403,detail="This player is not accepting messages.")
            now=datetime.now(timezone.utc).isoformat()
            db.execute("INSERT INTO universe_messages(sender_id,recipient_id,body,created_at) VALUES (?,?,?,?)",
              (user["id"],target,body,now))
            pref=db.execute("SELECT messages_enabled FROM universe_notification_preferences WHERE user_id=?",(target,)).fetchone()
            if not pref or pref["messages_enabled"]:
                db.execute("""INSERT INTO player_notifications(user_id,actor_id,kind,message,target_url,created_at)
                  VALUES (?,?,?,?,?,?)""",(target,user["id"],"message",f"New message from {user['username']}.","/universe#comms",now))
        return RedirectResponse("/universe?notice=Message+sent#comms",status_code=303)


    @app.post("/universe/notifications/read")
    async def read_notifications(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        await secure_form(request)
        with database() as db:
            db.execute("UPDATE player_notifications SET is_read=1 WHERE user_id=? AND is_read=0",(user["id"],))
        return RedirectResponse("/universe?notice=Notifications+cleared#notifications",status_code=303)

    @app.post("/universe/notifications/preferences")
    async def notification_preferences(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await secure_form(request)
        social=1 if str(form.get("social_enabled",""))=="on" else 0
        messages=1 if str(form.get("messages_enabled",""))=="on" else 0
        with database() as db:
            db.execute("""INSERT INTO universe_notification_preferences(user_id,social_enabled,messages_enabled)
              VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET
              social_enabled=excluded.social_enabled,messages_enabled=excluded.messages_enabled""",
              (user["id"],social,messages))
        return RedirectResponse("/universe?notice=Preferences+saved#notifications",status_code=303)

    @app.post("/universe/block")
    async def block_player(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await secure_form(request)
        try:target=int(form.get("player_id","0"))
        except (TypeError,ValueError):raise HTTPException(status_code=400,detail="Invalid player.")
        action=str(form.get("action","block"))
        if action not in {"block","unblock"} or target==user["id"]:
            raise HTTPException(status_code=400,detail="Invalid block action.")
        with database() as db:
            if action=="block":
                existing=db.execute("SELECT 1 FROM users WHERE id=?",(target,)).fetchone()
                if not existing:raise HTTPException(status_code=404,detail="Player not found.")
                db.execute("INSERT OR IGNORE INTO universe_blocked_players(blocker_id,blocked_id,created_at) VALUES (?,?,?)",
                  (user["id"],target,datetime.now(timezone.utc).isoformat()))
            else:
                db.execute("DELETE FROM universe_blocked_players WHERE blocker_id=? AND blocked_id=?",(user["id"],target))
        return RedirectResponse("/universe?notice=Player+settings+updated#comms",status_code=303)

    @app.post("/universe/password")
    async def change_password(request:Request):
        user=require_user(request)
        if not user:return RedirectResponse("/login",status_code=303)
        form=await secure_form(request)
        old=str(form.get("current_password",""))
        new=str(form.get("new_password",""))
        if not 12<=len(new)<=128:raise HTTPException(status_code=400,detail="New password must contain 12–128 characters.")
        with database() as db:
            row=db.execute("SELECT password_hash FROM users WHERE id=?",(user["id"],)).fetchone()
            try:valid=password_hasher.verify(row["password_hash"],old)
            except Exception:valid=False
            if not valid:raise HTTPException(status_code=403,detail="Current password is incorrect.")
            db.execute("UPDATE users SET password_hash=? WHERE id=?",(password_hasher.hash(new),user["id"]))
        request.session.clear()
        return RedirectResponse("/login",status_code=303)
