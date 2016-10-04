#STEP 2 : Compute lead attribution models from sequence of marketing activity touches sorted by timestamp
# https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/tag/3.0.4.1
# https://neo4j-contrib.github.io/neo4j-apoc-procedures/#
# you will need to download or compile the apoc .jar file and add it to Neo4j/plugins and restart Neo4j
# (tip: update to JDK 8)


#!pip install neo4j-driver

import time

from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"),
                              encrypted=False,
                              trust=TRUST_ON_FIRST_USE)

session = driver.session()

model1 = '''
//lastTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[touches-1]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'lastTouch', attributionTouchTime: touchSeq[touches-1], attributionTouchSeq: touches, attributionTimeSeq: 1, attributionWeight: 1.0, attributionTouches: touches}]->(a)
;
'''

model2 = '''
//firstTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[0]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'firstTouch', attributionTouchTime: touchSeq[0], attributionTouchSeq: 1, attributionTimeSeq: touches, attributionWeight: 1.0, attributionTouches: touches}]->(a)
;
'''

model3 = '''
//linearTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl, RANGE(count(*), 1, -1) AS sequence
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
UNWIND sequence AS seq
WITH i, touches, touchSeq[touches-seq] AS ts, seq, 1/toFloat(touches) AS linear_touch_wt
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = ts
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'linearTouch', attributionTouchTime: ts, attributionTouchSeq: (touches-seq+1), attributionTimeSeq: seq, attributionWeight: linear_touch_wt, attributionTouches: touches}]->(a)
;
'''

model4 = '''
//expDecay
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i,count(*) AS touches, COLLECT(t.timestamp) AS touchColl,  RANGE(count(*), 1, -1) AS sequence
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
UNWIND sequence AS seq
WITH i, touches, touchSeq[touches-seq] AS ts, seq,
CASE touches WHEN 1 THEN 1 ELSE EXP(seq*-0.7) END AS exp_decay_wt
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = ts
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'expDecay', attributionTouchTime: ts, attributionTouchSeq: (touches-seq+1),  attributionTimeSeq: seq, attributionWeight: exp_decay_wt, attributionTouches: touches}]->(a)
;
'''

session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(model1)
session.run(model2)
session.run(model3)
session.run(model4)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()
