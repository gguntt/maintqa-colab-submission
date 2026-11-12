import json
import sys
import threading
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from router import route,needs_rewrite
from retrieval import BM25,verify
from database import ident,validate_sql
from model import json_reply

class CoreTests(unittest.TestCase):
    def test_routing(self):
        for q in ['지난달 정비 몇 건','평균 수리 시간','정비 목록','부품 합계']: self.assertEqual(route(q),'aggregate')
        for q in ['펌프 고장 원인은','어떻게 조치하나요','정비 절차']: self.assertEqual(route(q),'procedure')
        self.assertTrue(needs_rewrite('그것은?'))
        self.assertFalse(needs_rewrite('주기관의 최근 정비 절차를 알려 주세요'))
    def test_bm25_and_no_evidence(self):
        records=[{'title':'pump','body':'replace mechanical seal','record':1},{'title':'coolant','body':'inspect coolant piping','record':2}]
        index=BM25(records)
        self.assertEqual(index.search('pump seal')[0]['title'],'pump')
        self.assertEqual(index.search('turbocharger'),[])
        self.assertEqual(index.search('pump'),index.search('pump'))
    def test_quote_matching_and_correction(self):
        rows=[{'record':1,'body':'Carefully inspect the pump before operation.'},{'record':2,'body':'Replace the damaged seal and inspect for leaks.'}]
        result=verify([{'record':1,'step':'unsupported claim','quote':'Replace the damaged seal'}],rows)
        self.assertEqual(result[0]['record'],2)
        self.assertEqual(result[0]['step'],'Replace the damaged seal')
        with self.assertRaises(ValueError): verify([{'quote':'Invented work instruction'}],rows)
        with self.assertRaises(ValueError): verify([],rows)
    def test_identifier_and_json(self):
        self.assertEqual(ident('DOC_NO'),'"DOC_NO"')
        with self.assertRaises(ValueError): ident('master;DROP TABLE master')
        self.assertEqual(json_reply('```json\n{"steps":[]}\n```'),{'steps':[]})
    def test_real_duckdb(self):
        try: import duckdb
        except ImportError: self.skipTest('DuckDB wheel unavailable locally')
        import tempfile
        import database
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/'test.duckdb')
            c=duckdb.connect(path);c.execute('create table master (value decimal(10,2))');c.execute('insert into master values (123.45),(67.89)');c.close()
            c=database.connect({'db_path':path})
            try:
                result=database.query(c,'SELECT sum(value) AS total FROM master',threading.Event())
                self.assertEqual(str(result['rows'][0][0]),'191.34')
                for sql in ['DELETE FROM master','SELECT 1;SELECT 2',"SELECT * FROM read_csv('C:/secret.csv')","COPY master TO 'C:/bad.csv'"]:
                    with self.assertRaises(Exception): database.query(c,sql,threading.Event())
                with self.assertRaises(Exception): c.execute('INSERT INTO master VALUES(1)')
            finally: c.close()

if __name__=='__main__': unittest.main()
