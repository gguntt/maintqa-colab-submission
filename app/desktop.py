"""Desktop lifecycle owner. Only processes started here are terminated."""
import atexit
import ctypes
import http.client
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import config

OWNED=[]
STOP=threading.Event()
SERVER=None

def probe(port,path):
    conn=http.client.HTTPConnection('127.0.0.1',port,timeout=1)
    try:
        conn.request('GET',path); response=conn.getresponse()
        data=response.read()
        return json.loads(data) if response.status==200 else None
    except Exception: return None
    finally: conn.close()

def cleanup():
    STOP.set()
    if SERVER:
        import maintqa_web
        for job in list(maintqa_web.JOBS.values()): job['cancel'].set()
        SERVER.shutdown(); SERVER.server_close()
    for process in reversed(OWNED):
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=6)
            except subprocess.TimeoutExpired: process.kill(); process.wait()

atexit.register(cleanup)

def prepare_model():
    import maintqa_web
    runtime=maintqa_web.RUNTIME
    try:
        if probe(50081,'/health'):
            runtime.update(state='ready',message='기존 모델 서버 연결됨'); return
        settings=config.read()
        for key,label in [('llama_server_path','llama-server 실행 파일'),('model_path','GGUF 모델 파일')]:
            if not settings[key] or not Path(settings[key]).is_file():
                raise ValueError(label+'을 찾을 수 없습니다. 설정에서 경로를 지정한 뒤 프로그램을 다시 켜세요.')
        runtime.update(state='starting',message='모델 불러오는 중 · gemma4:e2b')
        logs=config.ROOT/'logs'; logs.mkdir(exist_ok=True)
        with (logs/'llama-server.log').open('ab') as log:
            process=subprocess.Popen([settings['llama_server_path'],'--model',settings['model_path'],
                '--host','127.0.0.1','--port','50081','--ctx-size',str(settings['context_size']),
                '--parallel','1','--n-gpu-layers',str(settings['gpu_layers']),
                '--temp','0','--top-k','1','--seed','42'],
                stdout=log,stderr=log,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        OWNED.append(process)
        for _ in range(240):
            if STOP.wait(.5): return
            if process.poll() is not None: raise ValueError('모델 실행에 실패했습니다. logs/llama-server.log에서 원인을 확인하세요.')
            if probe(50081,'/health'):
                try:
                    import database
                    from engine import aggregate_prefix
                    from model import complete
                    con=database.connect(settings)
                    try: prefix=aggregate_prefix(settings,con)
                    finally: con.close()
                    runtime.update(state='starting',message='DB 프롬프트 준비 중 · 최초 1회 예열')
                    complete(prefix,STOP,1)
                except Exception:
                    # Missing business assets do not prevent opening the settings screen.
                    pass
                runtime.update(state='ready',message='모델 준비 완료 · 127.0.0.1 전용'); return
        raise ValueError('모델 준비 시간이 초과되었습니다. 모델 경로와 메모리를 확인하세요.')
    except Exception as error: runtime.update(state='error',message=str(error))

def main():
    global SERVER
    # A Windows mutex prevents two launchers from racing for process ownership.
    ctypes.windll.kernel32.CreateMutexW.restype=ctypes.c_void_p
    ctypes.windll.kernel32.CloseHandle.argtypes=[ctypes.c_void_p]
    mutex=ctypes.windll.kernel32.CreateMutexW(None,False,'Local\\MaintQA_Desktop_8760')
    if ctypes.windll.kernel32.GetLastError()==183:
        ctypes.windll.user32.MessageBoxW(None,'정비이력 도우미가 이미 실행 중입니다. 작업 표시줄에서 창을 선택하세요.','MaintQA',64)
        return
    existing=probe(8760,'/api/health')
    if existing and existing.get('app')!='MaintQA': raise RuntimeError('8760 포트를 다른 프로그램이 사용 중입니다.')
    if not existing:
        import maintqa_web
        SERVER=maintqa_web.create_server()
        threading.Thread(target=SERVER.serve_forever,daemon=True).start()
    threading.Thread(target=prepare_model,daemon=True).start()
    url='http://127.0.0.1:8760'
    sdk_candidates=[config.ROOT/'webview2',Path('C:/Program Files/Microsoft Office/root/Office16/ADDINS/Microsoft Power Query for Excel Integrated/bin'),Path('C:/Program Files (x86)/Sony/PS Remote Play')]
    sdk=next((p for p in sdk_candidates if (p/'Microsoft.Web.WebView2.WinForms.dll').is_file() and (p/'WebView2Loader.dll').is_file()),None)
    if sdk and (config.ROOT/'WebViewHost.exe').is_file():
        process=subprocess.Popen([str(config.ROOT/'WebViewHost.exe'),str(sdk)],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        OWNED.append(process)
        process.wait()
    else:
        try: import webview
        except ImportError: raise RuntimeError('WebView2 호스트 라이브러리가 없습니다. README의 오프라인 설치를 진행하세요.')
        webview.create_window('MaintQA · 선박 정비이력',url,width=1280,height=900,min_size=(820,600))
        webview.start(gui='edgechromium')
    cleanup()
    ctypes.windll.kernel32.CloseHandle(mutex)

if __name__=='__main__':
    try: main()
    except Exception as error:
        ctypes.windll.user32.MessageBoxW(None,str(error),'MaintQA · 실행 안내',16)
