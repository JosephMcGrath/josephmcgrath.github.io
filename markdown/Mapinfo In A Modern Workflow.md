---
title: MapInfo in a Modern Workflow
author: Joe McGrath
date_created: 2018-10-02
keyword: MapInfo
         MapBasic
         SQL
         GIS
finished: False
---
# MapInfo in a Modern Workflow

- Need to justify the title,

While my main (and favourite) desktop GIS is QGIS (followed closely by FME), my work often requires me to use MapInfo. From reading around, it certainly seems to be in a decline and I can certainly see why - where modern GIS seems to have reached a consensus on how a lot of things *should* be, whereas MapInfo sort of gone it's own way.

While it doesn't deserve a lot of the flack it gets, I wouldn't say it's a better GIS than others on the market. MapInfo certainly has its share of plus points (mainly its strong SQL integration).

## The Graphical Object

If you're coming from Arc or QGIS, the main difference you'll find on a day-to-day data creation basis is that rather than setting styles on a layer-by-layer basis, the symbol information is stored as part of the 'Graphical Object' that MapInfo calls geometry + style. This can be nice if you want *this one point* to have a different style to all the others but I personally find it's a massive pain to have to manually maintain the layer styles (though you can update them automatically through scripts).

While this sounds like a pretty trivial change to make, it permeates a lot of the problems MapInfo has:

* Any updates that are made to the styling of a layer are kinda tied to the version of MapInfo, potentially breaking backwards compatibility for a data file,
    - The dependence of point symbols on fonts mitigates this,
* Importing any data means brings in the results as un-styled geometries,
* Limited interoperability with other GIS,
    * While QGIS is pretty happy to work with TAB files (using a .qml, .qlr etc file), MapInfo interprets any external data source as monochrome polygons / stars,
* The ability to manually style geometries seems to have stymied MapInfo support for thematic maps,
    * It does have *ok* support but it's definitely feels like a second-tier of functionality,
- Bizarre quirk with labels not being part of the core styling,
    - Limited label length??
- About 50 software-specific geometry types,

Within it's own system, MapInfo's fairly capable of decent-looking outputs, though it is heavily reliant on pre-built styles. Luckily a lot of this hassle can be bypassed with FME's MapInfoStyler transformer.


## MapBasic

- Proprietary language, limited resources,
- Interactive prompt,
- Useful tricks:
    - Updating themes by defining a function, then calling it with an UPDATE statement,
    - Multi-file projects,
- Jump to ribbon interface breaking the UI,

### SQL Support

MapInfo integrates SQL directly into it's own programming language. While it's convenient not to have to define a statement and then execute it, there seems to be an intermediate level of processing that can lead to some ambiguity on what's a string or a column or a keyword in some more complex setups.

- alias data type and it's tiny size limit.
- WHERE clause on UPDATE

## The Interface

### Windows

### Ribbon Interface

- The general UX downgrade that is the ribbon interface,
    - Functionality is split up - context-switching to unhelpful ribbon tabs,
    - useful functionality being hidden a few layers down,

![X](/img/mapinfo_ribbon_map.jpg)
![X](/img/mapinfo_ribbon_spatial.jpg)
