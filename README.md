# Downstream

A TRMNL recipe that shows where a raindrop falling at your location ends up: the chain of streams and rivers it follows, how far it travels, and the sea or lake where it ends.

**Status:** in setup, not yet usable. See `PROJECT.md`.

## Data and attribution

### HydroATLAS (river network and sub-basins)

River reaches and sub-basins come from RiverATLAS and BasinATLAS, part of HydroATLAS v1.0 by Linke, Lehner et al., licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Source: https://www.hydrosheds.org/hydroatlas. **Changes:** Downstream keeps only the routing columns, simplifies the geometry and splits it into tiles.

- Linke, S., Lehner, B., Ouellet Dallaire, C., Ariwi, J., Grill, G., Anand, M., Beames, P., Burchard-Levine, V., Maxwell, S., Moidu, H., Tan, F., Thieme, M. (2019). Global hydro-environmental sub-basin and river reach characteristics at high spatial resolution. Scientific Data 6: 283. https://doi.org/10.1038/s41597-019-0300-6
- Underlying river network (HydroRIVERS, in the format provided by RiverATLAS v1.0): Lehner, B., Grill G. (2013). Global river hydrography and network routing: baseline data and new approaches to study the world's large river systems. Hydrological Processes, 27(15): 2171–2186. https://doi.org/10.1002/hyp.9740

### Natural Earth (river, lake and sea names)

Made with Natural Earth. Free vector and raster map data @ naturalearthdata.com (public domain), including the Europe river supplement.

### GeoNames (towns)

Town names and positions from [GeoNames](https://www.geonames.org/), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). **Changes:** Downstream uses a selection of towns and their English and German names.

### Basemap

© OpenStreetMap contributors.

## Limits

Engineered drainage (dams, canals, city sewers) is not modeled.
