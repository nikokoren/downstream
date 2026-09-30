"""Remote source locations (verified 2026-09-28, see PROJECT.md; re-check before relying on them)."""

# HydroATLAS v1.0 on figshare (CC BY 4.0, D5). GDAL reads single zip members via HTTP range requests.
RIVERATLAS_ZIP = "https://ndownloader.figshare.com/files/20087486"  # RiverATLAS_Data_v10_shp.zip
BASINATLAS_ZIP = "https://ndownloader.figshare.com/files/20087237"  # BasinATLAS_Data_v10_shp.zip
RIVERATLAS_EU = f"/vsizip/{{/vsicurl/{RIVERATLAS_ZIP}}}/RiverATLAS_v10_shp/RiverATLAS_v10_eu.shp"
BASINATLAS_L12 = (
    f"/vsizip/{{/vsicurl/{BASINATLAS_ZIP}}}/BasinATLAS_v10_shp/BasinATLAS_v10_lev12.shp"
)

REACH_COLUMNS = [
    "HYRIV_ID",
    "NEXT_DOWN",
    "MAIN_RIV",
    "LENGTH_KM",
    "DIST_DN_KM",
    "ENDORHEIC",
    "ORD_CLAS",
    "ORD_STRA",
    "HYBAS_L12",
    "UPLAND_SKM",  # upstream area: tells a real confluence from a delta arm (D12)
    "dis_m3_pyr",  # mean annual flow (m3/s): speed estimate for the travel time (D3, R10)
]
BASIN_COLUMNS = ["HYBAS_ID", "NEXT_DOWN", "ENDO", "COAST"]

# Natural Earth via the NACIS CDN (naturalearthdata.com download links returned HTTP 500 on 2026-09-28).
NE_BASE = "https://naciscdn.org/naturalearth/10m"
NE_LAYERS = {
    "rivers": f"{NE_BASE}/physical/ne_10m_rivers_lake_centerlines.zip",
    "rivers_europe": f"{NE_BASE}/physical/ne_10m_rivers_europe.zip",
    "lakes": f"{NE_BASE}/physical/ne_10m_lakes.zip",
    "lakes_europe": f"{NE_BASE}/physical/ne_10m_lakes_europe.zip",
    "marine": f"{NE_BASE}/physical/ne_10m_geography_marine_polys.zip",
    "ocean": f"{NE_BASE}/physical/ne_10m_ocean.zip",
    "admin0": f"{NE_BASE}/cultural/ne_10m_admin_0_countries.zip",
}

# GeoNames (CC BY 4.0, D9).
GEONAMES_DUMP = "https://download.geonames.org/export/dump"

# HydroLAKES v1.0 lake pour points (Messager et al. 2016), CC BY 4.0, direct download, no
# registration (checked 2026-09-30, docs/sources/HYDROLAKES_2026-09-30.md). Used for the time a
# raindrop spends in lakes on its way (`Res_time`, days; D3).
HYDROLAKES_POINTS = "https://data.hydrosheds.org/file/hydrolakes/HydroLAKES_points_v10_shp.zip"
LAKE_COLUMNS = ["Hylak_id", "Lake_name", "Lake_type", "Res_time", "Vol_total", "Dis_avg"]
