# EU Referendum Mapping
@author = Joe McGrath
@date_created = 2018-05-13
@description = Basic exploratory mapping of the results of the EU referendum.
@keyword = EU
@keyword = European Union
@keyword = Referendum
@keyword = Mapping
@keyword = Election
@keyword = SpatiaLite
@keyword = QGIS
@map = j-a004-01
@map = j-a004-02
@map = j-a004-03
@finished = True

It's been a while since the UK had it's referendum on membership and I've been sitting on the data that came out of it for a while now. I *did* do some maps at the time, I wasn't too happy with them. This is just a quick write up of me going back over the mapping the results.

## Data Used

The data I'm using is:

* Vote counts from the UK Electoral Commission.
* Region boundaries from the Ordinance Survey BoundaryLine set.

For the sake of simplicity I've not added Northern Ireland or Gibraltar to the map yet.

## Vote Percentage Lead

The most obvious map to make of the election results is the percentage by which each region voted for remain / leave.

### Collating the Data

To combine the table of vote results with their spatial extetents, I'm using SpatiaLite. This lets me use spatial SQL and store the data in a standalone file without much setup. After importing the data via the SpatiaLite GUI, I merged the data into a view:

```sql
CREATE INDEX os_dist_borough_unitary_region_join_idx ON os_dist_borough_unitary_region(code);
CREATE INDEX eu_ref_result_join_idx ON eu_ref_result(area_code);

CREATE VIEW eu_ref_poly AS SELECT
    r.PK_UID AS pid
  , r.NAME AS region_name
  , r.CODE AS region_code
  , r.HECTARES AS area_ha
  , d.Electorate AS electorate
  , d.ExpectedBallots AS expected_ballots
  , d.VerifiedBallotPapers AS verified_ballots
  , d.Pct_Turnout AS pct_turnout
  , d.Votes_Cast AS votes_cast
  , d.Valid_Votes AS valid_votes
  , d.Rejected_Ballots AS rejected_ballots
  , d.Remain AS vote_remain
  , d.Leave AS vote_leave
  , d.Remain - d.Leave AS vote_ballance
  , CAST((d.Remain - d.Leave) AS REAL) / d.Valid_Votes * 100 AS pct_vote_ballance
  , r.the_geom AS the_geom
FROM
    os_dist_borough_unitary_region AS r
    INNER JOIN eu_ref_result AS d
        ON r.code = d.area_code;

INSERT INTO views_geometry_columns
    (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only)
VALUES
    ('eu_ref_poly', 'the_geom', 'pid', 'os_dist_borough_unitary_region', 'the_geom', 1);
```

To cleanly visualise this, I merged the votes columns into a percentage of the votes - with positive being more net votes to remain (using ```CAST``` to prevent the result coming out as an integer). And then loaded this into QGIS. When producing the maps I labelled them as 'Leave' and 'Remain' rather than positive or negative values.

----

After reviewing the data it seems that everything from the CSV came in as text. To fix this, I'm re-creating the view and casting to appropriate data types:

```sql
BEGIN;

DROP VIEW eu_ref_poly;

CREATE VIEW eu_ref_poly AS SELECT
    r.PK_UID AS pid
  , r.NAME AS region_name
  , r.CODE AS region_code
  , r.HECTARES AS area_ha
  , CAST(d.Electorate AS INTEGER) AS electorate
  , CAST(d.ExpectedBallots AS INTEGER) AS expected_ballots
  , CAST(d.VerifiedBallotPapers AS INTEGER) AS verified_ballots
  , CAST(d.Pct_Turnout AS REAL) AS pct_turnout
  , CAST(d.Votes_Cast AS INTEGER) AS votes_cast
  , CAST(d.Valid_Votes AS INTEGER) AS valid_votes
  , CAST(d.Rejected_Ballots AS INTEGER) AS rejected_ballots
  , CAST(d.Remain AS INTEGER) AS vote_remain
  , CAST(d.Leave AS INTEGER) AS vote_leave
  , CAST(d.Remain - d.Leave AS INTEGER) AS vote_ballance
  , CAST((d.Remain - d.Leave) AS REAL) / d.Valid_Votes * 100 AS pct_vote_ballance
  , r.the_geom AS the_geom
FROM
    os_dist_borough_unitary_region AS r
    INNER JOIN eu_ref_result AS d
        ON r.code = d.area_code;

COMMIT;
```

While SQLite's fairly flexible on data types, QGIS is less so - making having the correct data types more important.

### Making the Map

I did a thematic map with the percentage lead in the polls. Picking colours wasn't too difficult - the main Remain campaign had a red-white-blue theme, focussing on blue and the main Leave campaign had red-white focussing on red. I ended up sampling the ends of the colour ramp directly from posters for the different campaigns and adding in a light grey at the middle.

The fairly obvious choice was to have 0 be the central point of the histogram bins. Each side of that I chose three bins for each group and a central '± 1%' group for no clear leaning. Despite the fact the two groups didn't have the same distribution of values, I used the same set of bins as it would otherwise be practically impossible to compare the two. The bins I ended up choosing are included below:

<img src="img/uk-ref-vote_lead_hist.jpg" alt="The histogram bins for vote lead.">

I feel these give a decent ballance between the two. To plot these on a map I split off the Scottish Northern Isles into their own inset map to get a better scale. As the plain polygons on a white background felt a little flat I added an outer glow in black - this does give some weird results for smaller islands but overall pulls a lot more focus to the map.

This worked pretty well, after a few tests I came out with this map:

<img src="/map/j-a004-01.jpg" alt="Map of the lead for Leave & Remain in each region.">

The result of which looks reassuringly similar to every other map of the results I've seen.

## Adding Graphs

An idea I've been playing around with for a while is to use the ```MAKEPOINT``` function in the database to produce a graph directly in QGIS. I'm not sure how well this will turn out - but there's one way to be sure and this is a good a place as any.

### Formatting the Points

The SQL is pretty simple, I'm also keeping a few extra columns for reference. The only part that needs some explaination is the creation of a dummy table. I've done this so I can register the new view as a geometry table for QGIS to see (otherwise it's just a view that happens to have some geometry in it).

```sql
BEGIN;

CREATE TABLE dummy_geom (
    pid INTEGER PRIMARY KEY
  , point_geom POINT
);

SELECT
    RecoverGeometryColumn('dummy_geom', 'point_geom', 27700, 'POINT', 'XY');

UPDATE geometry_columns_auth
SET hidden = 1
WHERE f_table_name = 'dummy_geom';

CREATE VIEW eu_ref_turnout_graph AS SELECT
    pid
  , region_code
  , region_name
  , electorate
  , pct_turnout
  , pct_vote_ballance
  , MAKEPOINT(pct_vote_ballance, pct_turnout, 27700) AS the_geom
FROM eu_ref_poly;

INSERT INTO views_geometry_columns
    (view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only)
VALUES
    ('eu_ref_turnout_graph', 'the_geom', 'pid', 'dummy_geom', 'point_geom', 1);

COMMIT;
```

All the points seem to have made it into QGIS without any trouble (so long as it's loaded as a SpatiaLite layer rather than a generic vector data source).

### Styling the Graphs

The full rendering options in QGIS are quite nice to have access to, but are clearly not designed to be used for creating graphs (e.g. the axes are identically scaled). Luckily by shrinking the main map a little, the wide graph fitted in quite well. I coloured the points the same as the polygons in the map (one of the advantages of hacking the graph into QGIS).

One other useful feature was to define the size of the points in 'metres at scale' - so that the size of the points didn't change with the size of the output. The output turned out pretty nice - but I would probably jsut take the time to use a tool designed for the job in the future.

<img src="/map/j-a004-02.jpg" alt="Referendum lead map with turnout percentage graph.">

The results of percentage turnout of electorate against vote ballance is quite interesting. The overall pattern seems to be that districts that voted to leave generally had a higher proportion of the electorate turn out.

## A Different Angle

An aspect I'd like to explore is if there's any inherant bias in assessing percentage rather than actual vote counts. Just looking at the percentages makes it look like much more of a landslide than the actual 52% / 48% split. I don't know the criteria for defining the district borough unitary regions is - but I wouldn't be surprised if there was a trend for more densely populated urban regions to have higher total populations than rural ones.

To check this, I've plotted out the histogram of total votes:

<img src="img/uk-ref-vote_count_hist.jpg" alt="The histogram bins for net total votes.">

It does seem that despite the fairly even bins for percentage votes, there are regions with much higher total vote counts for remain. I'll explore the result of plotting vote count rather than percentages. As plotting absolute counts on a choropleth with different-sized regions is bad practise I'm going with votes per unit area (in this case hectares). I suspect this pushes the bias in the other direction. The histogram of votes per area does seem to be significantly less ballanced:

<img src="img/uk-ref-vote_density_hist.jpg" alt="The histogram bins for votes per hectare.">

Coming up with a scale that works for both is a little fiddly. The bins I settled on had their finer scale based on the leave votes and their upper end based on the remain votes.

<img src="/map/j-a004-03.jpg" alt="Map of net votes for remain and leave per hectare.">

This shows a bit of a different pattern to the percentage of voters - visually compensating better for large, less-densely populated regions. There's a natural bias in this to show cities due to their higher raw population.

## Next Steps

The next obvious step would be to bring in other variables - probably from ONS census data. I've heard people making a lot of the demographics of the different groups - so it'd be interesting to get my own eyes on those numbers. There's also a bit more room to explore with graphs in QGIS - like sizing the points on the graph based on their total electorate.
