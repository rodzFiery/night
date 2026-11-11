"""ASHFALL 2.0: realistic SQLite multiplayer race and rollback tests.

Run: python -m unittest discover -s tests -p test_ashfall_concurrency.py -v
These tests use temporary databases only, never a player's save.
"""
import os
import sqlite3
import tempfile
from contextlib import contextmanager
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from app.ashfall_alliances import initialize as alliance_init, upgrade_schema
from app.ashfall_alliance_progress import initialize as progress_init

class MultiplayerTransactions(unittest.TestCase):
 def setUp(self):
  fd,self.path=tempfile.mkstemp(prefix="ashfall-race-",suffix=".db")
  os.close(fd)
  with self.connect() as db:
   db.execute("CREATE TABLE users(id INTEGER PRIMARY KEY)")
   db.execute("CREATE TABLE ashfall_states(id INTEGER PRIMARY KEY)")
   db.execute("""CREATE TABLE ashfall_havens(
    id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),
    state_id INTEGER REFERENCES ashfall_states(id),name TEXT,
    command_center_level INTEGER DEFAULT 1)""")
   db.execute("""CREATE TABLE ashfall_resource_balances(
    haven_id INTEGER PRIMARY KEY REFERENCES ashfall_havens(id),
    food INTEGER NOT NULL DEFAULT 0 CHECK(food>=0),
    wood INTEGER NOT NULL DEFAULT 0 CHECK(wood>=0),
    metal INTEGER NOT NULL DEFAULT 0 CHECK(metal>=0),
    gas INTEGER NOT NULL DEFAULT 0 CHECK(gas>=0))""")
   alliance_init(db)
   upgrade_schema(db)
   progress_init(db)
   db.execute("INSERT INTO ashfall_states(id) VALUES(1)")
   db.executemany("INSERT INTO users(id) VALUES(?)",[(1,),(2,)])
   db.executemany("INSERT INTO ashfall_havens(id,user_id,state_id,name) VALUES(?,?,1,?)",[(1,1,"North"),(2,2,"South")])
   db.executemany("INSERT INTO ashfall_resource_balances(haven_id,food) VALUES(?,100)",[(1,),(2,)])
   db.execute("INSERT INTO ashfall_alliances(state_id,name,tag,leader_haven_id,created_at) VALUES(1,'Wardens','WRD',1,0)")
   db.executemany("INSERT INTO ashfall_alliance_members(haven_id,alliance_id,role,joined_at) VALUES(?,1,'member',0)",[(1,),(2,)])
 @contextmanager
 def connect(self):
  db=sqlite3.connect(self.path,timeout=10)
  try:
   db.row_factory=sqlite3.Row
   db.execute("PRAGMA foreign_keys=ON")
   db.execute("PRAGMA busy_timeout=10000")
   try:
    yield db
   except BaseException:
    db.rollback()
    raise
   else:
    db.commit()
  finally:
   db.close()
 def tearDown(self):
  os.unlink(self.path)
 def donate(self,hid,amount,barrier):
  barrier.wait()
  with self.connect() as db:
   db.execute("BEGIN IMMEDIATE")
   db.execute("INSERT OR IGNORE INTO ashfall_alliance_projects(alliance_id,project_key,contributed) VALUES(1,'supply_network',0)")
   progress=db.execute("SELECT contributed FROM ashfall_alliance_projects WHERE alliance_id=1 AND project_key='supply_network'").fetchone()["contributed"]
   if progress+amount>150:return False
   debit=db.execute("UPDATE ashfall_resource_balances SET food=food-? WHERE haven_id=? AND food>=?",(amount,hid,amount))
   if debit.rowcount!=1:return False
   db.execute("INSERT INTO ashfall_alliance_contributions(alliance_id,haven_id,project_key,resource,amount,created_at) VALUES(1,?,'supply_network','food',?,1000)",(hid,amount))
   db.execute("UPDATE ashfall_alliance_projects SET contributed=contributed+? WHERE alliance_id=1 AND project_key='supply_network'",(amount,))
   return True
 def test_simultaneous_donations_are_serialized(self):
  barrier=threading.Barrier(2)
  with ThreadPoolExecutor(max_workers=2) as pool:
   a=pool.submit(self.donate,1,100,barrier)
   b=pool.submit(self.donate,2,100,barrier)
   self.assertEqual(sorted([a.result(),b.result()]),[False,True])
  with self.connect() as db:
   self.assertEqual(db.execute("SELECT contributed FROM ashfall_alliance_projects").fetchone()[0],100)
   self.assertEqual(db.execute("SELECT SUM(amount) FROM ashfall_alliance_contributions").fetchone()[0],100)
   self.assertEqual(db.execute("SELECT SUM(food) FROM ashfall_resource_balances").fetchone()[0],100)
 def test_simultaneous_claims_only_one_wins(self):
  barrier=threading.Barrier(2)
  def claim():
   barrier.wait()
   with self.connect() as db:
    db.execute("BEGIN IMMEDIATE")
    inserted=db.execute("INSERT OR IGNORE INTO ashfall_alliance_project_claims(alliance_id,haven_id,project_key,claimed_at) VALUES(1,1,'supply_network',1000)")
    if inserted.rowcount:
     db.execute("UPDATE ashfall_resource_balances SET food=food+250 WHERE haven_id=1")
    return inserted.rowcount
  with ThreadPoolExecutor(max_workers=2) as pool:
   a=pool.submit(claim);b=pool.submit(claim)
   self.assertEqual(sorted([a.result(),b.result()]),[0,1])
  with self.connect() as db:
   self.assertEqual(db.execute("SELECT COUNT(*) FROM ashfall_alliance_project_claims").fetchone()[0],1)
   self.assertEqual(db.execute("SELECT food FROM ashfall_resource_balances WHERE haven_id=1").fetchone()[0],350)
 def test_failed_transaction_rolls_back_all_changes(self):
  try:
   with self.connect() as db:
    db.execute("BEGIN IMMEDIATE")
    db.execute("UPDATE ashfall_resource_balances SET food=food-60 WHERE haven_id=1")
    db.execute("INSERT INTO ashfall_alliance_contributions(alliance_id,haven_id,project_key,resource,amount,created_at) VALUES(1,1,'supply_network','food',60,1000)")
    raise RuntimeError("Simulated interrupted request")
  except RuntimeError:pass
  with self.connect() as db:
   self.assertEqual(db.execute("SELECT food FROM ashfall_resource_balances WHERE haven_id=1").fetchone()[0],100)
   self.assertEqual(db.execute("SELECT COUNT(*) FROM ashfall_alliance_contributions").fetchone()[0],0)

if __name__=="__main__":unittest.main()
