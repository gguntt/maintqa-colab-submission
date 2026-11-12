import json
import os
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCK = threading.RLock()
DEFAULT = {
    'model_path': '', 'llama_server_path': '', 'db_path': '',
    'assets_path': str(ROOT / 'assets'), 'bilingual': False, 'theme': 'light',
    'record_table': 'master',
    'columns': {'id':'DOC_NO','vessel':'VESSELCODE','document':'DOC_NO',
                'equipment':'EQUIPMENT','date':'DATE','title':'TITLE','body':'DESCRIPTION'},
    'source_table':'pms', 'source_vessel':'VESSELCODE', 'source_document':'DOC_NO',
    'gpu_layers':99, 'context_size':8192,
    'dataset_id':'', 'demo_data':False, 'dataset_notice':''
}

def read():
    with LOCK:
        path = ROOT / 'settings.json'
        saved = json.loads(path.read_text('utf-8')) if path.exists() else {}
        return DEFAULT | saved

def save(values):
    with LOCK:
        data = read()
        for key, value in values.items():
            if key in DEFAULT:
                data[key] = value
        for key in ('model_path','llama_server_path','db_path','assets_path'):
            value = str(data[key])
            if value.startswith(('\\\\','//')) or '://' in value:
                raise ValueError('네트워크 경로는 사용할 수 없습니다. 이 PC의 파일을 선택하세요.')
        if data['theme'] not in ('light','dark') or not isinstance(data['columns'],dict):
            raise ValueError('설정 형식이 올바르지 않습니다.')
        temp = ROOT / 'settings.tmp'
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf-8')
        os.replace(temp, ROOT / 'settings.json')
        return data
