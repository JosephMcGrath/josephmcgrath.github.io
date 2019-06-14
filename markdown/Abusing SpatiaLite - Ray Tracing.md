# Abusing SpatiaLite - Ray Tracing

@author = Joe McGrath
@date_created = 2019-06-14
@description = implementing a basic ray tracing algorithm in SpatiaLite.
@keyword = SpatiaLite
@keyword = QGIS
@keyword = Line of sight
@keyword = Visibility
@keyword = Ray tracing
@finished = False

As a matter of curiosity I wanted to see if I could implement a simple ray-tracing algorithm in GIS. It's not something that I can see much practical application, just a bit of fun (though could be interesting for mapping visibility using a layer of buildings / fences).

There's enough functionality in SpatiaLite to do this fairly simply - but it's a bit awkward working with multi-part geometries. As normal this would be easier in PostGIS but I like the portability of SpatiaLite.

First things first we're going to need a table of angles:

```sql
CREATE TABLE angles (r REAL PRIMARY KEY);

WITH RECURSIVE angle_temp (d) AS (
    VALUES (0)
    UNION ALL
    SELECT d + (360 / 256)
    FROM angle_temp
    WHERE d < 360
)

INSERT OR IGNORE INTO angles (r)
SELECT Radians(d) FROM angle_temp
ORDER BY d;
```

This creates a list of angles (in radians) that I can use to generate "rays" at uniform angles.

For the sake of this proof of concept I'm using three layers. The first is "base points" that have a line of sight (with the sight column representing how far the point can "see"):

```sql
CREATE TABLE base_point (
    fid INTEGER PRIMARY KEY
  , sight REAL DEFAULT 1
  , the_geom POINT
);

SELECT RecoverGeometryColumn('base_point' , 'the_geom' , 27700 , 'POINT');
```

A set of "walls" that block lines of sight:

```sql
CREATE TABLE wall (
    fid INTEGER PRIMARY KEY
  , the_geom LINESTRING
);

SELECT RecoverGeometryColumn('wall' , 'the_geom' , 27700 , 'LINESTRING');
```

And then a table to hold the final lines of sight. In theory this could all be done with live views but a straight table updated with triggers is a little more reliable for testing:

```sql
CREATE TABLE los (
    fid INTEGER PRIMARY KEY
  , the_geom POLYGON
);

SELECT RecoverGeometryColumn('los' , 'the_geom' , 27700 , 'POLYGON');
```

Now to go through the ray-tracing algorithm. First generate a set of rays. This is complicated by the ```ST_Project``` function being a little bit weird. It always expects lon/lat coordinates so you have to pass through WGS84 on the way through. It'd be possible to do the same with ```ST_Translate``` and a little trigonometry too.

```sql
CREATE VIEW base_ray AS SELECT
    fid
  , r AS angle
  , MakeLine(the_geom,
             ST_Transform(ST_Project(ST_Transform(the_geom, 4326), sight, r), ST_SRID(the_geom))
             ) AS the_geom
FROM base_point CROSS JOIN angles ORDER BY r;
```

Then split them by the wall geometries. This step requires a two-part solution as otherwise a "split ray" is generated for each geometry the ray passes through. There's also a bit of an assumption that ```ST_Split``` returns geometry parts in the same order as the original.

```sql
CREATE VIEW split_ray AS SELECT
    r.fid
  , r.angle
  , Coalesce(ST_GeometryN(ST_Split(r.the_geom, w.the_geom), 1),
             r.the_geom
             ) AS the_geom
FROM base_ray AS r
    LEFT OUTER JOIN wall AS w
        ON ST_Intersects(r.the_geom, w.the_geom);

CREATE VIEW shortest_split_ray AS SELECT fid, angle, the_geom
FROM split_ray
GROUP BY fid, angle
HAVING ST_LENGTH(the_geom)  = MIN(ST_LENGTH(the_geom));
```

Next the far ends of each of these rays can be joined to create a single line, which can then be closed to make a closed ring:

```sql
CREATE VIEW unclosed_ring AS SELECT fid, MakeLine(ST_PointN(the_geom, -1)) AS the_geom
FROM shortest_split_ray
GROUP BY fid
ORDER BY angle;

CREATE VIEW view_ring AS SELECT fid, AddPoint(the_geom, ST_StartPoint(the_geom)) AS the_geom
FROM unclosed_ring;
```

Finally I define a set of triggers to update the line of sight geometry whenever the base point is updated:

```sql
CREATE TRIGGER los_calc_insert AFTER INSERT ON base_point
BEGIN
    INSERT INTO los (fid, the_geom)
    SELECT fid, MakePolygon(the_geom) FROM view_ring
    WHERE fid = NEW.fid;
END;

CREATE TRIGGER los_calc_update AFTER UPDATE ON base_point
BEGIN

    DELETE FROM los WHERE fid = OLD.fid;

    INSERT INTO los (fid, the_geom)
    SELECT fid, MakePolygon(the_geom) FROM view_ring
    WHERE fid = NEW.fid;
END;

CREATE TRIGGER los_calc_delete AFTER DELETE ON base_point
BEGIN

    DELETE FROM los WHERE fid = OLD.fid;

END;
```

Last thing of all is to fire up QGIS and play about with the layers I've made. As an experiment I'm trying out Ordinance Survey [Openmap Local](https://www.ordnancesurvey.co.uk/business-and-government/products/os-open-map-local.html):

```sql
INSERT INTO wall (the_geom)
SELECT ST_ExteriorRing(the_geom) FROM sk_building;

SELECT CreateSpatialIndex('wall', 'the_geom');

INSERT INTO base_point (sight, the_geom)
VALUES (100, MakePoint(459400,379000, 27700));

DELETE FROM wall
WHERE NOT ST_Intersects(the_geom, (SELECT ST_Buffer(the_geom, 10000) FROM base_point));
```

The result does take quite a while to process (there's a whole bunch of optimisations that could be made if it was important, but it's not relevant at this stage).
