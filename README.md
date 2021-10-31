
# My CV

-   My CV can be downloaded [**from
    here**](https://dominiquemakowski.github.io/CV/).
-   More information can be found on [**my
    website**](https://dominiquemakowski.github.io).

[![](img/preview.png)](https://dominiquemakowski.github.io/CV/)

## Steps

The steps to pull the data from Google scholar and render the CV are the
following:

``` r
# 1. Update scientific impact data
source("make_data_impact.R")

# 4. Render CV (and CV-data)
rmarkdown::render("C:/Dropbox/PERSO/CV/DominiqueMakowski_CV.Rmd", encoding = "UTF-8")
```

## Research Wordcloud

<figure>
<img src="https://raw.githubusercontent.com/DominiqueMakowski/CV/main/img/wordcloud.png"/>
<figcaption>
My research wordcloud, generated from the most frequent words present in
my publications.
</figcaption>
</figure>

## Impact

<img src="img/scientificImpact-1.png" style="display: block; margin: auto;" />

## Collaboration Network

The data is retrieved from the Google Scholar co-author list (that one
must update ***manually*** on its scholar profile by clicking the `+`
button and accept the suggestions), thus not 100% accurate (e.g.,
co-authors without a scholar profile are not listed).

<figure>
<img src="https://raw.githubusercontent.com/DominiqueMakowski/CV/main/img/collaboration_network.png"/>
<figcaption>
My coauthors network, based on Google Scholar data.
</figcaption>
</figure>
