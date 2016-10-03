import time

from neo4j.v1 import GraphDatabase, basic_auth, TRUST_ON_FIRST_USE, CypherError

driver = GraphDatabase.driver("bolt://localhost",
                              auth=basic_auth("neo4j", "neo4j"),
                              encrypted=False,
                              trust=TRUST_ON_FIRST_USE)

session = driver.session()


detachDelete = '''
MATCH (n) DETACH DELETE n
'''

t0 = time.time()
print("processing...")
result = session.run(detachDelete)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')


summary = result.consume()

for record in result:
    print(record)

print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()
