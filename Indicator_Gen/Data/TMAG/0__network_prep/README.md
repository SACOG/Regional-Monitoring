# Extracting OSM data and making an LTS line file that can be used in Conveyal

## Context
1. Extract OSM lines using process below
2. Conflate bikeway infrastructure data from a SACOG file onto the OSM lines, but with SACOG bikeway line extents
3. Resulting file has OSM segments clipped to SACOG bikeway extents, with LTS tags too

## Where to get extracts
[Protomaps](https://app.protomaps.com/downloads/osm) is a good starting point.

## Extract only stuff needed for a Conveyal Bundle using osmosis
See [Conveyal documentation](https://docs.conveyal.com/prepare-inputs)

## Extract only roads needed for bikeway LTS computation
**More to come on bikeway LTS computation**
`osmosis --read-pbf sacog20230222.osm.pbf ^`
`--tf accept-ways highway=living_street,primary,primary_link,residential,road,secondary,secondary_link,tertiary,tertiary_link,trunk,cycleway,path,unclassified ^`
`--tf accept-relations type=restriction ^`
`--used-node ^`
`--write-pbf sacog_roads_trimmed_wsvcrds.osm.pbf`

## Convert to format usable by geopandas using ogr2ogr
Check out GDAL ogr2ogr documentation for more details.

Example command takes OSM PBF file and converts its line elements into a polyline spatial file (SHP, GeoJSON, GPKG, etc.)
`ogr2ogr <destination_spatial_file> <source .osm.pbf> lines`
