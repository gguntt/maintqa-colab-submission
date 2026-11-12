import sys,unittest,threading
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config,database
from engine import Engine
class PublicDemoTests(unittest.TestCase):
    def setUp(self):
        self.settings=config.read()
        if self.settings.get('dataset_id')!='public12': self.skipTest('Run create_public_demo.py first')
        self.con=database.connect(self.settings)
    def tearDown(self):
        if hasattr(self,'con'):self.con.close()
    def test_counts_and_keys(self):
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM master').fetchone()[0],12)
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM pms').fetchone()[0],24)
        self.assertEqual(self.con.execute('SELECT COUNT(DISTINCT DOC_NO) FROM master').fetchone()[0],2)
        self.assertEqual(self.con.execute('SELECT COUNT(*) FROM (SELECT DISTINCT VESSELCODE,DOC_NO FROM master)').fetchone()[0],12)
    def test_source_join_and_retrieval(self):
        records=Engine().index(self.settings).search('training pump inspection')
        self.assertEqual(len(records),4)
        self.assertIn('pump',records[0]['title'])
        for r in records:
            sources=database.sources(self.con,self.settings,r)
            self.assertEqual(len(sources),2)
            self.assertTrue(all(s['VESSELCODE']==r['vessel'] and s['DOC_NO']==r['document'] for s in sources))
    def test_readonly(self):
        with self.assertRaises(Exception):self.con.execute('DELETE FROM master')
        with self.assertRaises(Exception):database.query(self.con,"SELECT * FROM read_csv('secret.csv')",threading.Event())
if __name__=='__main__':unittest.main()
