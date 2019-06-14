# Visualising GPS Logs
@author = Joe McGrath
@date_created = 2018-09-15
@description = Generating simple overviews with GPS data.
@keyword = GPS
@keyword = QGIS
@keyword = PostGIS
@keyword = Visualisation
@map = j-a002-01
@finished = True

![An overview of several years of GPS logs.](/map/j-a002-01.jpg)

## Introduction

I've been collecting GPS data using my phone for about a year and a half now (partially out of curiosity and partially so I could have a data-set of my own to play around with). Currently my processing is pretty simple and just pointed at creating a few pretty [firefly-style maps](https://adventuresinmapping.com/2016/10/17/firefly-cartography). I've had to sit on this project for a little while because the most interesting outputs all plainly identify my house or a friend's house, but having moved house recently has freed that up significantly.

## Collecting Data

My point-collection setup went through a few iterations before I settled on a final version. The first (stupid) method was manually putting down points in QField on my phone (which I was experimenting with at the time). I stopped doing this pretty quickly as it was dull, didn't collect much in the way of metadata and was pretty unsafe (I almost walked into a few roads while looking at my phone).

The next (and current) solution is to use a purpose-built app to record the data directly into a csv without manual interference. [The app](https://play.google.com/store/apps/details?id=com.mendhak.gpslogger&hl=en_GB) also records other data at the same time (most notably accuracy) that I wouldn't otherwise be able to get at. The only real downside is a hit to my battery of about 10%.

I've opted for a somewhat over-the-top approach to recording points, with the app recording one every 2 seconds while I'm moving. Over the past year and a bit this has generated quite a large number of points - which has made visualisation pretty interesting at the other end.

## Storing the Data

I opted to do most of my processing in-database as the project was likely to be fairly data-intensive and access to indexes etc while running seemed like a good idea due to the relatively large quantity of data I'm generating.

At first, I stored the data in a simple SpatiaLite database that also joined consecutive points into lines if they passed an accuracy / timing threshold, but that quickly got clogged up with the volume of data I was trying to throw around through it on a regular basis. I switched to PostGIS, with an R script on the front end to throw the csvs in automatically using ogr2ogr. Once the data was in the database, trigger functions handled the rest.

It taken a little while to tune the triggers so that they run in a reasonable time. I tried not to assume that the data was coming in the exact right order of files / rows, so I couldn't just look at the previous point to see if a line needed to be created so I had to pull out all of the point within a particular duration - a functional index turned out to be a good method here. For example:

```sql
CREATE INDEX gps_point_time_plus_20_idx
    ON gps_data.gps_point USING btree
    (("time" + '00:00:20'::interval))
    TABLESPACE pg_default;
```

This resulted in a pipeline where I could just offload csv files into a folder whenever it was convenient, run the R script and have all my data run through my processing automatically.

## Visualising the Output

Visualisation of this data has been quite a fun challenge, as it's got harder as time went on. When I only had a few points and lines I could have bold arrows on the lines and other decoration on my geometries. As the points built up things started to get more and more cluttered. A few of the problems I've noticed are:

* Even recording a point every few seconds doesn't produce points at a high enough density to form an obvious route (especially when I started playing around with transparency).
    * This is helped by joining consecutive points into lines as a background layer. The lines didn't need that high a contrast to help reduce ambiguity.
    * The inverse is true too - in areas where I regularly walk the density of points is so high that it's impossible to make out anything clearly.
* The phone GPS I'm using isn't hyper-accurate and just giving all points the same visual weight created some weird paths.
    * My solution here was to get QGIS to give each point a transparency and size based on its accuracy level (so lower accuracy points were larger pale circles). Because both the accuracy measurement and coordinate system I'm using are in metres I could get QGIS to give the points a size equal to their accuracy envelope.
* For overlaying multiple points with transparency I played around with blend-modes in QGIS, eventually going for addition-style blending on a black background.
    * An [Ordinance Survey blog post](https://www.ordnancesurvey.co.uk/blog/2017/02/carto-tips-using-blend-modes-opacity-levels/) covers these better than I can.

So my end result was to have faint lines in the background, overlaid by variable-transparency points. I feel like there's a bit more work to do here, but this is a decent enough point to park things.

Below I've got a quick example of the difference that even very faint lines make:

![An example of an area made clearer by the addition of lines.](/img/gps-traces-with-lines.jpg)

This does end up making the output look quite a bit more busy, particularly in areas I've been through multiple times (as it adds up to a lighter background). Personally I prefer having the lines in for less-travelled areas.

## More Detail on the Database

As I've already mentioned, I'd put together a small SpatiaLite database to store my first results - but as the data set passed several months SQLite started to act as a bottleneck on a few operations (or at least my understanding of how indexes in SQLite work). I ended up switching to PostGIS, which also seems to have improved performance (with the full code being [here](https://github.com/JosephMcGrath/Misc-scripts/tree/master/PostGreSQL/Schema_GPS_Data)).

The problem in question was joining up consecutive points with linestrings. In SpatiaLite I'd kind-of hacked things around by assuming the previous point entered into the database was the one to compare against. While that's not a *bad* assumption, it means data has to be fed into the database in a very particular way. Instead I applied the following criteria:

* When a new GPS point is entered into the database, generate a line between it and most recent the point meeting the following criteria:
    * The point is at most 20 seconds before the current point.
    * The accuracy measurement of both points is less than 25 metres.

The tricky part for my novice understanding of PostgreSQL was returning 'points within 20 seconds' from a variable point in time while keeping things quick. Eventually I came up with this index which does the job (but is limited to 20 second intervals):

```sql
CREATE INDEX gps_point_time_plus_20_idx
    ON gps_data.gps_point USING btree
    (("time" + '00:00:20'::interval))
    TABLESPACE pg_default;
```

Which defines a [functional index](https://www.postgresql.org/docs/9.1/static/indexes-expressional.html) on the result of adding 20 seconds to the point's timestamp. So far this has been scalling reasonably well as a long-term solution one and a half million points in.
