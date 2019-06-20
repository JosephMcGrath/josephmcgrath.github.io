---
title: Geology and Geomorphometry
author: Joe McGrath
description: Scraping information out of video games to produce maps.
date_created: 2019-05-11
keyword: Python
         Tesseract
         Fictional Mapping
         Subnautica
         Subnautica Below Zero
finished: False
---
# Under the Sea: Mapping Subnautica

## Overview

I've been building a simple system to scrape information out of a game I've been playing ([Subnautica](https://unknownworlds.com/subnautica)) and generate a map out of it. The high-level view of the methodology is:

1. Play the game with the technical information open (includes in-game coordinates and other technical information),
2. Capture images of the technical information,
3. Convert those images to text via OCR,
4. Extract the information I want out of this text,
5. Visualise the output,

The main sticking point is converting a screen-shot into text. To do this I chose [Tesseract](https://en.wikipedia.org/wiki/Tesseract_(software)), mainly because it has simple Python bindings and it seems to have fairly widespread use.

The code is available [here](link_to_the_repo) but I thought it would be interesting to go over a few of the design choices & hurdles here.

*Also I am aware that it's possible to pull the game's data apart and that the developers have published details of it's structure [with an explanation here](https://unknownworlds.com/subnautica/terrain-data-format).*

## Two-Part Solution

One of the things that quickly became apparent is that my computer's not nearly powerful to run Tesseract in real time at the temporal resolution I was aiming for. Depending on how much I was messing around with the screen-shots it could take several seconds for the process to run end-to-end which ended up with too sparse a map. The bits of post-processing I was doing taken a trivial amount of time but going from an image to text was the bottleneck (understandably).

To get around this I split my script into two separate parts. The first taken screen-shots as fast as it could and saved them to disk. The second could then do the processing at a slower pace and could be left running to pick up the excess. This approach also had the advantage of leaving me with a test data set that I could to improve the processing script at my leisure. This also meant I didn't have to mess around trying to optimise Tesseract - I don't need it to be quick and would rather spend my time cleaning up the data.

## Generalised OCR

The first version of my screen-shot OCR script was full of hard-coded variables and specialised functions. When I came to re-write the problem could be boiled down to a case of running the output text through [some simple regular expressions](https://xkcd.com/1171) to ensure I had a valid output. When I did this I divided the parts of the screen-shots that were required data (mainly coordinate) and parts that were nice but not actually required (the game includes a lot of technical information, like release version and in-game biome).

The approach I ended up with had a JSON config file that listed out a series of fields, with a regex pattern that identified the part of the text that contained the data and then another piece of regex that could be used to extract the data itself. For example this chunk extracts the position of the player (listed as a series of three decimal numbers):

````JSON
{
  "name": "Position",
  "pattern": "(?i).*pos: (.*).*",
  "extract" : "\\-?[\\d|\\.]+"
}
````

This would allow me to define an different config file to extract almost any text out of a game. For that matter the approach could easily be generalised to extract data from text in images. For now I'm more than happy with my current application.

## Preprocessing the Images

I think the biggest learning curve here was pre-processing the imagery. All of my previous experience with raster manipulation is remote sensing imagery in R so I had to
