# neo4j-binary-cosine-similarity
Neo4j GraphGist - Marketing Attribution &amp; Recommendations Using k-NN Binary Cosine Similarity

Part 1.
Neo4j Marketing Attribution Modeling

> "I'm wasting half of my marketing budget, I just don't know which half! - John Wanamaker"

The main goal of marketing is to create demand - doing lots of messaging across different marketing channels, trying to convert individuals to leads. And when an individual does convert (perhaps by adding an item to a cart or filling out a form), the next question is -- which of the various marketing activities (an email, an ad, an event, a webinar, a website visit, a social share, etc) that touched the individual should get the credit?  This is known as marketing attribution - a hotly debated topic.  Marketing attribution is often modeled as a sequence of weighted touches, computed across for each individual.

Some example attribution models are:

 * First Touch - the first marketing touch gets 100% credit
 * Last Touch - the last marketing touch gets 100% credit
 * Linear - credit is evenly allocated across all touches
 * Time Decay - credit is allocated using a time-dependent function

https://support.google.com/analytics/answer/1662518?hl=en

In Part 1. of this GraphGist I'll show you how we can leverage relationships to compute marketing attributions, using multiple simulataneous models - a formidable task for a typical SQL database, but very straightforward in Neo4j.  In Part 2, we'll use the marketing attribution models to provide personalized marketing recommendations for individuals who have not yet converted to a lead.

*Table 1 OTUs Expression of Binary Instances i and j*
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


Part 2.
Neo4j Marketing Recommendations
