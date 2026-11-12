"""ASHFALL 8.1 — authenticated Grand Arsenal APIs and inventory page."""
import json
import time
from fastapi import HTTPException,Request
from fastapi.responses import HTMLResponse,RedirectResponse
from app import ashfall_grand_arsenal as arsenal

def register_grand_arsenal(app,database,get_user,valid_csrf,base_dir,csrf_token):
 with database() as db:arsenal.initialize(db)
 def haven(db,request,state):
  user=get_user(request.session.get("user_id"))
  if not user:raise HTTPException(401,"Sign in required")
  row=db.execute("SELECT id FROM ashfall_havens WHERE user_id=? AND state_id=?",
                 (user["id"],state)).fetchone()
  if not row:raise HTTPException(404,"Haven not found")
  return row[0]
 @app.get("/ashfall/arsenal",response_class=HTMLResponse)
 async def arsenal_page(request:Request):
  if not get_user(request.session.get("user_id")):
   return RedirectResponse("/login",status_code=303)
  html=(base_dir/"ashfall_arsenal.html").read_text(encoding="utf-8")
  return HTMLResponse(html.replace("__CSRF_JSON__",json.dumps(csrf_token(request))))
 @app.get("/ashfall/api/arsenal")
 async def arsenal_status(request:Request,state_id:int=1,category:str="",offset:int=0):
  with database() as db:
   hid=haven(db,request,state_id)
   result=arsenal.inventory(db,hid,category or None,50,offset)
   result["categories"]=arsenal.CATEGORIES
   return result
 @app.get("/ashfall/api/arsenal/catalog")
 async def arsenal_catalog(request:Request,category:str="hero_gear",search:str="",offset:int=0):
  if not get_user(request.session.get("user_id")):raise HTTPException(401,"Sign in required")
  if category not in arsenal.CATEGORIES:raise HTTPException(400,"Unknown category")
  if offset<0:raise HTTPException(400,"Invalid offset")
  query=search.strip().lower()[:70]
  matches=[item for item in arsenal.CATALOG.values()
           if item["category"]==category and (not query or query in item["name"].lower())]
  return {"total":len(matches),"offset":offset,"items":matches[offset:offset+50]}
 @app.post("/ashfall/api/arsenal/action")
 async def arsenal_action(request:Request):
  form=await request.form()
  if not valid_csrf(request,str(form.get("csrf_token",""))):
   raise HTTPException(400,"Invalid security token")
  try:state=int(form.get("state_id","1"))
  except (ValueError,TypeError):raise HTTPException(400,"Invalid state")
  action=str(form.get("action",""))
  if action not in ("craft","enhance","equip"):raise HTTPException(400,"Unknown arsenal action")
  with database() as db:
   db.execute("BEGIN IMMEDIATE")
   hid=haven(db,request,state)
   if action=="craft":
    result=arsenal.craft(db,hid,str(form.get("item_id","")),time.time())
   else:
    try:instance=int(form.get("instance_id","0"))
    except (ValueError,TypeError):raise HTTPException(400,"Invalid equipment")
    if action=="enhance":result=arsenal.enhance(db,hid,instance)
    else:
     target=str(form.get("target",""))
     if target.startswith("hero:"):
      parts=target.split(":")
      if len(parts)!=3:raise HTTPException(400,"Invalid hero target")
      from app.ashfall_hero_generations import CATALOG
      if parts[1] not in CATALOG:raise HTTPException(400,"Unknown hero")
      if not db.execute("SELECT 1 FROM ashfall_heroes WHERE haven_id=? AND hero_key=?",
                        (hid,parts[1])).fetchone():
       raise HTTPException(409,"Recruit hero before equipping")
     elif not target.startswith("chief:"):raise HTTPException(400,"Invalid equipment target")
     result=arsenal.equip(db,hid,instance,target)
   return {"result":result,"inventory":arsenal.inventory(db,hid)}
