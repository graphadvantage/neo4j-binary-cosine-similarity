#STEP 4 : Compute recommendations for target individual, using converted nearest neighbors
# and activity selected from the lastTouch marketing attribution model

#!pip install neo4j-driver

import time

import pandas as pd

from IPython.display import display, HTML

from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"),
                              encrypted=False,
                              trust=TRUST_ON_FIRST_USE)

session = driver.session()

reco1 = '''
MATCH (a1:Activity)-[:TOUCHED]->(i1:Individual)-[s:SIMILARITY]->(n1:Individual)-[c:CONVERTED_TO]->(l:Lead)-[:ATTRIBUTED_TO {attributionModel: 'lastTouch'}]->(a2:Activity)
WHERE NOT ((i1)-[:CONVERTED_TO]->(:Lead)) AND a1 <> a2
WITH i1, s.measure AS msr, s.similarity AS sim, a2.activityId AS acts
ORDER BY id(i1) ASC, sim DESC
//sample 10 nearest neighbors with highest similarity
WITH i1, msr, COLLECT([acts,sim])[0..10] AS nn
UNWIND nn AS top_nn
WITH i1, msr, top_nn[0] AS av, ROUND(avg(top_nn[1])*1000)/1000 AS avg_s, count(top_nn[1]) AS cnt_nn
ORDER BY id(i1) ASC, avg_s DESC, cnt_nn DESC
RETURN id(i1) AS targetId, i1.firstName AS firstName, i1.lastName AS lastName, av AS activityId, avg_s AS avgSimilarity, cnt_nn AS countNeighbors , msr AS simMeasure
'''

session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(reco1)
print()
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
session.close()

print()
print("Marketing Activity Recommendations:")
print("k-NN using Binary Similarity and Last Touch Attribution")
print()
print("(Recommended next marketing activity for an unconverted individual based on")
print("nearest converted neighbors with a similar history of marketing touches")
print("and where conversion to lead is attributed to the last marketing touch.)")
print()

df = pd.DataFrame(list([r.values() for r in result]),
                      columns=['nodeId (target)','firstName','lastName', 'activityId (reco)', 'avgSimilarity', 'countNeighbors','simMeasure'])
#print(df)

#display(df)

df.style\
    .bar(subset=['avgSimilarity'], color='#ff9500')\
    .bar(subset=['countNeighbors'], color='#efefef')\
