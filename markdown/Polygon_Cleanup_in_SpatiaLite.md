---
title: Polygon Cleanup in SpatiaLite
author: Joe McGrath
date_created: 2018-05-22
keyword: SpatiaLite
         Data Cleanup
finished: False
---
# Polygon Cleanup in SpatiaLite

A problem I've came across a few times recently is digitising a clean set of polygons covering an entire area. The comprehensive solution would be to use some topology-based storage - but a  solution with minimal setup would also be nice. SpatiaLite has most of the functions needed to piece this together, just needs putting together.

## Defining the Problem

The plan is to end up with a trigger that I can just throw data at, seamlessly doing the following:

* Snapping to adjacent polygons.
    * The difficulty here is work out a general-purpose tolerance - maybe use ````CASE```` to have a few.
* Not covering existing polygons.
* Only produces valid polygons.
* **Never** breaks in a way that an edit will be lost.
    * At least they never just disappear into the aether. Might be acceptable to have a 'rejects' table.
* Bonus points if the result is uniformly oriented in the style of [ST\_ForceRHR function](https://postgis.net/docs/ST_ForceRHR.html) PostGIS.

I'm thinking that this will be defined for triggers on both the insert and update operations, probably attached to a view that mirrors the main table itself.

# The Tools

The relevant functions would be:

* ````ST_Snap```` - Snaps one gemetry to another.
    * In this case the 'other' is going to be the other nearby geometries with ````ST_Union````.
    * For the sake of speed, probably filter for nearby geometries with ````PtDistWithin````.
* ````ST_MakeValid```` - Makes the geometry valid.
* ````ST_ForceLHR```` - Standardises winding direction of the polygon.
    * Despite the name, the description seems to indicate it has the same properties of the function with the opposite name in PostGIS (Exterior Ring clockwise).
    * Seems to go with a theme in SpatiaLite of using *slightly* different names to everything else.
* I was thinking about using ````ST_SimplifyPreserveTopology```` - but that starts to take the geometry further away from the input than I'd like.
    * Particularly as geometries are going to be cleaned up sequentially, this might mess up junctions particularly.
* A latecomer to my list of functions was ````SanitizeGeometry```` to remove duplicate vertexes.
* To ensure the new polygons don't overlap existing ones, ````ST_Difference```` can be used to drop anything covering an existing geometry.
    * Though this step could end up producing NULL geometries or weird multi-part slivers.

## Exploring Options

While I'm experimenting, I'll just have the base-minimum table to test out ideas:

```sql
CREATE TABLE base_polygons (
    pid INTEGER PRIMARY KEY
  , the_geom POLYGON NOT NULL
);

SELECT
    RecoverGeometryColumn('base_polygons', 'the_geom', 27700, 'POLYGON', 2)
  , CreateSpatialIndex('base_polygons', 'the_geom');
```

At first I was building up my options using CTE's:

```sql
WITH new_geom AS (
    SELECT * FROM base_polygons WHERE pid = 3
), anchor_geom AS (
    SELECT ST_Union(b.the_geom) AS the_geom
    FROM base_polygons AS b
        CROSS JOIN new_geom AS n
    WHERE b.pid != n.pid AND
        PtDistWithin(b.the_geom, n.the_geom, 1)
), snap_geom AS (
    SELECT
        ST_MakeValid(ST_Snap(n.the_geom, a.the_geom, 0.2))
    FROM new_geom AS n
         CROSS JOIN anchor_geom AS a
)

UPDATE base_polygons
SET the_geom = (SELECT * FROM snap_geom)
WHERE pid = 3;
```

Though as it later turns out, the queries are easier to read in the form of a trigger, because the new geometry's not actually part of the table yet. For general purposes, snapping under a metre seems like a good idea for polygons on the scale of buildings.

## Moving to Triggers

Having got a setup that I was relatively happy with, I migrated things into a view and a trigger. I used a view so that I had more of a framework to build a properly normalised structure in.

```sql
CREATE VIEW edit_polygons AS SELECT
    pid
  , the_geom
FROM base_polygons;

INSERT INTO views_geometry_columns
    (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only)
VALUES
    ('edit_polygons', 'the_geom', 'pid', 'base_polygons', 'the_geom', 0);
```

Then building the trigger on top of that. As the integer primary key I added for QGIS' benefit is purely synthetic, so I'm just letting SQLite handle it's own key. Adding a layer of ````COALESCE```` means that gives a little reliability if the geometry modifications fail.

```sql
CREATE TRIGGER IF NOT EXISTS polygon_insert
INSTEAD OF INSERT ON edit_polygons
FOR EACH ROW
BEGIN

    INSERT INTO base_polygons
        (category, the_geom)
    VALUES
        (NEW.category
       , ST_Multi(
            ST_ForceLHR(
                ST_MakeValid(
                    SanitizeGeometry(
                        COALESCE(
                            ST_Difference(
                                ST_Snap(NEW.the_geom,
                                        (SELECT ST_Union(the_geom)
                                         FROM base_polygons
                                         WHERE PtDistWithin(NEW.the_geom,
                                                            the_geom,
                                                            1
                                                            )
                                         ),
                                         0.2
                                ),
                                (SELECT ST_Union(the_geom)
                                              FROM base_polygons
                                              WHERE PtDistWithin(NEW.the_geom,
                                                                 the_geom,
                                                                 1
                                                                 )
                                              )
                                ),
                            NEW.the_geom
                            )
                        )
                    )
                )
            )
         );

END;
```

This ended up being an unwieldy pile of functions because of all the things I'm trying to do at once. I'm considering pushing out a lot of this into a few temporary tables to give a clearer syntax, though that might add quite a bit of overhead. Some savings might come from only having the ````ST_Union```` subquery once. This is going to need a little bit of testing - but if I can avoid the pyramid of function, then maintaining and tuning this will be a *lot* easier. If needed later I can just crunch down the end product into a single statement.

More importantly - this actually does most of what I'm after, dealing with most small digitisation problems.

## Using a Temporary Table

To store the geometries in a temporary table, I need to make one. I'm going to store both the anchor and new geometries in the same table.

```sql
CREATE TABLE temp_geom (
    label TEXT PRIMARY KEY
  , the_geom GEOMETRY
);
```

Then at the top of the insert / update triggers, I'm adding the following:

```sql
/*Store the geometries in a temp table.*/
DELETE FROM temp_geom;
INSERT INTO temp_geom (label, the_geom) VALUES ('new', NEW.the_geom);
INSERT INTO temp_geom
    (label, the_geom)
SELECT
    'anchor'
  , ST_Union(the_geom)
FROM base_polygons
WHERE PtDistWithin(NEW.the_geom,
                   the_geom,
                   1
                   );

/*Fix up the geometries.*/
UPDATE temp_geom
SET the_geom = ST_ForceLHR(ST_MakeValid(SanitizeGeometry(the_geom)));

UPDATE temp_geom
SET the_geom = ST_Snap(the_geom,
                       (SELECT the_geom FROM temp_geom WHERE label = 'anchor');
                       )
WHERE label = 'new';

UPDATE temp_geom
SET the_geom = ST_Difference(the_geom,
                             (SELECT the_geom FROM temp_geom WHERE label = 'anchor');
                             )
WHERE label = 'new';

UPDATE temp_geom
SET the_geom = ST_ForceLHR(ST_MakeValid(SanitizeGeometry(the_geom)))
WHERE label = 'new';
```

This has the double advantage of being easier to read while also letting me apply the cleanup stack of functions to both the anchor geometry and the new one. I'm clearing out the ````temp_geom```` table at the *start* of the trigger rather than at the end so that if there is an error, it won't break the *next* polygon as well. I'm also cleaning up the polygon after snapping it etc.

After a bit of experimentation, there's a bit of an issue with polygons included inside another one. If they're not passed in the 'correct' order, the inclusions will just get ignored / create overlaps.
