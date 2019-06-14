# LiDAR Data and Contours in QGIS 2
@date_created = 2017-08-19  
@author = Joe McGrath  
@description = A guide to visualising LiDAR and creating contours in QGIS 2.
@keyword = QGIS
@keyword = QGIS 2  
@keyword = LiDAR
@keyword = Contours
@keyword = Guide
@finished = True

*Note - this was written for QGIS 2 and hasn't been updated for QGIS 3.*

![An example output of LiDAR data.](img/qgis-2-lidar-example.jpg)

## Getting LiDAR into QGIS

Most sources of LiDAR data I've seen (and raster data in general) comes split into tiles for a number of reasons. This does causes us a few problems when using the data:

* If the files don't have a projection assigned in a way your GIS understands (which they probably won't), then importing tile-by-tile manually can take a *long* time and isn't a good use of anyones time. This is the same for both QGIS and MapInfo when I tried it.
* When those tiles have been imported, they're treated as separate layers, so getting a consistent theme is difficult and more advanced visualisation (e.g. histogram stretch) is impossible.

There's a few ways to solve this, but the simplest I know of is to build a virtual raster / raster catalog. This is basically a small file that acts as an intermediate and allows a set of tiles to be treated as a single file. It can do a couple of fairly clever things with different resolutions and projections - but for the simple purpose of merging LiDAR tiles we don't need that.

The processing steps to create a virtual raster are:

1. Extract all of the data if you haven't already, preferably in a single folder.
2. In QGIS go through Raster -> Miscellaneous -> Build Virtual Raster (Catalog)
3. Use the 'Input files' dialog to select all of your input files.
4. Choose a name for the output.
5. Set the 'Source No Data' (The value that is used to represent a lack of data for a specific cell) and 'Target SRS' values (The projection the files use).
    * For Environment Agency LiDAR these are -9999 and EPSG:27700 (British National Grid) respectively.
6. Press 'OK'.
7. After you've created the virtual raster you might want to save it to it's own file (e.g. a geotiff) for a few reasons:
    * The single file's a lot more transferable.
    * More programs have support for single-raster files then virtual ones.
    * In my experience, features like pyramids work a bit more consistently on single files.

![The Build Virtual Raster menu in QGIS.](img/qgis-2-build-virtual-raster.jpg)

From this image, you can see an example. The big box full of file paths is a bit of a giveaway to what's *actually* happening here. One of the major open-source components of QGIS is *GDAL*, which handles the bult of raster processing. In this example, QGIS is acting as an intermediary between the user and gdalbuildvrt which actually builds the virtual raster.

## Displaying the LiDAR

As an example I'll assume the desired output is a hillshade (aka shaded relief) with height themed by colour and contours over the top.

### Theme by Height (pseudocolour)

The simplest of these is elevation themed by height. The previous step should have loaded the data into QGIS (if it hasn't you should be able to load it through the 'Add Raster Layer' menu), so go into the layer properties for the LiDAR data:

1. In the 'Style' tab of layer properties, it should say 'Singleband gray' near the top, this just displays the image as greyscale. Instead choose 'Singleband Pseudocolor' which lets you apply a colour ramp to the data instead, so switch to that.
2. The 'interpolation method' probably wants to be linear, though you could get some interesting results with discrete values combined with contours.
    * **Linear** interpolated grades the colour between break points.
    * **Discrete** uses the same shade for all values between two break points.
    * I wouldn't advise it for this use-case, but **Exact** themes only values matching a criteria (you could use it to create some very ugly almost-contours if you really wanted but the mode's more for classified rasters).
3. Choose a colour ramp - I normally go for a monochrome one, e.g. the greens above.
    * While 'spectral' does give very good distinction between values - rainbow maps are something of a mapping faux-pas and won't help your colourblind users much.
4. If needed, you can invert the colour ramp and manually define break points in this menu (particularly suggested if you're going to put the colour ramp on a legend to avoid weird units).
    * And you can set a 'Label Unit suffix' so it shows up as something like '140 m AD' rather than just '140'.
5. Press ok or apply (you might need to go back and forth to find a scheme that works for you).

### Hillshade

Hillshading is very simple in newer versions of QGIS.

1. Create a duplicate of the LiDAR layer (right click, then 'Duplicate').
2. Rather than 'Singleband Pseudocolor' use 'Hillshade'
3. Most of the default settings should be fine.
   * I'd advise having the 'Azimuth' coming in from the top-left, otherwise terrain can appear inverted.
   * You may need to play around with the 'Altitude' and 'Z Factor' (virtical exaggeration) setting, particularly in hilly areas.
4. Set the 'Blending mode' beneath the hillshade options to 'Multiply'
5. Press ok.
6. Make sure that the hillshade layer is above the pseudocolour layer in the legend.

In older versions, there's an option to create hillshades using the 'Raster Terrain Analysis Plugin' which may need to be installed if it's not already in the 'Raster' menu.

A note of caution for calculating hillshades on the fly - it re-calculates itself dynamically, so if you're planning to view the data up-close you're better off pre-calculating it through the Terrain Analysis Plugin. Otherwise if you zoom in far enough to see individual pixels then they get shaded as if they're cuboid blocks. You can see a little bit of this effect in the buildings shown at the top of the page.

## Creating Contours

Contours are fairly simple to create in QGIS, but need a little editing if you want something for presentation:

1. Go to Raster -> Extraction -> Contour.
2. Set the input file to your LiDAR.
3. Choose an output file.
4. I'd advise setting elevation to an attribute.
5. Press 'OK' - processing might take a few minutes depending on how much data you're using.

### Cleaning up the Contours

On fine-scale data like most LiDAR, you might find that the contours produced are a little on the noisey side. The most effective way to clean this up is to delete all of the short contours. To do this, use the 'Select by Expression' tool:

![The location of the 'Select by Expression' dialog menu in QGIS.](img/qgis-2-select-by-expression.jpg)

I prefer to use an expression that makes a distinction between lines that form closed contours and ones that don't (meaning that contours at the edge of your data have a bit more leeway to be short):

```qgis
(is_closed( $geometry ) AND $length < 350) OR $length < 100
```

All of the variables in QGIS with a dollar sign ($) in front of them are calculated variables that all features with a geometry have. The two used here are *$length* - the length of the line as a number and *$geometry* which gets passed to functions expecting a geometry, in this case is_closed which returns *true* if the line forms a closed loop.

Then delete all of the lines selected by this (you'll need to set the layer to editable). Though an alternative approach would be to select all of the contours you want to *keep* (e.g. length > 100) and save them as a new layer.

The default theme for lines in QGIS is a semi-random colour of medium width, which probably isn't what you're after. I normally go for semi-transparent black lines with height labels.

## Additional notes.

### LiDAR types.

The distinction between DSM (Digital Surface Model) and DTM (Digital Terrain Model) is pretty important for this type of work. A surface model will include buildings and trees and make a very messy set of countours - so I'd advise a terrain model which has those features processed out. My personal preference is to use a surface model for the hillshade, but a terrain model for both the pseudocolour layer and contours. That avoids both the messy contours of a DSM and the unnatural flat areas where buildings were removed from the DTM.

### Blend Modes

Rather than using blend modes, an alternative to show both the elevation and hillshade would be to use transparency with a  'normal' blend mode. This gives a desaturated look that I've always thought of as a bit 'plastic'. This has the advantage of showing up contour lines a bit better no-matter what your colour ramp is. There's a comparison of the two below:

![A comparison of different methods of stacking hillshades with pseudocolour imagery.](img/qgis-2-lidar-blend-comparison.jpg)

### Further Contour Processing

When you zoom further in to the contours they might start to look a bit blocky (which makes sense - they came from blocks in the first place). The easiest way to get rid of this is with the smoothing tool, for which you'll need to be using QGIS with GRASS (GRASS is another open-source program that QGIS uses for additional functionality). In the processing toolbox (processing -> toolbox) and search for v.generalise.smooth. There is a smoothing function built into QGIS - but it doesn't seem to give as good results for this task.

I've put together a comparison of the algorithms on a set of contours (not including the 'snakes' algorithm which caused QGIS to crash whenever I tried it):

![An example of the boyle smoothing algorithm available through GRASS.](img/qgis-2-lidar-smoothing-comparison-boyle.jpg)  
![An example of the sliding average smoothing algorithm available through GRASS.](img/qgis-2-lidar-smoothing-comparison-sliding-average.jpg)  
![An example of the distance weighting smoothing algorithm available through GRASS.](img/qgis-2-lidar-smoothing-comparison-distance-weighting.jpg)  
![An example of the chaiken smoothing algorithm available through GRASS.](img/qgis-2-lidar-smoothing-comparison-chaiken.jpg)  
![An example of the hermite smoothing algorithm available through GRASS.](img/qgis-2-lidar-smoothing-comparison-hermite.jpg)  

From these, I'd personally choose the 'distance weighting' algorithm as it seems to produce the smoothest results (assuming aesthetics are the only aim here) with 'chaiken' being a good candidate for maintaining shape. Though it's worth pointing out that these algorithms are topologically 'dumb' and don't care if the smoothing causes contour lines to cross themselves or other lines.
