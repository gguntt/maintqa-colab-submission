"""Local-only HTTP server; one FIFO worker, independent cancellation and settings APIs."""
import hmac
import http.client
import json
import importlib.util
import queue
import secrets
import threading
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import config
from engine import Engine

TOKEN=secrets.token_urlsafe(32)
JOBS={}; QUEUE=queue.Queue(); ENGINE=Engine()
RUNTIME={'state':'starting','message':'모델 불러오는 중'}

def public(job): return {k:v for k,v in job.items() if k not in ('cancel','history')}

def worker():
    while True:
        job=QUEUE.get()
        try:
            ENGINE.run(job,config.read())
        except Exception as error:
            job['status']='abstained'
            job['answer']='설정 또는 기록 파일을 처리하지 못했습니다. 파일 권한과 남은 저장 공간을 확인하세요. '+str(error)
        finally: QUEUE.task_done()

def health_model():
    c=http.client.HTTPConnection('127.0.0.1',50081,timeout=1)
    try:
        c.request('GET','/health'); response=c.getresponse()
        return response.status==200
    except OSError: return False
    finally: c.close()

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,data,status=200,html=False):
        body=data.encode('utf-8') if html else json.dumps(data,ensure_ascii=False,default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','text/html; charset=utf-8' if html else 'application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError): pass
    def allowed(self):
        return self.headers.get('Host')=='127.0.0.1:8760' and self.headers.get('Origin','http://127.0.0.1:8760')=='http://127.0.0.1:8760'
    def do_GET(self):
        if not self.allowed(): return self.send({'error':'로컬 접속만 허용됩니다.'},403)
        if self.path=='/': return self.send((config.ROOT/'maintqa_web.html').read_text('utf-8').replace('__TOKEN__',TOKEN),html=True)
        if self.path=='/api/health':
            settings=config.read()
            db_exists=bool(settings['db_path']) and config.Path(settings['db_path']).is_file()
            return self.send({'app':'MaintQA','version':1,'runtime':RUNTIME,'model_ready':health_model(),
                             'db_ready':db_exists,'duckdb_ready':importlib.util.find_spec('duckdb') is not None})
        if not hmac.compare_digest(self.headers.get('X-MaintQA-Token',''),TOKEN): return self.send({'error':'접속을 다시 여세요.'},403)
        if self.path=='/api/settings': return self.send(config.read())
        if self.path=='/api/jobs': return self.send([public(j) for j in list(JOBS.values())])
        self.send({'error':'없는 경로입니다.'},404)
    def do_POST(self):
        if not self.allowed() or not hmac.compare_digest(self.headers.get('X-MaintQA-Token',''),TOKEN): return self.send({'error':'허용되지 않는 요청입니다.'},403)
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length>65536: raise ValueError('입력 내용이 너무 깁니다.')
            data=json.loads(self.rfile.read(length))
            if self.path=='/api/settings': return self.send(config.save(data))
            if self.path=='/api/jobs':
                question=str(data.get('question','')).strip()
                if not question or len(question)>4000: raise ValueError('질문은 1~4,000자로 입력하세요.')
                if QUEUE.qsize()>=20: raise ValueError('대기열이 가득 찼습니다. 처리 후 다시 입력하세요.')
                history=[]
                for jid in data.get('history',[])[-3:]:
                    old=JOBS.get(jid)
                    if old and old['status']=='done': history.append({'question':old.get('resolved_question',old['question']),'answer':old.get('answer'),'result':old.get('result'),'steps':old.get('steps')})
                job={'id':uuid.uuid4().hex,'question':question,'history':history,'status':'queued','stages':[],'cancel':threading.Event()}
                JOBS[job['id']]=job; QUEUE.put(job)
                return self.send(public(job),202)
            if self.path=='/api/cancel':
                job=JOBS.get(data.get('id'))
                if job: job['cancel'].set()
                return self.send({'ok':True})
            self.send({'error':'없는 경로입니다.'},404)
        except Exception as error: self.send({'error':str(error)},400)

def create_server():
    server=ThreadingHTTPServer(('127.0.0.1',8760),Handler)
    server.daemon_threads=True
    threading.Thread(target=worker,daemon=True).start()
    def preload():
        try: ENGINE.index(config.read())
        except Exception: pass
    threading.Thread(target=preload,daemon=True).start()
    return server

if __name__=='__main__':
    RUNTIME.update(state='ready',message='질의응답 서버 준비됨')
    create_server().serve_forever()
