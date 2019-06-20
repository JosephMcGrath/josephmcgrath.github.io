---
title: Version Control for GeoJSON with Git
author: Joe McGrath
date_created: 2018-09-15
description: Generating simple overviews with GPS data.
keyword: Git
         GIS
         QGIS
         GeoJSON
         Version Control
finished: True
---
# Version Control for GeoJSON with Git

# Introduction

As an experiment, I've been trying out storing data for a small personal project as a GeoJSON and using Git to do version control across the data set. I've heard mixed results about using Git on data so figured this was a low-risk way of trying it out for myself.

My current GIS platform of choice is QGIS, but in theory there's nothing stopping me using any other GIS that accepts GeoJSON here.

## Naive QGIS Output

First out, I tried just initialising a Git repo on my data folder, editing Adobe data and looking at the diffs. This came out with 2 problems:

* QGIS saves GeoJSON to 15 decimal places. As I'm using British National Grid, this ends up being sub-picometer detail. I have absolutely no need for this and it inflates file sizes dramatically.
* Each feature is saved on a single line. This isn't a problem per se but means that *any* changes to a feature mean the whole feature (all properties and all coordinates) is marked as a diff. This makes actually spotting changes difficult.

## Parsing the Output

My solution to this problem was to write a [quick Python script](https://github.com/JosephMcGrath/Misc-scripts/blob/master/python_3/reformat_geojson/reformat_geojson.py) to reformat the GeoJSON to better fit my needs by rounding off coordinates to the nearest cm and splitting each feature over multiple lines.

As GeoJSON is still JSON, I just used the standard JSON library for Python. The main tricky part was customising the somewhat over-the-top indentation as the library applies. My ideal was to have each property value on its own line and each coordinate pair as it's own line. This should ensure that it's easy to spot the actual changes in Git.

After a bit of hacking around, I ended up using regex on the string output to find arrays consisting of only numbers, and collapsing that to a single line. I'm not that keen on editing a data structure as plain text - but I'm keeping it as simple as possible so there's less room for mistakes.

A few other steps I taken to help Git look after my data sensibly:

* Used the OrderedDict class of the Collections library to prevent properties getting muddled during their brief residence as a dict and showing up as false positives for changes.
* Sorted the features by their unique id values to prevent a change in feature order showing up as a change to the data.

In terms of file size, all of the additional whitespace is almost exactly offset by the reduction in coordinate precision, so no massive increases in file size (though I've not done any quantitative testing there).

A side-effect of this that I'm really finding useful is the ability to roll back a batch of changes, particularly bulk edits - so I think I might be a convert to this workflow (though I've not tested performance on larger data sets).

## Future Steps

There's a few other steps I've been considering if I was going to roll this out to a production environment:

* I'd probably use a UUID rather than numeric ID. If multiple people are using and branching the data set out then there's a high likelihood of collisions. UUID values would fix this, but remove any natural ordering to the data. I suspect managing branching datasets is a lot more complex than this - but it's a better foundation at least.
* As all of the workspace/style files produced by QGIS are XML, they can be rolled into the same Git repo too. The only problem I've noticed is that the ordering of properties is non-deterministic, so there's a lot of false-positives with change detection. A similar preparatory script might be used here with the advantage of also hitting a whole life of other files, like GML.
* There *might* be some scope for linting / validating the data. I'm not really sold on this as it starts to fragment data processing. The only real processing I've considered is to tidy up whitespace in string properties.
* Rather than *working* in GeoJSON, another possible workflow might be to use a higher-performance format while editing, but dumping changes out to GeoJSON - this comes with it's own set of problems, particularly for multiple users.
