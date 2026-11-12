import re
import threading
from pathlib import Path

def ident(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name):
        raise ValueError('테이블·컬럼명에는 영문, 숫자, 밑줄만 사용할 수 있습니다.')
    return '"'+name+'"'

def connect(settings):
    path = Path(settings['db_path'])
    if not settings['db_path'] or not path.is_file():
        raise ValueError('정비이력 DB가 없습니다. 설정에서 DuckDB 파일을 지정하세요.')
    try: import duckdb
    except ImportError: raise ValueError('DuckDB 실행 모듈이 없습니다. README의 오프라인 설치를 진행하세요.')
    return duckdb.connect(str(path),read_only=True,config={'enable_external_access':'false','threads':'2','memory_limit':'1GB'})

def catalog(con):
    rows = con.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='main' ORDER BY table_name,ordinal_position").fetchall()
    tables = {}
    for table,col,typ in rows: tables.setdefault(table,[]).append(f'{ident(col)} {typ}')
    return '\n'.join(f'CREATE TABLE {ident(t)} ({", ".join(cols)});' for t,cols in tables.items())

def validate_sql(con,sql):
    # DuckDB parser supplies statement boundaries; external IO is also disabled at connection level.
    statements = con.extract_statements(sql)
    if len(statements)!=1 or str(statements[0].type).split('.')[-1]!='SELECT':
        raise ValueError('읽기 전용 SELECT 한 문장만 허용됩니다.')
    scrubbed = re.sub(r"'(?:''|[^'])*'", "''",sql)
    if re.search(r'--|/\*|\b(pragma|attach|detach|copy|install|load|call|export|import|read_csv|read_parquet|read_json|sqlite_scan|postgres_scan|query|query_table|glob|getenv)\b',scrubbed,re.I):
        raise ValueError('외부 접근 또는 허용되지 않는 SQL입니다.')
    return sql.strip().rstrip(';')

def query(con,sql,cancel):
    sql = validate_sql(con,sql)
    stopped = threading.Event()
    def watch():
        import time
        deadline=time.monotonic()+30
        while not stopped.wait(.05):
            if cancel.is_set() or time.monotonic()>deadline:
                con.interrupt()
                return
    threading.Thread(target=watch,daemon=True).start()
    try:
        cursor=con.execute('SELECT * FROM ('+sql+') AS maintqa_result LIMIT 2001')
        rows=cursor.fetchall()
        # JSON numbers can lose integer precision in JavaScript; preserve every DB value as text.
        return {'columns':[x[0] for x in cursor.description],'rows':[[None if v is None else str(v) for v in row] for row in rows[:50]],
                'received':min(len(rows),2000),'truncated':len(rows)>50,'capped':len(rows)>2000}
    finally: stopped.set()

def records(con,settings):
    cols=settings['columns']
    fields=['id','vessel','document','equipment','date','title','body']
    sql='SELECT '+','.join(ident(cols[k]) for k in fields)+' FROM '+ident(settings['record_table'])+' WHERE length(CAST('+ident(cols['body'])+' AS VARCHAR)) >= 300'
    return [dict(zip(fields,[str(x) if x is not None else '' for x in row])) for row in con.execute(sql).fetchall()]

def sources(con,settings,record):
    table=settings.get('source_table')
    if not table: return []
    cursor=con.execute('SELECT * FROM '+ident(table)+' WHERE CAST('+ident(settings['source_vessel'])+' AS VARCHAR)=? AND CAST('+ident(settings['source_document'])+' AS VARCHAR)=? LIMIT 50',[record['vessel'],record['document']])
    names=[c[0] for c in cursor.description]
    return [dict(zip(names,row)) for row in cursor.fetchall()]
