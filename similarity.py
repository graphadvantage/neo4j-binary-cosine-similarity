#STEP 3 : Compute binary cosine similarity
# I'm using the OTU syntax so that you can try other similarity measures
# Measures that ignore negative similarity to rest of population: cosine, jaccard, euclidean, manhattan
# Measures that include negative similarity to rest of population: sokal-michener, faith, ample
# http://www.iiisci.org/journal/CV$/sci/pdfs/GS315JG.pdf

#!pip install neo4j-driver

import time

from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"),
                              encrypted=False,
                              trust=TRUST_ON_FIRST_USE)

session = driver.session()

sim1 = '''
MATCH (:Activity)
WITH COUNT(*) AS vcnt
MATCH (i1:Individual)<-[:TOUCHED]-(ax:Activity)-[:TOUCHED]->(i2:Individual)
WITH vcnt,i1,i2, COLLECT(ax.activityId) AS v1xv2
MATCH (i1)<-[:TOUCHED]-(a1:Activity)
WITH vcnt,i1,i2,v1xv2, COLLECT(a1.activityId) AS v1
MATCH (i2)<-[:TOUCHED]-(a2:Activity)
WITH vcnt,i1,i2,v1xv2,v1,COLLECT(a2.activityId) AS v2
WITH vcnt,i1,i2,v1xv2,v1,v2,
toFloat(SIZE(v1xv2)) AS a, //a = i • j  (i and j present: 1,1)
toFloat(SIZE(v2)-SIZE(v1xv2)) AS b, // b = i̅ • j (i absent, j present : 0,1)
toFloat(SIZE(v1)-SIZE(v1xv2)) AS c, // c = i • j̅ (i present, j absent: 1,0)
toFloat(vcnt-SIZE(v1)-SIZE(v2)) AS d // d = i̅ • j̅ (i and j absent: 0,0)
MERGE (i1)-[s:SIMILARITY]-(i2)
SET s.similarity = a/SQRT((a+b)*(a+c)), s.measure = 'cosine' // cosine similarity
//SET s.similarity = a/(a+b+c), s.measure = 'jaccard' // jaccard similarity
//SET s.similarity = (2*a)/((2*a)+b+c), s.measure = 'dice' // dice similarity
//SET s.similarity = SQRT(b+c), s.measure = 'euclidean' // euclidean distance
//SET s.similarity = (b+c), s.measure = 'manhattan' // manhattan distance
//SET s.similarity = (a+d)/(a+b+c+d), s.measure = 'sokal-michener' // sokal-michener similarity
//SET s.similarity = (a+(0.5*d))/(a+b+c+d), s.measure = 'faith' // faith similarity
//SET s.similarity = ABS((a*(c+d))/(c*(a+b))), s.measure = 'ample' // ample similarity
'''

session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(sim1)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()
