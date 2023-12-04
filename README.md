# Analysis of Marx's Letters

This is the final project for Dr. Jessy Li's `LIN 350: Analyzing Linguistic Data`, Fall 2023 course.

In this project, we scrape the letters found on the (*Marx-Engels-Gesaumtausgabe*)[https://megadigital.bbaw.de/briefe/index.xql],
and then perform the following tasks.

The first is to attempt authorship classification by means of tf-idf and word-frequency. The results are a bit unfortunate,
as the kmeans clustering was unable to effectively classify the unique authors- we hypothesize that this is due to the fact
that there were too many authors, yet the distribution of texts was non-uniform.

The second task was to attempt to predict historical events based upon the sentiment of the letters. We did find a statistically 
significant result, and it seems that historical events do have some correlation to the sentiment.
