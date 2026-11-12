import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import config
import engine
from model import Cancelled

def job(question):
    return {'id':'test','question':question,'history':[],'status':'queued','stages':[],'cancel':threading.Event()}

class PipelineTests(unittest.TestCase):
    def test_aggregate_does_not_rewrite_numbers(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(config,'ROOT',Path(temp)):
            root=Path(temp)
            for name in ['dictionary.json','rules.json','fewshots.json']: (root/name).write_text('["fixture"]')
            item=job('주기관의 정비는 몇 건인가요')
            expected={'columns':['count'],'rows':[['9007199254740993']],'received':1,'truncated':False,'capped':False}
            with patch('engine.database.connect',return_value=MagicMock()),patch('engine.database.catalog',return_value='DDL'),patch('engine.database.validate_sql'),patch('engine.database.query',return_value=expected),patch('engine.complete',return_value='SELECT count(*) FROM master') as model:
                engine.Engine().run(item,{'assets_path':temp})
                self.assertEqual(item['status'],'done')
                self.assertEqual(item['result']['rows'][0][0],'9007199254740993')
                self.assertEqual(model.call_count,1)
                self.assertTrue(list((root/'logs').glob('*.csv')))
    def test_cancel_before_processing_is_logged(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(config,'ROOT',Path(temp)):
            item=job('주기관의 정비는 몇 건인가요');item['cancel'].set()
            with patch('engine.complete') as model:
                engine.Engine().run(item,{})
                self.assertEqual(item['status'],'cancelled');model.assert_not_called()
            self.assertIn('cancelled',next((Path(temp)/'logs').glob('*.csv')).read_text('utf-8-sig'))
    def test_missing_database_abstains(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(config,'ROOT',Path(temp)):
            item=job('주기관의 정비는 몇 건인가요')
            with patch('engine.complete') as model:
                engine.Engine().run(item,{'db_path':''})
                self.assertEqual(item['status'],'abstained')
                self.assertIn('DB가 없습니다',item['answer']);model.assert_not_called()
    def test_model_sampling_and_cancel(self):
        import model
        connection=MagicMock();response=MagicMock()
        response.status=200;response.read.return_value=json.dumps({'choices':[{'message':{'content':'answer'}}]}).encode()
        connection.getresponse.return_value=response
        with patch('model.http.client.HTTPConnection',return_value=connection):
            self.assertEqual(model.complete('question',threading.Event()),'answer')
            payload=json.loads(connection.request.call_args.args[2])
            self.assertEqual((payload['temperature'],payload['top_k'],payload['seed']),(0,1,42))
            cancel=threading.Event();cancel.set()
            with self.assertRaises(Cancelled): model.complete('question',cancel)

if __name__=='__main__': unittest.main()
