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

She then sets a (i1:Individual {name:"M.Hunger"})-[:SIMILARITY]->(i2:Individual {name:"M.Sherman"}) relationship and gives it a value of 0.86.

Now movie recommendations can be produced by averaging the movie ratings of the most similar neighbors, and picking the highest rated movies that the target individual has not seen.


##Binary Cosine Similarity: Marketing Recommendations

In the case of marketing activities, we can use cosine similarity but we need to make some modifications to account for how marketing works.

First of all, there's no concept of "rating" - as we saw in Part 1, marketing activities either touch - or don't touch - an individual.

Second, the movie rating case is dealing with exact intersections, whereas for marketing if we compute similarity using the sequence of touches we have to account for intersecting and non intersecting parts of each vector pair.

Here's what we need to solve for - how similar are the touch histories of Nicklaus and Ibrahim?

![touch-vectors](https://cloud.githubusercontent.com/assets/5991751/19096766/f16a2b30-8a53-11e6-9e07-e88c1b75930e.png)

We can consider the two individuals to represent vectors of binary touches for each activity, as shown in table below.

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


In the binary case, the math reduces to be quite simple.

The dot product of i,j becomes (0\*1)+(0\*1)+(1\*1)+(1\*1)+(1\*1)+(1\*0) = 3, or the length of the intersection

The sum of squares of i becomes (0^2)+(0^2)+(1^2)+(1^2)+(1^2)+(1^2) = 4, or the length of i

The sum of squares of j becomes (1^2)+(1^2)+(1^2)+(1^2)+(1^2)+(0^2) = 5, or the length of j

The cosine similarity for (i,j) is  3 / SQRT(4*5) = 0.67

You probably noticed the table row marked "OTU" - this refers to "Operational Taxonomic Units" and is based on an excellent review of binary measures of similarity: http://www.iiisci.org/journal/CV$/sci/pdfs/GS315JG.pdf by Choi et al.

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

a = i • j  (i and j present: 1,1) - the intersection of i, j = 3

b = i̅ • j (i absent, j present : 0,1) - the vector j minus the intersection = 2

c = i • j̅ (i present, j absent: 1,0) - the vector i minus the intersection = 1

d = i̅ • j̅ (i and j absent: 0,0) - all the other data points not included in of i,j

Choi et al provide about 70 measures of similarity and distance, to showcase a few:

Cosine Similarity: a/SQRT((a+b)\*(a+c)) = 3/SQRT((3 + 2)\*(3 + 1)) = 0.67

Jaccard Similarity is: a/(a+b+c) = 3/(3 + 2 + 1) = 0.50

Dice Similarity is: (2\*a)/((2\*a)+b+c) = (2\*3)/((2\*3) + 2 + 1) = 0.66



![neo4j-example-reco](https://cloud.githubusercontent.com/assets/5991751/19052701/a8a35e0e-896c-11e6-89b1-90e4fe480d15.png)


![similarity](https://cloud.githubusercontent.com/assets/5991751/19054363/f896d038-8973-11e6-956e-c1014bedbe58.png)
