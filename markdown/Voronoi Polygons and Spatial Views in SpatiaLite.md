# Voronoi Polygons and Spatial Views in SpatiaLite
@author = Joe McGrath
@date_created = 2018-05-15
@description = Creating Voronoi polygons live in SpatiaLite with examples.
@keyword = SpatiaLite
@keyword = Voronoi
@keyword = QGIS
@keyword = QGIS 2
@keyword = QGIS 3
@keyword = Spatial Views
@keyword = SQL
@keyword = Guide
@finished = True

![An example set of voronoi polygons created using the mechanism outlined below.](img/voronoi_example.jpg)

## SpatiaLite

[SpatiaLite](https://www.gaia-gis.it/fossil/libspatialite/index) is an extension for the widely used SQLite database. Like it's . It's open-source and provides reasonable support for spatial SQL in a portable format. It also has a bit of history with the open-source desktop GIS QGIS and works well with it once you get to grips with how they expect to work together.

Here I'm running through [some code](https://github.com/JosephMcGrath/Misc-scripts/blob/master/SQLite/Voronoi_View.sql) I wrote a while back in a little more detail.

## Spatial Views

When I talk about spatial views, I mean a standard SQL view that has an attached geometry (particularly views that generate their own geometry, rather than just passing through a base column). There's nothing special about a spatial view in database terms, it's just a label applied for making the view accessible in a GIS as a typical 'layer'. In this example I'm going through creating a set of Voronoi Polygons for a set of points in SpatiaLite.

It's fairly easy to create a spatial view - but making it usable in QGIS requires it to be registered first. The requirements for this are:

* The layer must have an entry in the ````views_geometry_columns```` table that's part of the SpatiaLite extension. This needs:
    * The name of the view.
    * The name of the geometry column in that view.
    * The row id for that view.
    * The name of a base table containing a geometry of the same type (ostensibly this is the table that the view is 'based on' - more on this later).
    * The name of the geometry of the same type as the view in the named table.
* The layer to be one QGIS is happy to work with:
    * Requires a numeric primary key.
    * Must be loaded as a *SpatiaLite* layer rather than a generic vector one (for most things other than just looking at the layer).

## Voronoi Polygons in SpatiaLite

SpatiaLite has [a function](http://www.gaia-gis.it/gaia-sins/spatialite-sql-4.2.0.html#p14c) that generates voronoi polygons. ````VoronojDiagram```` is not that convenient for everyday use as it takes a single multi-geometry (probably a multi-point) and outputs a single multi-polygon. In most cases what we want is to push in a table of points and return a table of polygons and it's not too difficult to manually do this.

As an experiment I tried to create a database view that directly converts a table of points into a set of voronoi polygons 'live'. As the points are altered, the polygons change with the output visible in QGIS. The example I've written goes slightly beyond this and allows for multiple sets of points in a table, each with it's own set of voronoi polygons.

The set of operations is going to be:

1. Merge the inputs into a single multi-geometry for each set.
2. Create the voronoi diagrams.
3. Split up the multi-polygon outputs.
4. Re-attach all the data that was attached to the point.
5. Register the output as a spatial view.

But first, we need some data to work with. I'm just using a set of randomly generated points.

### Generating Example Data

The table ````base_point```` is the stand-in for an actual input data.

````sql
CREATE TABLE base_point (
    pid INTEGER PRIMARY KEY
  , point_set INTEGER NOT NULL /*A Vorojoi diagram will be created for each unique entry in this column.*/
  , some_data VARCHAR /*Some example data to attach to the outputs.*/
  , the_geom POINT
);
````

Then registering this base table so it's visible in QGIS (27700 is the reference id for British National Grid). I tend to use the ````RecoverGeometryColumn```` function to register base geometry columns rather than modifying the ````geometry_columns```` table as it takes the inputs as text rather than a lookup value for each geometry type. It also lends itself to generating a spatial index at the same time.

````sql
SELECT
    RecoverGeometryColumn('base_point',
                          'the_geom',
                          27700,
                          'POINT',
                          'XY'
                          )
  , CreateSpatialIndex('base_point', 'the_geom');
````

Then generating a set of points to work with. Because of the size of number ````RANDOM()```` generates, they need to be divided down to values that fit in a reasonable area:

````sql
/*Populate with random points.*/
INSERT INTO base_point
    (point_set, some_data, the_geom)
VALUES
    (1, 'Data', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'in', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'this', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'column', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'will', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'be', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'preserved', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (2, 'through', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (2, 'the', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (2, 'Vorojoi', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (3, 'creation', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (3, 'process', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (3, 'and', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (3, 'added', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (4, 'to', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (2, 'the', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700))
  , (1, 'output', MakePoint(ABS(RANDOM() / POWER(10, 16)), ABS(RANDOM() / POWER(10, 16)), 27700));
````

One additional spanner I'm throwing in the works is the fact that, in normal usage rows will be deleted out of the base points. If this wasn't the case, splitting up the voronoi polygons later would be a bit simpler and process quicker.

````sql
DELETE FROM base_point WHERE pid = 2;
````

### Merging the Inputs and creating the polygons

Merging the inputs and generating the raw voronoi polygons is simple enough to do in a single step using ````ST_Union```` and ````GROUP BY````:

````sql
CREATE VIEW voronoi_raw AS SELECT
    point_set
  , VoronojDiagram(ST_Union(the_geom), /*Merge the points for each set into a single multipolygon.*/
                   0, /*We want the polygons, not just the boundaries.*/
                   20 /*Return polygons covering an area 20% larger the input.*/
                   ) AS the_geom
FROM
    base_point
GROUP BY
    point_set;
````

So now we've got a table with one row for each collection of points. The next step is to split them up.

### Splitting the Polygons

The theory of this is really simple. Just use ````GeometryN```` to split the geometries. The problem being that SQLite doesn't natively have any sort of ````generate_series```` function like PostGIS. The naive approach would be to use the pid column like:

````sql
SELECT
    p.pid
  , v.point_set
  , GeometryN(v.the_geom,
              p.pid
              ) AS the_geom
FROM
    base_point AS p
    CROSS JOIN voronoi_raw AS v
WHERE GeometryN(v.the_geom, p.pid) IS NOT NULL;
````

But this assumes that the pid column will be an unbroken sequence from 1 to the number of rows in the table. That's not an *unreasonable* assumption but the moment the input does into actual use, there's going to be missing or out-of sequence values and there'll be missing geometries. It's also arguably breaks the first normal form by assuming a certain order to the rows.

A more robust approach is to use a subquery to generate a set of values based on the number of parts in each geomery.

````sql
CREATE VIEW voronoi_split AS SELECT
    p.pid
  , v.point_set
  , GeometryN(v.the_geom,
              (SELECT COUNT(*) FROM base_point AS x WHERE x.pid <= p.pid)
              ) AS the_geom
FROM
    base_point AS p
    CROSS JOIN voronoi_raw AS v
WHERE
    (SELECT COUNT(*) FROM base_point AS x WHERE x.pid <= p.pid) <= NumGeometries(v.the_geom);
````

So now we've got a view with one row per polygon, but no data attached.

Another way to work it might be to have a pre-generated table of a numbers, but that requires a certain knowledge about the input data set and I'm trying to make something that's theoretically robust - even if it's a little impractical (and makes some scrifices on performance).

### Re-joining the Data

Joining the data from the base point table's very easy. Just a spatial inner join (as the points are guarenteed to be within their own voronoi polygon):

````sql
CREATE VIEW voronoi_out AS SELECT
    p.pid
  , p.point_set
  , p.some_data
  , v.the_geom
FROM
    base_point AS p
    INNER JOIN voronoi_split AS v ON ST_Within(p.the_geom, v.the_geom) AND
                                     p.point_set = v.point_set;
````

And checking the final view:

````sql
SELECT * FROM voronoi_out;
````

Shows we've got all the data through intact. If I was just working in SpatiaLite on it's own this is where the process could stop - but I'm after visualising the results in QGIS.

### Registering the View for use in QGIS

To register a view, we need a base table with a geometry of the same kind. If we had more tables with polygons we *could* register against that - but it starts to build up unexpected dependencies in the database. I favour a table of dummy geometries:

````sql
CREATE TABLE dummy_geom (
    pid INTEGER PRIMARY KEY
  , the_poly POLYGON
);

SELECT
    RecoverGeometryColumn('dummy_geom',
                          'the_poly',
                          27700,
                          'POLYGON',
                          'XY'
                          );
````

Especially combined with the option to hide the registered table by altering the ````geometry_columns_auth```` table:

````sql
UPDATE geometry_columns_auth
SET hidden = 1
WHERE f_table_name = 'dummy_geom';
````

And then it's just a simple ````INSERT```` to register the view:

````sql
INSERT INTO views_geometry_columns
    (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only)
VALUES
    ('voronoi_out', 'the_geom', 'pid', 'dummy_geom', 'the_poly', 0);
````

Which makes it available for viewing in QGIS.

![The QGIS 3 menu for loading the voronoi polygons.](img/voronoi_load.jpg)
