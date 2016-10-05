##Neo4j GraphGist - Marketing Recommendations Using Last Touch Attribution Modeling and k-NN Binary Cosine Similarity

# Neo4j Use Case: Real-Time Marketing Recommendations


#Part 1. Neo4j Marketing Attribution Models

## Introduction

Graphs are well suited for marketing analytics - a natural fit since marketing is principally about relationships.  In this GraphGist, we'll take a look at how to use Neo4j to make real-time marketing recommendations.

Modern digital marketing produces a ton of data which can be quite unmanagable in traditional SQL databases. However with Neo4j we can leverage the power of the graph to efficiently organize and analyze complex relationships present in our marketing data.

We are going to build a simple recommendation engine that has knowledge of what marketing activities are responsible for driving leads (using marketing attribution modeling) and what sequence of marketing activities are most likely to cause a specific individual to convert to a lead (using k- nearest neighbor and binary cosine similarity).

In Part 1, we'll leverage relationships to compute marketing attributions, resulting in multiple simultaneous attribution models that can be directly queried.

In Part 2, we'll use the marketing attribution models and similarity measures to provide personalized marketing recommendations for individuals who have not yet converted to a lead.


#Part 1. Neo4j Marketing Attribution Modeling

> "Half the money I spend on advertising is wasted; the trouble is I don't know which half." - John Wanamaker

The main goal of marketing is to create demand - doing lots of targeted messaging across different marketing channels, trying to convert individuals from awareness to consideration - or more specifically - converting individuals to leads. What constitutes a lead varies depending on the business - examples include: filling out a contact form, adding an item to a cart, registering for a webinar, walking into a showroom.

Marketers think about a funnel where marketing activities touch individuals who may or may not convert to leads.

This can be represented as a simple graph:

![funnel](https://cloud.githubusercontent.com/assets/5991751/19055116/4ac09242-8977-11e6-9448-fa92575812d1.png)

And when an individual does convert to a lead, the next question is --

Which of the various marketing activities that touched an individual (an email, an ad, an event, a webinar, a website visit, a social share, etc)  should properly get the credit for the conversion?  

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

We'll make the graph shown above -

```
(:Activity)-[:TOUCHED]->(:Individual)-[:CONVERTED_TO]->(:Lead)
```


However, we'll do a couple of things to make it more real.

We'll make 50 (:Individual) nodes where each is [:CONVERTED_TO] one, and only one (:Lead) node:
(this will be our training set for recommendations)

```
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 50) YIELD nodes as i
FOREACH (n IN i |
CREATE (l:Lead)
SET l.timestamp = 0, l.dispLabel = "Lead"
MERGE (n)-[c:CONVERTED_TO]->(l))
RETURN *

```


Then we'll make 50 (:Individual) nodes that have not converted to leads:
(this will our target set for recommendations)

```
CALL generate.nodes('Individual', '{firstName: firstName, lastName: lastName}', 50) YIELD nodes as i2
RETURN *

```


Next we'll create 25 (:Activity) nodes, where each has a [:TOUCHED] relationship set at random to between 5-30 (:Individual) nodes. The idea here is to get good, but not complete coverage of touches to individuals. We'll also set a random {timestamp: unixTime} on each [:TOUCHED] relationship.

```
MATCH (n:Individual) WITH COLLECT(n) AS i
CALL generate.nodes('Activity', '{activityId: randomNumber}', 25) YIELD nodes as a
CALL generate.relationships(a,i, 'TOUCHED', '{timestamp: unixTime}', 25, '5-30') YIELD relationships as rel2
RETURN *

```


Here is the full python script, using the Bolt driver.

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
SET l.dispLabel = "Lead"
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
result = session.run(generate1)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(generate2)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(generate3)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(generate4)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(generate5)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()

```

##Step 2.  Compute and Set Marketing Attribution Models

So now we're ready to take a look at our marketing activity graph and set some attributions for lead conversions.
I'm using procedures from the terrific APOC collection, you'll need to download or compile the apoc .jar file and add it to Neo4j/plugins, then and restart Neo4j.

https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/tag/3.0.4.1

https://neo4j-contrib.github.io/neo4j-apoc-procedures/#

(tip: update to JDK 8)

If you run a simple query, picking a node that has the [c:CONVERTED_TO] relationship -

```
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE id(i) = 6
RETURN a.activityId, t.timestamp, i.firstName, l.dispLabel ORDER BY t.timestamp DESC
```


You'll get a result like this:

![sequence](https://cloud.githubusercontent.com/assets/5991751/19055659/007ef590-897a-11e6-83ea-59c65391316b.png)

We can see that our (:Individual) Ibrahim has been [:TOUCHED] by at different times by four different (:Activity) nodes.

So which (:Activity) should get credit - the last touch? the first touch? multiple touches?

One of the great things about Neo4j is that time is represented in UNIX epoch format, which means that you can directly operate on time values. Here's our result in table format, sorted by [:TOUCHED] timestamp in descending order:

```
╒════════════╤═════════════╤═══════════╤═══════════╕
│a.activityId│t.timestamp  │i.firstName│l.dispLabel│
╞════════════╪═════════════╪═══════════╪═══════════╡
│9962776     │1375664344473│Ibrahim    │Lead       │
├────────────┼─────────────┼───────────┼───────────┤
│5           │1369329139115│Ibrahim    │Lead       │
├────────────┼─────────────┼───────────┼───────────┤
│493         │1255375038838│Ibrahim    │Lead       │
├────────────┼─────────────┼───────────┼───────────┤
│7           │267417903376 │Ibrahim    │Lead       │
└────────────┴─────────────┴───────────┴───────────┘
```


To create attribution models, all we need to do is collect all the [:TOUCHED] relationships for each (:Individual) that has [:CONVERTED_TO] a (:Lead), sort the collection and compute the model.  Because the model represents the unique vector of historical touches specific to the individual, we'll instantiate the attribution models as relationships, which also allows us to have as many models as we'd like:

```
(:Lead)-[:ATTRIBUTED_TO {attributionModel: lastTouch}]->(:Activity)

(:Lead)-[:ATTRIBUTED_TO {attributionModel: expDecay}]->(:Activity)

```


We can make collections of [:TOUCHED] timestamps, and then sort them using the apoc.coll.sort() procedure:

```
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, collect(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
RETURN i.firstName, touches, touchSeq  LIMIT 10
```


This produces collections for each (:Individual), with the oldest timestamp at touchSeq[0] and the most recent timestamp at touchSeq[touches-1]:

```
╒═══════════╤═══════╤═════════════════════════════════════════════════════════════════════════════════════════╕
│i.firstName│touches│touchSeq                                                                                 │
╞═══════════╪═══════╪═════════════════════════════════════════════════════════════════════════════════════════╡
│Michel     │5      │[683214895624, 1022527753486, 1127426290931, 1147267584540, 1291272829003]               │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Lelia      │5      │[773610084727, 996162214244, 1069739471934, 1236021026000, 1397203487581]                │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Julie      │9      │[741878204719, 787410706000, 1016436036278, 1155688166191, 1349002092720, 1361081390290, │
│           │       │1370401727621, 1413566631375, 1422497088344]                                             │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Grady      │8      │[632188698743, 892339299937, 1015726257805, 1084620820709, 1166570106468, 1169231572498, │
│           │       │1210582690808, 1376076806159]                                                            │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Bridie     │5      │[698291669105, 827463700452, 1352584281748, 1424960410657, 1438324410676]                │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Adrain     │3      │[1090639800509, 1315105479995, 1433439883470]                                            │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Greyson    │2      │[1202749235437, 1429128653726]                                                           │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Earnestine │1      │[774153831192]                                                                           │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Carlee     │3      │[508051588542, 1365162376421, 1471502656954]                                             │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Burley     │2      │[1363063898626, 1370542711963]                                                           │
└───────────┴───────┴─────────────────────────────────────────────────────────────────────────────────────────┘

```


###Last Touch Attribution Model

For the "Last Touch" model, we use the most recent timestamp from the sorted timestamp collection (touchSeq) to search for the (:Activity) with most recent [:TOUCH], and set the [:ATTRIBUTED_TO] relationship between this (:Activity) and the (:Lead).  Per the model, the attributionWeight is set 1.0.  I'm also recording some additional data about this  model, including the model name (attributionModel), the timestamp used in the attribution (attributionTouchTime), this touch's position relative to sequence (attributionTouchSeq [1 is oldest]), and relative to time (attributionTimeSeq [1 is the latest]), and total touches (attributionTouches).

```
//lastTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[touches-1]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'lastTouch', attributionTouchTime: touchSeq[touches-1], attributionTouchSeq: touches, attributionTimeSeq: 1, attributionWeight: 1.0, attributionTouches: touches}]->(a)

```


###First Touch Attribution Model

The "First Touch" model is exactly the same, except now we are searching the graph for the oldest (:Activity)-[:TOUCHED]-> relationship, using `t.timestamp = touchSeq[0]`. As above, the attributionWeight = 1.0.  

```
//firstTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[0]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'firstTouch', attributionTouchTime: touchSeq[0], attributionTouchSeq: 1, attributionTimeSeq: touches, attributionWeight: 1.0, attributionTouches: touches}]->(a)

```


###Linear Touch Attribution Model

The next two models require weights to be set for all participating touches. To accomplish this we'll COLLECT and sort the touches as above, and also generate a RANGE of integers from [touches..1] that represents a sequence index.  We'll UNWIND the touch collection on this sequence and use its values as inputs for our [:TOUCHED] search and for the weighting math for each touch.

For the "Linear Touch" attribution model the weighting is the inverse of the number of touches in the sequence. We have to convert (touches) to a float prior to division.

```
//linearTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl, RANGE(count(*), 1, -1) AS sequence
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
UNWIND sequence AS seq
WITH i, touches, touchSeq[touches-seq] AS ts, seq, 1/toFloat(touches) AS linear_touch_wt
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = ts
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'linearTouch', attributionTouchTime: ts, attributionTouchSeq: (touches-seq+1), attributionTimeSeq: seq, attributionWeight: linear_touch_wt, attributionTouches: touches}]->(a)

```


###Exponential Decay Touch Attribution Model

For the "Exponential Decay" attribution model we'll use e^( 0.7 * t ) as the time-dependent decay function, which halves the weighting at every time step. We need to wrap this in a CASE statement to handle collections of only 1 touch, in which case the weight should be equal to 1.

```
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

```


Here's the full script, which applies all four models to the (:Leads) in the graph.

```
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
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(model2)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(model3)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


session = driver.session()
t0 = time.time()
print("processing...")
result = session.run(model4)
print(round((time.time() - t0)*1000,1), " ms elapsed time")
print('-----------------')
summary = result.consume()
print(summary.statement)
print(summary.notifications)
print(summary.counters)
session.close()


```

Let's take a look -  

Using the simple query from above, picking a node that has the [c:CONVERTED_TO] relationship -

```
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)-[m:ATTRIBUTED_TO]->(a)
WHERE id(i) = 6
RETURN *
```


![attribution](https://cloud.githubusercontent.com/assets/5991751/19056221/c9f9114c-897c-11e6-8107-eab4354ee990.png)


Each of the four (:Activity) nodes has been attributed to the (:Lead) node.

The firstTouch model assigns all credit to {activityId: 7}, the lastTouch model (highlighted) assigns all credit to {activityId: 9962776}.

The linearTouch and expDecay models assign credit to all the participating (:Activity) nodes.

Here's a summary of our models for this (:Individual):


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

##Using the Lead Attribution Models

We can directly search the graph on the [:ATTRIBUTED_TO] relationship to understand which activities are contributing the most to driving leads.

If we want to see the top 10 activities using the lastTouch model, we can run this report:

 ```
 MATCH (n:Lead) WITH COUNT(n) as nLeads
 MATCH (l:Lead)-[m:ATTRIBUTED_TO {attributionModel: "lastTouch"}]->(a:Activity)
 WITH nLeads, m.attributionModel AS model, a.activityId AS activity, COUNT(l) AS leadCount
 RETURN model,activity,leadCount,nLeads AS totalLeads, ROUND((toFloat(leadCount)/nLeads)*10000)/100 + ' %' AS freq
 ORDER BY leadCount DESC LIMIT 10
 ```


The results show that 26% of the leads can be attributed to 3 activities.

```
lastTouch Lead Attribution Model
 ╒═════════╤════════╤═════════╤══════════╤══════╕
 │model    │activity│leadCount│totalLeads│freq  │
 ╞═════════╪════════╪═════════╪══════════╪══════╡
 │lastTouch│30740   │5        │50        │10.0 %│
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│2709812 │4        │50        │8.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│80      │4        │50        │8.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│46669   │4        │50        │8.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│493     │4        │50        │8.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│5107    │3        │50        │6.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│51      │3        │50        │6.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│20      │3        │50        │6.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│5       │2        │50        │4.0 % │
 ├─────────┼────────┼─────────┼──────────┼──────┤
 │lastTouch│4       │2        │50        │4.0 % │
 └─────────┴────────┴─────────┴──────────┴──────┘

```


What about our time-dependent models?

The report query is similar, except now we are averaging and summing the model weights.

These models take into account all touches over all time that may influenced the individual.  I like the expDecay attribution model because it makes the fair assumption that the more recent touches should have more influence compared to older touches.

Sorting on the sum of the {attributionWeight} gives us the ranked contribution to lead conversion by each Activity, and we can also estimate a weighted frequency as the freq * avgWt.

```
MATCH (l:Lead)-[m:ATTRIBUTED_TO {attributionModel: "expDecay"}]->(a:Activity)
WITH nLeads, m.attributionModel AS model, a.activityId AS activity, COUNT(l) AS leadCount, ROUND(AVG(m.attributionWeight)*1000)/1000 AS avgWt, ROUND(SUM(m.attributionWeight)*100)/100 AS sumWt, ROUND(AVG(m.attributionTimeSeq)*100)/100 AS avgTimeSeq
RETURN model,activity,leadCount, avgWt, sumWt, avgTimeSeq, nLeads AS totalLeads, ROUND((toFloat(leadCount)/nLeads)*10000)/100 + ' %' AS freq, ROUND((toFloat(leadCount)/nLeads)*avgWt*10000)/100 + ' %' AS weightedFreq ORDER BY sumWt DESC
```


Here is the result, showing (:Activities) ordered by sumWt. More than 30% of the leads are attributed to the two highest ranked Activities, and on average, these are seen as the 2nd or 3rd most recent touch (avgTimeSeq).

```
expDecay Lead Attribution Model
╒════════╤════════╤═════════╤═════╤═════╤══════════╤══════════╤══════╤════════════╕
│model   │activity│leadCount│avgWt│sumWt│avgTimeSeq│totalLeads│freq  │weightedFreq│
╞════════╪════════╪═════════╪═════╪═════╪══════════╪══════════╪══════╪════════════╡
│expDecay│30740   │15       │0.273│4.1  │2.27      │50        │30.0 %│8.19 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│2709812 │16       │0.205│3.27 │3.06      │50        │32.0 %│6.56 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│51      │12       │0.27 │3.24 │2.17      │50        │24.0 %│6.48 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│493     │13       │0.214│2.78 │2.92      │50        │26.0 %│5.56 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│5107    │9        │0.295│2.66 │2         │50        │18.0 %│5.31 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│20      │11       │0.239│2.63 │2.55      │50        │22.0 %│5.26 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│46669   │11       │0.238│2.62 │3.09      │50        │22.0 %│5.24 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│80      │6        │0.373│2.24 │2.17      │50        │12.0 %│4.48 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│9962776 │13       │0.162│2.11 │3.62      │50        │26.0 %│4.21 %      │
├────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│expDecay│0       │9        │0.21 │1.89 │3.11      │50        │18.0 %│3.78 %      │
└────────┴────────┴─────────┴─────┴─────┴──────────┴──────────┴──────┴────────────┘

```


Here is the result for the linearTouch model, you can see the rankings are a bit different.

```
expDecay Lead Attribution Model
╒═══════════╤════════╤═════════╤═════╤═════╤══════════╤══════════╤══════╤════════════╕
│model      │activity│leadCount│avgWt│sumWt│avgTimeSeq│totalLeads│freq  │weightedFreq│
╞═══════════╪════════╪═════════╪═════╪═════╪══════════╪══════════╪══════╪════════════╡
│linearTouch│30740   │15       │0.269│4.03 │2.27      │50        │30.0 %│8.07 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│51      │12       │0.291│3.49 │2.17      │50        │24.0 %│6.98 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│2709812 │16       │0.217│3.47 │3.06      │50        │32.0 %│6.94 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│493     │13       │0.26 │3.38 │2.92      │50        │26.0 %│6.76 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│9962776 │13       │0.259│3.37 │3.62      │50        │26.0 %│6.73 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│9167612 │11       │0.252│2.77 │3.45      │50        │22.0 %│5.54 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│46669   │11       │0.25 │2.75 │3.09      │50        │22.0 %│5.5 %       │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│5942581 │13       │0.189│2.46 │4.77      │50        │26.0 %│4.91 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│0       │9        │0.257│2.32 │3.11      │50        │18.0 %│4.63 %      │
├───────────┼────────┼─────────┼─────┼─────┼──────────┼──────────┼──────┼────────────┤
│linearTouch│20      │11       │0.187│2.06 │2.55      │50        │22.0 %│4.11 %      │
└───────────┴────────┴─────────┴─────┴─────┴──────────┴──────────┴──────┴────────────┘
```


##Summary

In a typical enterprise there might be hundreds of thousands of marketing activities every month that touch millions of individuals - calculating marketing attribution would be nearly impossible to perform in a SQL database at this scale.

With a graph database we can leverage relationships as inputs to complex, atomic-level calculations as well as for efficiently storing and retrieving the output of simultaneous calculations (also at an atomic level).

Here I've shown how marketing attribution is a straightforward, flexible exercise in Neo4j.  We used [:TOUCHED] relationships to keep a full history of marketing touches on individuals, which were mined to compute marketing attributions using several different models, with the output of each model calculation stored as [:ATTRIBUTED_TO] relationships connecting leads to activities.

With these relationships in place it's easy to determine which marketing activities are driving the most leads - our main objective.

Next we'll explore how to make personalized marketing recommendations.



----

##Neo4j GraphGist - Marketing Recommendations Using Last Touch Attribution Modeling and k-NN Binary Cosine Similarity

# Neo4j Use Case: Real Time Marketing Recommendations


#Part 2. Neo4j Marketing Recommendations

In Part 1 we took a look at how to implement marketing attribution models in a Neo4j graph to enable us to determine which marketing activities are driving leads.  We produced a graph with this basic structure, where each (:Lead) has been [:ATTRIBUTED_TO] one or more of the (:Activity) nodes with a [:TOUCHED] relationship to the (:Individual) :

![attribution](https://cloud.githubusercontent.com/assets/5991751/19056221/c9f9114c-897c-11e6-8107-eab4354ee990.png)

So for the (:Individual) that has NOT [:CONVERTED_TO]->(:Lead) which is the best next (:Activity)?

We'll solve this using a collaborative filtering technique called k-nearest neighbors (k-NN).  We'll compute the cosine similarity across all (:Individual) nodes, using their history of marketing touches as the basis for the similarity measure.

For more background see the excellent GraphGist by Nicole White where she uses k-NN and cosine similarity to compute movie recommendations.

http://portal.graphgist.org/graph_gists/movie-recommendations-with-k-nearest-neighbors-and-cosine-similarity

##Cosine Similarity: Movie Recommendations

Cosine similarity is the angle between two vectors in n-dimensional space, and ranges from -1 (exactly dissimilar) to 1 (exactly similar).

It is typically calculated as the dot product of the two vectors, divided by the product of the length of each vector (where the length of each vector is the square root of the sum of squares).

![similarity-eq](https://cloud.githubusercontent.com/assets/5991751/19095909/94375fe2-8a4d-11e6-91ad-ceff4c92549a.png)

In Nicole's movie example, she is working with individuals that have submitted different ratings for the same movie.

The rating vectors are sorted by movie, and the cosine similarity is computed for pairs of ratings (one rating from each individual, for the same movie):

![similarity-example-eq](https://cloud.githubusercontent.com/assets/5991751/19095933/b4148cae-8a4d-11e6-9855-66f61f8fb245.png)

She then sets a the similarity relationship (i1:Individual {name:"M.Hunger"})-[:SIMILARITY]->(i2:Individual {name:"M.Sherman"})  and gives it a value of 0.86. This is done for all individuals in the graph (full cartesian, so every individual has a [:SIMILARITY] to every other individual).

Now movie recommendations can be produced by averaging the movie ratings of the most similar neighbors to the target individual, and picking the highest rated movies that the target individual has not seen.


##Binary Cosine Similarity: Marketing Recommendations

We'll follow Nicole's approach, but we need to make some modifications to account for how marketing works.

First of all, there's no concept of "rating" - as we saw in Part 1, marketing activities either touch - or don't touch - an individual, meaning our scores are strictly binary.

Second, the movie rating case is dealing with exact intersections of vectors. In the marketing use case we need to compute similarity from both the intersecting and non-intersecting lengths of each vector.

Here's a simple query

```
MATCH (a)-[t:TOUCHED]->(i:Individual)
WHERE id(i)=6
MATCH (a2)-[t2:TOUCHED]->(i2:Individual)
WHERE id(i2)=100
RETURN a,t,i,i2,t2,a2
```

Here's what we need to solve for: How similar are the touch histories of Nicklaus and Ibrahim?

You can see that between Nicklaus and Ibrahim there are 6 six activities, with 5 touching Nicklaus and 4 touching Ibrahim.  There are 2 activities that have touched Nicklaus that have not touched Ibrahim, and 1 marketing activity that has touched Ibrahim that has not touched Nicklaus.

![touch-vectors](https://cloud.githubusercontent.com/assets/5991751/19096766/f16a2b30-8a53-11e6-9e07-e88c1b75930e.png)

We can consider the two individuals Ibrahim and Nicklaus as overlapping vectors of binary touches for each activity, as shown in table below.

Let's call Ibrahim vector(i) and Nicklaus vector(j).

<table style="textalign: center">
<colgroup>
<col style="width: 83px">
<col style="width: 76px">
<col style="width: 74px">
<col style="width: 68px">
<col style="width: 67px">
<col style="width: 74px">
<col style="width: 72px">
<col style="width: 78px">
</colgroup>
  <tr>
    <th class="tg-s6z2">activityId</th>
    <th class="tg-baqh">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;51&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
    <th class="tg-baqh">56903247</th>
    <th class="tg-baqh">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;493&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
    <th class="tg-baqh">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
    <th class="tg-baqh">9962776</th>
    <th class="tg-baqh">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;7&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</th>
    <th class="tg-baqh">&nbsp;&nbsp;Sum&nbsp;&nbsp;</th>
  </tr>
  <tr>
    <td class="tg-baqh">Ibrahim (i)</td>
    <td class="tg-baqh">0</td>
    <td class="tg-baqh">0</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">a + c = 4</td>
  </tr>
  <tr>
    <td class="tg-baqh">Nicklaus (j)</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">1</td>
    <td class="tg-baqh">0</td>
    <td class="tg-baqh">a + b = 5</td>
  </tr>
  <tr>
    <td class="tg-baqh">OTU</td>
    <td class="tg-baqh" colspan="2">b = i̅ • j</td>
    <td class="tg-baqh" colspan="3">a = i • j</td>
    <td class="tg-baqh">c = i • j̅</td>
    <td class="tg-baqh"></td>
  </tr>
  <tr>
    <td class="tg-baqh">Sum</td>
    <td class="tg-baqh" colspan="2">b = 2</td>
    <td class="tg-baqh" colspan="3">a = 3</td>
    <td class="tg-baqh">c = 1</td>
    <td class="tg-baqh"></td>
  </tr>
</table>


In the binary case, our math reduces to the intersection and the lengths of each vector:

The dot product i • j becomes (0\*1)+(0\*1)+(1\*1)+(1\*1)+(1\*1)+(1\*0) = 3, or the length of the intersection

The sum of squares of i becomes (0^2)+(0^2)+(1^2)+(1^2)+(1^2)+(1^2) = 4, or the length of i

The sum of squares of j becomes (1^2)+(1^2)+(1^2)+(1^2)+(1^2)+(0^2) = 5, or the length of j

The binary cosine similarity Ibrahim (i) and Nicklaus (j) is then:  (3 / SQRT(4*5)) = 0.67

##Operational Taxonomic Unit (OTU) Notation

The table row marked "OTU" refers to "Operational Taxonomic Units" and is based on an excellent review of binary measures of similarity by Choi et al, 2010 http://www.iiisci.org/journal/CV$/sci/pdfs/GS315JG.pdf  

They provide 76 measures of binary similarity and distance written in OTU notation.

The contingency table below describes this notation, which we can use to explore other similarity measures, such as Jaccard and Dice.

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

OTU notation describes how the vectors are related:

a = i • j  (i and j present: 1,1) - the intersection of (i,j) = 3

b = i̅ • j (i absent, j present : 0,1) - the vector j minus the intersection = 2

c = i • j̅ (i present, j absent: 1,0) - the vector i minus the intersection = 1

d = i̅ • j̅ (i and j absent: 0,0) - all the other data points not included in (i,j)

In OTU notation (and using Ibrahim and Nicklaus) we get:

Bianry Cosine Similarity: a/SQRT((a+b)\*(a+c)) = 3/SQRT((3 + 2)\*(3 + 1)) = 0.67

Binary Jaccard Similarity: a/(a+b+c) = 3/(3 + 2 + 1) = 0.50

Binary Dice Similarity: (2\*a)/((2\*a)+b+c) = (2\*3)/((2\*3) + 2 + 1) = 0.66

In the next section we'll use OTU notation for computing binary cosine similarity in our marketing graph

##Step 1. Adding Binary Cosine Similarity to the Graph

Because all of our data is binary, and now that we understand how to compute binary cosine similarity using OTU notation, all we need to do is determine the lengths of a, b, c, d for each pair of individuals in the graph.

1. First we COUNT all activities as vcnt

2. Next we COLLECT all intersecting activities as v1xv2

3. Next we COLLECT all the activities for the first individual as v1

4. Next we COLLECT all the activities for the second individual as v2

5. We then derive a, b, c, d from the lengths of each vector

> a = SIZE(v1xv2)

> b = SIZE(v2) - SIZE(v1xv2)

> c = SIZE(v1) - SIZE(v1xv2)

> d = vcnt - SIZE(v1) - SIZE(v2)

Finally, we create the [:SIMILARITY] relationship each pair of individuals, and set the computed binary cosine similarity: (a/SQRT((a+b)\*(a+c))). This is done for all individuals in the graph (full cartesian, so every individual has a [:SIMILARITY] to every other individual).

```
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

```

The full Python script, using the Bolt driver.

You'll notice I've included some other similarity and distance measures in OTU notation for you to experiment with.

```
#STEP 3 : Compute binary cosine similarity
# I'm using the OTU syntax so that you can try other similarity measures
# Measures that ignore negative similarity to rest of population: cosine, jaccard, euclidean, manhattan
# Measures that include negative similarity to rest of population: sokal-michener, faith
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

```

##Step 2. Making k-NN Recommendations using Binary Cosine Similarity and Last Touch Lead Attribution

Lets take a look at Nicklaus's 4 nearest neighbors who have converted to leads:

```
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)
WHERE id(i) = 100
OPTIONAL MATCH (i)-[s:SIMILARITY]->(i2)-[c:CONVERTED_TO]->(l:Lead)
OPTIONAL MATCH (a2:Activity)-[t2:TOUCHED]->(i2)
RETURN * ORDER BY s.similarity DESC LIMIT 35
```


![similarity](https://cloud.githubusercontent.com/assets/5991751/19054363/f896d038-8973-11e6-956e-c1014bedbe58.png)

You can see that each neighbor (Ibrahim, Cyril, Sonny, Geovanni) has a [:SIMILARITY] relationship to Nicklaus, and - as we would expect - that these neighbors have been [:TOUCHED] by a number of the same (:Activity) nodes.

Our goal is to search the nearest neighbors for (:Activity) nodes that are associated with converting the neighbor to a lead, but have not yet [:TOUCHED] Nicklaus.  We'll assume that the best picks will be from the neighbors with the highest cosine similarity score.

This raises the question: Which of the similar neighbor's (:Activity) nodes do we want recommend?  

Fortunately we've got this covered from Part 1 -- every neighbor's lead has already been [:ATTRIBUTED_TO]->(:Activity) with our attribution models. So all we have to do is pick the lead attribution model we want to use for our recommendations.  

To keep things simple, we'll use our Last Touch attribution model, which gives 100% credit for lead conversion to the most recent (:Activity) that touched the individual.

For each unconverted target individual:

1. We'll find the 10 nearest converted neighbors, find their "lastTouch" attributed (:Activity)
2. We check to make sure that the target hasn't converted to a (:Lead) and hasn't already been touched by a k-NN lastTouch (:Activity)
3. We sort the target individuals by id, and their neighbors by descending similarity score
4. We then COLLECT the activityId and similarity scores for the top ten most similar neighbors
5. We then UNWIND the top ten collection, and for each k-NN activity, average the similarity score and count the neighbors
6. Return the result for each target individual, with recommended (:Activity) sorted by average similarity in descending order

Here's the recommendation query:

```
MATCH (a1:Activity)-[:TOUCHED]->(i1:Individual)-[s:SIMILARITY]->(n1:Individual)-[c:CONVERTED_TO]->(l:Lead)-[:ATTRIBUTED_TO {attributionModel: 'lastTouch'}]->(a2:Activity)
WHERE NOT ((i1)-[:CONVERTED_TO]->(:Lead)) AND a1 <> a2
WITH i1, s.measure AS msr, s.similarity AS sim, a2.activityId AS acts
ORDER BY id(i1) ASC, sim DESC
//sample 10 nearest neighbors with highest similarity
WITH i1, msr, COLLECT([acts,sim])[0..10] AS nn
UNWIND nn AS top_nn
WITH i1, msr, top_nn[0] AS av, ROUND(avg(top_nn[1])*1000)/1000 AS avg_s, count(top_nn[1]) AS cnt_nn
ORDER BY id(i1) ASC, avg_s DESC, cnt_nn DESC
RETURN id(i1) AS targetId, i1.firstName AS firstName, i1.lastName AS lastName, av AS activityId, avg_s AS avgSimilarity, cnt_nn AS countNeighbors, msr AS simMeasure

```

And here's the result:

So now we have a handful of recommendations to make for each unconverted individual in our marketing graph, along with stats on similarity and lastTouch frequency across the k-NN converted neighbors.  The table formatting as done using Pandas (see the Jupyter notebook that consolidates Part 1 and Part 2).

![neo4j-example-reco](https://cloud.githubusercontent.com/assets/5991751/19052701/a8a35e0e-896c-11e6-89b1-90e4fe480d15.png)


Here are the recommendations using Jaccard similarity (from re-running the similarity.py script uncommenting the Jaccard OTO calc).


![neo4j-example-reco-jaccard](https://cloud.githubusercontent.com/assets/5991751/19128164/f9528682-8af6-11e6-9cfc-f8cabf8a69b3.png)



Here's the full script:

```
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

```

## Summary

I've shown how to create recommendations in a Neo4j marketing graph which leverages relationships to compute k-NN similarity scores from binary data (presence or absence of a relationship, in this case the [:TOUCHED] relationship).  

Our recommendation algorithm uses the marketing attribution models built in Part 1, which enables us to do more sophisticated selections of activities that we can recommend.

We also took a look at Operational Taxonomic Unit (OTU) notation which makes it easy to experiment with different type of similarity and distance functions. I've provide a handful of these in the scripts, there are many more covered in Choi et al, 2010.

Neo4j is well-suited for marketing use cases, and in this GraphGist we've pulled together the basic elements needed to build a graph-based real-time marketing recommendation engine.

Special thanks to Michael Kilgore (InfoClear Consulting) and Nicole White's inspiring GraphGist.
