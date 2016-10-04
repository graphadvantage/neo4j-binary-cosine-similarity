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

##Step 2.  Compute and Set Marketing Attribution Models

So now we're ready to take a look at our marketing activity graph and set some attributions for lead conversions.
I'm using procedures from the terrific APOC collection, you'll need to download or compile the apoc .jar file and add it to Neo4j/plugins, then and restart Neo4j

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

We can see that our (:Individual) Ibrahim has been [:TOUCHED] by at different times by four different (:Activity) nodes. And - thanks to the miracle of random numbers, even once during the summer of '78... long before email...

https://weeklytop40.wordpress.com/1978/06/24/us-top-40-singles-week-ending-24th-june-1978/

<table>
  <tr>
    <th rowspan="5">
    <img src="https://weeklytop40.files.wordpress.com/1978/07/andy-gibb-shadow-dancing-rso-3.jpg?w=200&amp;h=200">
    </th>
    <td>1. SHADOW DANCING –•– Andy Gibb (RSO)</td>
  </tr>
  <tr>
    <td>2. BAKER STREET –•– Gerry Rafferty (United Artists)</td>
  </tr>
  <tr>
    <td>3. IT’S A HEARTACHE –•– Bonnie Tyler (RCA)</td>
  </tr>
  <tr>
    <td>4. YOU’RE THE ONE THAT I WANT –•– John Travolta and Olivia Newton-John (RSO)</td>
  </tr>
  <tr>
    <td>5. TAKE A CHANCE ON ME –•– Abba (Atlantic)</td>
  </tr>
</table>

Okay, let's get back on track...

So which (:Activity) should get credit - the last touch? the first touch? multiple touches?

One of the really great things about Neo4j is that time is represented in UNIX epoch format, which means that you can directly operate on time values. Here's our result in table format, sorted by [:TOUCHED] timestamp in descending order:

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

The starting point is to make collections of [:TOUCHED] timestamps, and then sort them using the apoc.coll.sort() procedure:

```
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, collect(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
RETURN i.firstName, touches, touchSeq  LIMIT 10
```

This produces collections for each (:Individual), with the oldest timestamp at touchSeq[0] and the most recent timestamp at touchSeq[touches-1]:

```
rerun using touchSeq

╒═══════════╤═══════╤═════════════════════════════════════════════════════════════════════════════════════════╕
│i.firstName│touches│touchColl                                                                                │
╞═══════════╪═══════╪═════════════════════════════════════════════════════════════════════════════════════════╡
│Michel     │5      │[683214895624, 1127426290931, 1291272829003, 1022527753486, 1147267584540]               │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Lelia      │5      │[773610084727, 1236021026000, 1397203487581, 996162214244, 1069739471934]                │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Julie      │9      │[741878204719, 1016436036278, 1422497088344, 1413566631375, 1370401727621, 1361081390290,│
│           │       │ 1349002092720, 1155688166191, 787410706000]                                             │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Grady      │8      │[892339299937, 632188698743, 1210582690808, 1015726257805, 1376076806159, 1169231572498, │
│           │       │1084620820709, 1166570106468]                                                            │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Bridie     │5      │[1424960410657, 1352584281748, 698291669105, 1438324410676, 827463700452]                │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Adrain     │3      │[1315105479995, 1433439883470, 1090639800509]                                            │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Greyson    │2      │[1202749235437, 1429128653726]                                                           │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Earnestine │1      │[774153831192]                                                                           │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Carlee     │3      │[1365162376421, 1471502656954, 508051588542]                                             │
├───────────┼───────┼─────────────────────────────────────────────────────────────────────────────────────────┤
│Burley     │2      │[1363063898626, 1370542711963]                                                           │
└───────────┴───────┴─────────────────────────────────────────────────────────────────────────────────────────┘

```

Now it's a simple matter to find the appropriate (:Activity) by [:TOUCHED] timestamp using touchSeq[], and set the attribution model (:Lead)-[:ATTRIBUTED_TO]->(:Activity).

```
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[touches-1]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'lastTouch', attributionTouchTime: touchSeq[touches-1], attributionTouchSeq: touches, attributionTimeSeq: 1, attributionWeight: 1.0, attributionTouches: touches}]->(a)

```

For lastTouch attribution, which gives 100% credit to the most recent activity, we find the [:TOUCHED] relationships that satisfy `t.timestamp = touchSeq[touches-1]` and assign an attributionWeight = 1.0.

Here's the complete query:

```
//lastTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[touches-1]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'lastTouch', attributionTouchTime: touchSeq[touches-1], attributionTouchSeq: touches, attributionTimeSeq: 1, attributionWeight: 1.0, attributionTouches: touches}]->(a)

```

For firstTouch attribution, which gives 100% credit to the oldest (first) activity, we find the [:TOUCHED] relationships that satisfy `t.timestamp = touchSeq[0]` and assign an attributionWeight = 1.0.  

```
//firstTouch
MATCH (:Activity)-[t:TOUCHED]->(i:Individual)-[:CONVERTED_TO]->(:Lead)
WITH i, count(*) AS touches, COLLECT(t.timestamp) AS touchColl
CALL apoc.coll.sort(touchColl) YIELD value AS touchSeq
MATCH (a:Activity)-[t:TOUCHED]->(i:Individual)-[c:CONVERTED_TO]->(l:Lead)
WHERE t.timestamp = touchSeq[0]
MERGE (l)-[m:ATTRIBUTED_TO {attributionModel:'firstTouch', attributionTouchTime: touchSeq[0], attributionTouchSeq: 1, attributionTimeSeq: touches, attributionWeight: 1.0, attributionTouches: touches}]->(a)

```

For linearTouch attribution, which evenly distributes credit across activities, we'll create a sorted collection of timestamps and we'll also generate a RANGE of integers from [1..touches] that we'll use as index values for accessing touchSeq[] timestamps for matching.

find the [:TOUCHED] relationships that satisfy `t.timestamp = touchSeq[touches-seq]` and assign an attributionWeight equal to 1/touches

note: update python nb remove RANGE

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

For expDecay attribution

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

```


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
