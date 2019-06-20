---
title: Geology and Geomorphometry
author: Joe McGrath
date_created: 2018-05-12
keyword: Geology
         Geomorphometry
         Geomorphology
finished: False
---
# Geology and Geomorphometry

## Introduction

This is something of a rehash / autopsy of my postgrad dissertation. The basic idea was trying to identify & exploit a link between the structure of the land and the underlying geology (and also how the geology dictates landforms). My original methodology had some fairly major issues, so this is a mix of 'what I did' and 'what I'd do another time'.

## The Theory

The core bit of theory here is that the different type of rock will erode in a different (and ideally charictaristic) way. The problem comes with the fact that there's a *whole* range of factors that play into erosion and interfere with getting a clear signal.

### Rock Type

Depending on the context, there's a few ways to define the 'type' of a rock. Normally the origin or mineralogy would be a good place to start - but to a certain extent, we're not that worried about that. The main property of rocks that we're interested in is the way in which they erode.

### Erodability

I have a fairly limited training in the theory of erosion but as I see it, the main factors are:

* The meso-scale properties of the rock.
    * Prone to fractures etc.
    * Chemistry -
* The environment the rock's in.
* Location-specific issues.
* Human interaction.

## Measuring Surface Shape

The main practical way I've looked at the shape of the ground is using LiDAR data. In my dissertation I used a patch of data from Cyprus, but there's plenty of other areas covered by LiDAR.

### Parameters

The problem with using LiDAR is that the raw values aren't that useful - the raw elevation values *might* have some very coarse-scale applications, but I've not tested. As a result, we've got to derive something from the data. The approach I taken was to pass a window over the LiDAR and use it to calculate a variety of parameters.

A other angles that I've not explored yet are:

* Fuzzy terrain analysis in the style of Fisher.

#### Scale

The way I approach the measurement of the land surface is highly dependent on the size of the window being pushed over the elevation data - adding another dimension to the search-space.

#### Parameters
