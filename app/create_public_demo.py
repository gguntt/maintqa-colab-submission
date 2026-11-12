"""Generate an original fictional dataset. No supplied student records are used."""
import json
from pathlib import Path
import duckdb
import config

def main():
    root=Path(__file__).resolve().parent
    data=root/'data'; data.mkdir(exist_ok=True)
    path=data/'public_demo.duckdb'
    if path.exists(): raise SystemExit('public_demo.duckdb already exists. Reuse it or choose a clean checkout.')
    con=duckdb.connect(str(path))
    con.execute('CREATE TABLE master (VESSELCODE VARCHAR, DOC_NO VARCHAR, DOC_NO_DEMO VARCHAR, EQUIP_DESC VARCHAR, MACH_DESC VARCHAR, WORK_DATE DATE, TITLE VARCHAR, WORK_REMARK VARCHAR)')
    con.execute('CREATE TABLE pms (VESSELCODE VARCHAR,DOC_NO VARCHAR,LINE_NO INTEGER,MACH_DESC VARCHAR,EQUIP_DESC VARCHAR,PMS_DESC VARCHAR)')
    con.execute('CREATE TABLE vessels (VESSELCODE VARCHAR,VESSEL_NAME VARCHAR)')
    con.execute('CREATE TABLE approval (VESSELCODE VARCHAR,DOC_NO VARCHAR,SEQ INTEGER,STATUS VARCHAR)')
    con.execute('CREATE TABLE attachments (VESSELCODE VARCHAR,DOC_NO VARCHAR,FILE_NAME VARCHAR)')
    con.execute('CREATE TABLE consumption (VESSELCODE VARCHAR,DOC_NO VARCHAR,MATERIAL_DESC VARCHAR,CONS_QTY INTEGER)')
    for vessel in range(1,7):
        code=f'DEMO{vessel:02d}'
        con.execute('INSERT INTO vessels VALUES (?,?)',[code,f'Fictional training vessel {vessel}'])
        for number in range(1,3):
            doc=f'D{number:03d}';machine='TRAINING PUMP' if number==1 else 'TRAINING FAN'
            body=(f'This is an original fictional software-test record for {machine.lower()} on {code}. '
                  'It is not an operating procedure for a real vessel. '
                  '1) Read the training checklist and identify the mock equipment label. '
                  '2) Visually inspect the disconnected training model and record the observation. '
                  '3) Compare the observation with the classroom worksheet. '
                  '4) Submit the worksheet to the instructor. No actual equipment was operated or repaired.')
            con.execute('INSERT INTO master VALUES (?,?,?,?,?,?,?,?)',
                [code,doc,code+'-'+doc,machine,machine,f'2026-01-{vessel:02d}',machine.lower()+' fictional inspection',body])
            for line in [1,2]: con.execute('INSERT INTO pms VALUES (?,?,?,?,?,?)',[code,doc,line,machine,machine,'Fictional checklist item '+str(line)])
            con.execute('INSERT INTO approval VALUES (?,?,1,?)',[code,doc,'DEMO_COMPLETE'])
            if number==1: con.execute('INSERT INTO consumption VALUES (?,?,?,?)',[code,doc,'Fictional worksheet sheet',vessel])
    con.close()
    assets=root/'assets'/'public_demo';assets.mkdir(parents=True,exist_ok=True)
    values={
      'dictionary.json':{'dataset':'12 original fictional classroom records; not real maintenance advice','document_key':['VESSELCODE','DOC_NO'],'master':'one document per composite key','pms':'two task lines per document'},
      'rules.json':['Count documents using (VESSELCODE,DOC_NO), never DOC_NO alone.','Join using both VESSELCODE and DOC_NO.','Use master for document counts, pms for work-line counts.','Only use exact values present in the schema. Return NOT_RECORDED when unsupported.','All records are fictional classroom software tests.'],
      'fewshots.json':[{'question':'전체 문서는 몇 건인가요?','sql':'SELECT COUNT(*) AS document_count FROM master'},
                      {'question':'선박별 문서 수를 알려 주세요','sql':'SELECT VESSELCODE,COUNT(*) AS document_count FROM master GROUP BY VESSELCODE ORDER BY VESSELCODE'}],
      'terms.json':[{'aliases':['훈련용 펌프','펌프','training pump'],'record_term':'TRAINING PUMP'},
                    {'aliases':['훈련용 팬','팬','training fan'],'record_term':'TRAINING FAN'}]}
    for name,value in values.items(): (assets/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),'utf-8')
    config.save({'db_path':str(path),'assets_path':str(assets),'dataset_id':'public12','demo_data':True,
                 'dataset_notice':'공개 재현용 가상 기록 12건 · 실제 정비 판단용 아님',
                 'columns':{'id':'DOC_NO_DEMO','vessel':'VESSELCODE','document':'DOC_NO','equipment':'EQUIP_DESC','date':'WORK_DATE','title':'TITLE','body':'WORK_REMARK'}})
    print('Created 12 original fictional documents, 24 task lines, 6 vessels.')
    print('Composite keys: 12. DOC_NO alone: 2 (intentionally demonstrates wrong counting).')

if __name__=='__main__': main()
