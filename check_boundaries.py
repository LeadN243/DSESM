import geopandas as gpd
from pathlib import Path

DATA_PROCESSED = Path.cwd() / "data" / "processed"
DATA_RAW = Path.cwd() / "data" / "raw"

# Check the shapefile
print("Checking Portugal shapefile:")
shape_shp = DATA_PROCESSED / "regions" / "portugal_boundaries.shp"
shape = gpd.read_file(shape_shp)
print(f"Bounds: {shape.total_bounds}")
print(f"Number of regions: {len(shape)}")
print(f"Columns: {shape.columns.tolist()}")
print(f"\nFirst few rows:")
print(shape[['NAME_1', 'geometry']].head())

# Check GADM
print("\n\nChecking GADM file:")
gadm = gpd.read_file(DATA_RAW / "gadm" / "gadm_410-levels-ADM_1-PRT.gpkg")
print(f"Bounds: {gadm.total_bounds}")
print(f"Columns: {gadm.columns.tolist()}")
print(f"Number of features: {len(gadm)}")
print(f"\nFirst few rows:")
if 'NAME_1' in gadm.columns:
    print(gadm[['NAME_1', 'geometry']].head())
else:
    print(gadm.head())
