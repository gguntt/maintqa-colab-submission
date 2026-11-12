"""Deterministic, model-free routing."""
import re

AGG = re.compile(r'몇\s*건|건수|개수|평균|목록|비율|순위|합계|총\s*몇|최대|최소|count|average|list|ratio|sum', re.I)
PROC = re.compile(r'어떻게|절차|원인|조치|방법|기준|고장|procedure|cause|how', re.I)

def route(question):
    # Explicit procedure intent takes precedence over incidental words such as 목록.
    return 'procedure' if PROC.search(question) else 'aggregate' if AGG.search(question) else 'procedure'

def needs_rewrite(question):
    return len(question.strip()) <= 8 or bool(re.search(r'그것|그거|그때|해당|이것|앞서|그러면|그 장비|그 선박', question))
