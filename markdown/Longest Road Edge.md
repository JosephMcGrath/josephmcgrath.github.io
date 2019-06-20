---
title: Longest Road Edge
author: Joe McGrath
date_created: 2018-09-25
keyword: Road Edge
         Ordinance Survey
finished: False
---
# Longest Road Edge

## The Idea

I was joking with my brother about a navigation algorithm that [only says 'turn right'](https://en.wikipedia.org/wiki/Maze_solving_algorithm#Wall_follower) when I got to wondering what the longest road edge in the country is (so if you followed it you would be able to get to the most places).

Seeing as navigable road data is readily available, that makes a simple estimate pretty easy - if a bit computationally expensive. My initial thoughts are to:

1. Buffer all the road segments by a small value.
    * Would have to be small to avoid merging adjacent roads.
2. Take the union of those buffers.
3. Extract the boundaries of the single multipolygon as individual linestrings.
4. Calculate the length of those lines.

This method does have a few obvious downsides:

1. The output length is heavily influenced by the size of the buffer.
2. This method only works for navigable roads, so won't include features like car parks.

So with that in mind, it's time to pull out some data.

## Unioned Buffer - Test Area

Rather than roll out my method across the entirety of England right away, I decided to test the methodology on a small area first.

As I don't care about having smooth corners on the output, I'm using mitred corners and flat ends to my buffers. Doing this should save quite a few vertexes over rounded corners over the whole country.

## Checking the Output with OS MasterMap

Luckily the UK has done excellent mapping data in the form of the [Ordinance Survey's MasterMap topography layer](https://www.ordnancesurvey.co.uk/business-and-government/products/topography-layer.html), which has all the needed data to get as close to an actual answer as I'll get without putting my boots on and grabbing a GPS. They also provide a sample area that covers the same area I did my test in - so I can check the worts-and-all length of the road edge.
