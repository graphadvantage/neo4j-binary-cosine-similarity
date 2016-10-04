# neo4j-binary-cosine-similarity
##Neo4j GraphGist - Marketing Recommendations Using Last Touch Attribution Modeling and k-NN Binary Cosine Similarity

# Neo4j Use Case: Real Time Marketing Recommendations

## Introduction

In this GraphGist, we'll take a look at how to use Neo4j to make real-time marketing recommendations. Modern digital marketing produces a ton of data which can be quite unmanagable in traditional SQL databases. However with Neo4j we can leverage the power of the graph to efficiently organize and analyze complex relationships present in our marketing data.

We are going to build a simple recommendation engine that has knowledge of what marketing activities are responsible for driving leads (using marketing attribution modeling) and what sequence of marketing activities are most likely to cause a specific individual to convert to a lead (using k- nearest neighbor and binary cosine similarity).

In Part 1, we'll leverage relationships to compute marketing attributions, resulting in multiple simultaneous attribution models that can be directly queried.

In Part 2, we'll use the marketing attribution models and similarity measures to provide personalized marketing recommendations for individuals who have not yet converted to a lead.


##Part 1. Neo4j Marketing Attribution Modeling

> "Half the money I spend on advertising is wasted; the trouble is I don't know which half." - John Wanamaker

The main goal of marketing is to create demand - doing lots of targeted messaging across different marketing channels, trying to convert individuals from awareness to consideration, or more specifically converting to a lead. What constitutes a lead varies depending on the business - examples include: filling out a contact form, adding an item to a cart, registering for a webinar, walking into a showroom.

Marketers think about a funnel where marketing activities touch individuals who may or may not convert to leads.

This can be represented as a simple graph, that any marketer will understand:

![funnel](https://cloud.githubusercontent.com/assets/5991751/19055116/4ac09242-8977-11e6-9448-fa92575812d1.png)

And when an individual does convert to a lead, the next question is -- which of the various marketing activities (an email, an ad, an event, a webinar, a website visit, a social share, etc) that have touched the individual should get the credit?  

This is the marketing attribution problem - often hotly debated, since every marketer would like to claim that it was their campaign that drove the conversion.  So how can we sort this out?

Marketing attribution is modeled using the historical sequence of touches for each individual, where the individual touches are variously weighted depending the model.

Some example attribution models are:

 * First Touch - the first marketing touch gets 100% credit

 * Last Touch - the last marketing touch gets 100% credit

 * Linear - credit is evenly allocated across all marketing touches (everybody wins!)

 * Time Decay - credit is allocated to marketing touches using a time-dependent function (like exponential decay)

The Google Analytics website provides additional detail on attribution modeling.

https://support.google.com/analytics/answer/1662518?hl=en


##Step 1. Make the Test Graph

So let's start by creating a graph, here we'll use the GraphAware GraphGen plugin (https://github.com/graphaware/neo4j-graphgen-procedure).

You'll need a running Neo4j instance, and you'll need to compile the graphgen .jar file and add it to Neo4j/plugins and restart Neo4j.








This python script uses the Bolt driver.

```
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
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 50) YIELD nodes as i
FOREACH (n IN i |
CREATE (l:Lead)
SET l.timestamp = 0, l.dispLabel = "Lead"
MERGE (n)-[c:CONVERTED_TO]->(l))
RETURN *
;
'''

generate2 = '''
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 50) YIELD nodes as i2
RETURN *
;
'''

generate3 = '''
MATCH (n:Individual) WITH COLLECT(n) AS i
CALL generate.nodes('Activity', '{activityId: randomNumber}', 25) YIELD nodes as a
CALL generate.relationships(a,i, 'TOUCHED', '{timestamp: unixTime}', 25, '5-30') YIELD relationships as rel2
RETURN *
;
'''

generate4 = '''
MATCH (a:Activity)
SET a.dispLabel = "Activity"
RETURN *
;
'''

generate5 = '''
MATCH (i:Individual)
SET i.dispLabel = "Indiv"
RETURN *
;
'''

session = driver.session()
t0 = time.time()
print("processing...")
session.run(generate1)
session.run(generate2)
session.run(generate3)
session.run(generate4)
result = session.run(generate5)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()    
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()

```


##Step 2.

![sequence](https://cloud.githubusercontent.com/assets/5991751/19055659/007ef590-897a-11e6-83ea-59c65391316b.png)

![attribution](https://cloud.githubusercontent.com/assets/5991751/19056221/c9f9114c-897c-11e6-8107-eab4354ee990.png)

*Attribution Models & Weights*
<table>
  <tr>
    <th></th>
    <th>activityId</th>
    <th>9962776</th>
    <th>5</th>
    <th>493</th>
    <th>7</th>
  </tr>
  <tr>
    <td rowspan="3">sequence</td>
    <td>timestamp</td>
    <td>8/5/13</td>
    <td>5/23/13</td>
    <td>10/12/09</td>
    <td>6/23/1978</td>
  </tr>
  <tr>
    <td>attributionTouchSeq</td>
    <td>4</td>
    <td>3</td>
    <td>2</td>
    <td>1</td>
  </tr>
  <tr>
    <td>attributionTimeSeq</td>
    <td>1</td>
    <td>2</td>
    <td>3</td>
    <td>4</td>
  </tr>
  <tr>
    <td rowspan="4">attribution model and weights</td>
    <td>lastTouch</td>
    <td>1.00</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
  </tr>
  <tr>
    <td>firstTouch</td>
    <td>0</td>
    <td>0</td>
    <td>0</td>
    <td>1.00</td>
  </tr>
  <tr>
    <td>linearTouch</td>
    <td>0.25</td>
    <td>0.25</td>
    <td>0.25</td>
    <td>0.25</td>
  </tr>
  <tr>
    <td>expDecay</td>
    <td>0.50</td>
    <td>0.25</td>
    <td>0.12</td>
    <td>0.06</td>
  </tr>
</table>


Part 2.
Neo4j Marketing Recommendations


*OTUs Expression of Binary Instances i and j*
<table>
<tr>
  <th>j \ i</th>
  <th>1 (Presence)</th>
  <th>0 (Absence)</th>
  <th>Sum</th>
</tr>
<tr>
  <th>1 (Presence)</th>
  <td>a = <i>i&nbsp;•&nbsp;j</i></td>
  <td>b = <i>i&#773;&nbsp;•&nbsp;j</i></td>
  <td>a+b</td>
</tr>
<tr>
  <th>0 (Absence)</th>
  <td>c = <i>i&nbsp;•&nbsp;j&#773;<i></td>
  <td>d = <i>i&#773;&nbsp;•&nbsp;j&#773;</i></td>
  <td>c+d</td>
</tr>
<tr>
  <th>Sum</th>
  <td>a+c</td>
  <td>b+d</td>
  <td>n=a+b+c+d</td>
</tr>
</table>


![neo4j-example-reco](https://cloud.githubusercontent.com/assets/5991751/19052701/a8a35e0e-896c-11e6-89b1-90e4fe480d15.png)


![similarity](https://cloud.githubusercontent.com/assets/5991751/19054363/f896d038-8973-11e6-956e-c1014bedbe58.png)
