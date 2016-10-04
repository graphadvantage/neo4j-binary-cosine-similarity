##Neo4j GraphGist - Marketing Recommendations Using Last Touch Attribution Modeling and k-NN Binary Cosine Similarity

# Neo4j Use Case: Real Time Marketing Recommendations


#Part 2. Neo4j Marketing Recommendations

In Part 1 we took a look at how to implement marketing attribution models in a Neo4j graph to enable us to determine which marketing activities are driving leads.  We produced a graph with this basic structure, where each (:Lead) has been [:ATTRIBUTED_TO] one or more of the (:Activity) nodes with a [:TOUCHED] relationship to the (:Individual) :

![attribution](https://cloud.githubusercontent.com/assets/5991751/19056221/c9f9114c-897c-11e6-8107-eab4354ee990.png)

So for the (:Individual) that has NOT [:CONVERTED_TO]->(:Lead) which is the best next (:Activity)?

We'll solve this using a collaborative filtering technique called k-nearest neighbors (k-NN).  We'll compute the cosine similarity across all (:Individual) nodes, using their history of marketing touches as the basis for the similarity measure.

For more background see the excellent GraphGist by Nicole White where she uses k-NN and cosine similarity to compute movie recommendations.

http://portal.graphgist.org/graph_gists/movie-recommendations-with-k-nearest-neighbors-and-cosine-similarity

Cosine similarity is the angle between two vectors in n-dimensional space, and ranges from -1 (exactly dissimilar) to 1 (exactly similar).

It is typically calculated as the dot product of the two vectors, divided by the product of the length of each vector (where the length of each vector is the square root of the sum of squares).

To

![similarity-eq](https://cloud.githubusercontent.com/assets/5991751/19095909/94375fe2-8a4d-11e6-91ad-ceff4c92549a.png)

![similarity-example-eq](https://cloud.githubusercontent.com/assets/5991751/19095933/b4148cae-8a4d-11e6-9855-66f61f8fb245.png)


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
