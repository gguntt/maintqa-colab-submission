import math
import re
from collections import Counter

def tokenize(text): return re.findall(r'[a-z0-9]+|[가-힣]+',text.lower())

class BM25:
    def __init__(self,records):
        self.records=records
        self.docs=[Counter(tokenize((r['title']+' ')*3+r['body'])) for r in records]
        self.lengths=[sum(d.values()) for d in self.docs]
        self.average=sum(self.lengths)/max(len(records),1)
        self.df=Counter(t for d in self.docs for t in d)
    def search(self,text):
        scores=[]
        for i,doc in enumerate(self.docs):
            score=0
            for term in set(tokenize(text)):
                tf=doc[term]
                if tf:
                    idf=math.log(1+(len(self.docs)-self.df[term]+.5)/(self.df[term]+.5))
                    score+=idf*tf*2.5/(tf+1.5*(.25+.75*self.lengths[i]/self.average))
            if score>0: scores.append((score,i))
        return [dict(self.records[i],record=n+1,score=round(score,5)) for n,(score,i) in enumerate(sorted(scores,key=lambda x:(-x[0],x[1]))[:4])]

def verify(steps,records):
    verified=[]
    for step in steps:
        quote=step.get('quote','')
        if not isinstance(quote,str) or len(quote.strip())<8:
            raise ValueError('인용이 없거나 너무 짧아 검증할 수 없습니다.')
        matches=[r for r in records if quote in r['body']]
        if not matches: raise ValueError('실제 원문에서 인용을 찾지 못했습니다. 답변을 보류합니다.')
        match=next((r for r in matches if r['record']==step.get('record')),matches[0])
        # Display the exact supported text. Generated instructions cannot be substituted for evidence.
        verified.append({'step':quote,'record':match['record'],'quote':quote,'verified':True,
                         'proposed_step':str(step.get('step',''))})
    if not verified: raise ValueError('검증할 수 있는 단계별 근거가 없습니다.')
    return verified
