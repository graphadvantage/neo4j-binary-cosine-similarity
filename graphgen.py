#STEP 1 : Generate fake data using GraphAware graphgen
# https://github.com/graphaware/neo4j-graphgen-procedure
# you will need to compile the graphgen .jar file and add it to Neo4j/plugins and restart Neo4j
# (tip: update to JDK 8)

#!pip install neo4j-driver

import time

from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"),
                              encrypted=False,
                              trust=TRUST_ON_FIRST_USE)

session = driver.session()


generate1 = '''
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 100) YIELD nodes as i
FOREACH (n IN i |
CREATE (l:Lead)
SET l.timestamp = 0, l.dispLabel = "Lead"
MERGE (n)-[c:CONVERTED_TO]->(l))
RETURN *
;
'''

generate2 = '''
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 100) YIELD nodes as i2
RETURN *
;
'''

generate3 = '''
MATCH (n:Individual) WITH COLLECT(n) AS i
CALL generate.nodes('Activity', '{activityId: randomNumber}', 25) YIELD nodes as a
CALL generate.relationships(a,i, 'TOUCHED', '{timestamp: unixTime}', 25, '25-50') YIELD relationships as rel2
RETURN *
;
'''

generate4 = '''
MATCH (a:Activity)-[:TOUCHED]->(i:Individual)
SET i.dispLabel = "Indiv"
SET a.dispLabel = "Activity"
;
'''

session = driver.session()
t0 = time.time()
print("processing...")
session.run(generate1)
session.run(generate2)
session.run(generate3)
session.run(generate4)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
session.close()
