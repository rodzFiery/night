"""ASHFALL 3.4 Expedition Chronicle persistence regression tests."""
import sqlite3
import unittest

class ChronicleTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.execute("""CREATE TABLE chronicle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            haven_id INTEGER NOT NULL,
            state_id INTEGER NOT NULL,
            sector_x INTEGER NOT NULL,
            sector_y INTEGER NOT NULL,
            started_at REAL NOT NULL,
            completed_at REAL NOT NULL,
            UNIQUE(haven_id,sector_x,sector_y))""")

    def tearDown(self):
        self.db.close()

    def test_duplicate_claim_is_idempotent(self):
        row=(1,1,4,5,100.0,300.0)
        self.db.execute("INSERT OR IGNORE INTO chronicle(haven_id,state_id,sector_x,sector_y,started_at,completed_at) VALUES(?,?,?,?,?,?)",row)
        self.db.execute("INSERT OR IGNORE INTO chronicle(haven_id,state_id,sector_x,sector_y,started_at,completed_at) VALUES(?,?,?,?,?,?)",row)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM chronicle").fetchone()[0],1)

    def test_haven_history_is_isolated(self):
        for haven in (1,2):
            self.db.execute("INSERT INTO chronicle(haven_id,state_id,sector_x,sector_y,started_at,completed_at) VALUES(?,?,?,?,?,?)",(haven,1,4,5,100.0,300.0))
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM chronicle WHERE haven_id=1").fetchone()[0],1)

    def test_recent_history_order(self):
        for i in range(4):
            self.db.execute("INSERT INTO chronicle(haven_id,state_id,sector_x,sector_y,started_at,completed_at) VALUES(?,?,?,?,?,?)",(1,1,i,0,100.0,200.0+i))
        rows=self.db.execute("SELECT sector_x FROM chronicle WHERE haven_id=1 ORDER BY completed_at DESC,id DESC LIMIT 2").fetchall()
        self.assertEqual([row[0] for row in rows],[3,2])

if __name__=="__main__":
    unittest.main()
