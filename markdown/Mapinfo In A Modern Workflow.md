---
title: Mapinfo in a Modern Workflow
author: Joe McGrath
date_created: 2018-10-02
keyword: MapInfo
finished: False
---
# Mapinfo in a Modern Workflow

While my main (and favourite) desktop GIS is QGIS (followed closely by FME), my work often requires me to use Mapinfo. From reading around, it certainly seems to be in a decline and I can certainly see why - where modern GIS seems to have reached a consensus on how a lot of things *should* be, whereas Mapinfo sort of gone it's own way.

While it doesn't deserve a lot of the flack it gets, I wouldn't say it's a better GIS than others on the market. Mapinfo certainly has its share of plus points (mainly its strong SQL integration).

## The Graphical Object

If you're coming from Arc/Q, the main difference you'll find on a day-to-day data creation basis is that rather than setting styles on a layer-by-layer basis, the symbol information is stored as part of the 'Graphical Object' that MapInfo calls geometry + style. This can be nice if you want *this one point* to have a different style to all the others but I personally find it's a massive pain to have to manually maintain the layer styles (though you can update them automatically through scripts).

While this sounds like a pretty trivial change to make, it permeates a lot of the problems Mapinfo has:

* If Pitney Bowes want to update the styles Mapinfo supports
* Importing any data means brings in the results as unstyled geometries
* The ability to manually style geometries seems to have stymied Mapinfo support for thematic maps

## SQL Support
