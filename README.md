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
print("k-NN using Binary Cosine Similarity and Last Touch Attribution")
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
