"""Only loopback inference; no redirects, proxies or remote model downloads."""
import http.client
import json
import threading
import time

class Cancelled(Exception): pass

def complete(prompt, cancel, limit=600):
    connection = http.client.HTTPConnection('127.0.0.1',50081,timeout=180)
    result = {}
    done = threading.Event()
    def request():
        try:
            body = {'messages':[{'role':'user','content':prompt}], 'temperature':0,
                    'top_k':1,'seed':42,'max_tokens':limit,'stream':False,
                    'chat_template_kwargs':{'enable_thinking':False}}
            connection.request('POST','/v1/chat/completions',json.dumps(body),{'Content-Type':'application/json'})
            response = connection.getresponse()
            data = response.read(4_000_000)
            if response.status != 200:
                raise RuntimeError('모델 서버가 요청을 처리하지 못했습니다: HTTP '+str(response.status))
            result['text'] = json.loads(data)['choices'][0]['message']['content']
        except Exception as error:
            result['error'] = error
        finally:
            connection.close()
            done.set()
    threading.Thread(target=request,daemon=True).start()
    start = time.monotonic()
    while not done.wait(.1):
        if cancel.is_set() or time.monotonic()-start > 185:
            if connection.sock:
                try: connection.sock.shutdown(2)
                except OSError: pass
            connection.close()
            if cancel.is_set(): raise Cancelled()
            raise RuntimeError('모델 응답 시간이 초과되었습니다.')
    if cancel.is_set(): raise Cancelled()
    if 'error' in result: raise RuntimeError('모델 연결 실패: '+str(result['error']))
    return result['text']

def json_reply(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n',1)[1].rsplit('```',1)[0]
    return json.loads(text)
