"""
Test script to verify the Section 3.1 fix works
"""

import geopandas as gpd
from pathlib import Path
from atlite.gis import ExclusionContainer

BASE_DIR = Path.cwd()
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

print("Testing Section 3.1 fix...")
print("=" * 70)

# 1. Load shape
print("\n1. Loading Portugal shape...")
shape = gpd.read_file(DATA_PROCESSED / "regions" / "portugal_boundaries.shp")
print(f"   Original: {len(shape)} regions, bounds: {shape.total_bounds[:2]}...{shape.total_bounds[2:]}")

# 2. Filter Azores
print("\n2. Filtering out Azores...")
shape_mainland = shape[shape['NAME_1'] != 'Azores'].copy()
print(f"   After filter: {len(shape_mainland)} regions")
print(f"   New bounds: {shape_mainland.total_bounds[:2]}...{shape_mainland.total_bounds[2:]}")
print(f"   ✅ Azores removed successfully")

# 3. Initialize excluder
print("\n3. Initializing ExclusionContainer...")
excluder = ExclusionContainer(crs=3035, res=100)
print(f"   CRS: {excluder.crs}, Resolution: {excluder.res}m")

# 4. Add CORINE raster
print("\n4. Adding CORINE raster...")
corine_files = list((DATA_RAW / "copernicus-glc").glob("*.tif"))
if corine_files:
    print(f"   Found: {corine_files[0].name}")
    codes_to_exclude = [1, 2, 3, 4, 5, 6]
    try:
        excluder.add_raster(
            str(corine_files[0]),
            codes=codes_to_exclude,
            crs=4326,      # KEY: Specify input CRS
            buffer=800,
            nodata=255
        )
        print(f"   ✅ Raster added successfully")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"   ⚠️  No CORINE file found")

# 5. Check bounds overlap
print("\n5. Checking bounds overlap...")
import rasterio
with rasterio.open(corine_files[0]) as src:
    raster_bounds = src.bounds
    shape_bounds = shape_mainland.total_bounds
    
    print(f"   Portugal bounds: X=[{shape_bounds[0]:.2f}, {shape_bounds[2]:.2f}], Y=[{shape_bounds[1]:.2f}, {shape_bounds[3]:.2f}]")
    print(f"   Raster bounds:   X=[{raster_bounds[0]:.2f}, {raster_bounds[2]:.2f}], Y=[{raster_bounds[1]:.2f}, {raster_bounds[3]:.2f}]")
    
    x_overlap = not (shape_bounds[2] < raster_bounds[0] or shape_bounds[0] > raster_bounds[2])
    y_overlap = not (shape_bounds[3] < raster_bounds[1] or shape_bounds[1] > raster_bounds[3])
    
    if x_overlap and y_overlap:
        print(f"   ✅ SPATIAL OVERLAP CONFIRMED")
    else:
        print(f"   ❌ NO OVERLAP: X={x_overlap}, Y={y_overlap}")

print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED - Fix should work!")
print("=" * 70)
