#!/usr/bin/env python3
"""
Diagnostic script to check data compatibility for Section 3.1 eligibility analysis
"""

import geopandas as gpd
import rasterio
import xarray as xr
from pathlib import Path

BASE_DIR = Path.cwd()
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

print("\n" + "=" * 80)
print("DIAGNOSTIC: Data Compatibility Check for Section 3.1")
print("=" * 80)

# ============================================================================
# 1. PORTUGAL BOUNDARY
# ============================================================================
print("\n1️⃣ PORTUGAL BOUNDARY:")
portugal_shp = DATA_PROCESSED / "regions" / "portugal_boundaries.shp"

if portugal_shp.exists():
    shape = gpd.read_file(portugal_shp)
    print(f"   File: {portugal_shp.name}")
    print(f"   CRS: {shape.crs}")
    print(f"   Bounds (minx, miny, maxx, maxy): {shape.total_bounds}")
else:
    print(f"   ❌ Shapefile not found, trying GADM...")
    gadm_file = DATA_RAW / "gadm" / "gadm_410-levels-ADM_1-PRT.gpkg"
    if gadm_file.exists():
        shape = gpd.read_file(gadm_file)
        print(f"   File: {gadm_file.name}")
        print(f"   CRS: {shape.crs}")
        print(f"   Bounds (minx, miny, maxx, maxy): {shape.total_bounds}")
    else:
        print(f"   ❌ GADM not found either")
        exit(1)

# ============================================================================
# 2. CORINE LAND COVER RASTER
# ============================================================================
print("\n2️⃣ CORINE LAND COVER RASTER:")
corine_path = DATA_RAW / "copernicus-glc"
corine_files = list(corine_path.glob("*.tif"))

if corine_files:
    corine_file = corine_files[0]
    print(f"   File: {corine_file.name}")
    print(f"   Size: {corine_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        with rasterio.open(corine_file) as src:
            print(f"   CRS: {src.crs}")
            print(f"   Bounds (minx, miny, maxx, maxy): {src.bounds}")
            print(f"   Resolution: {src.res}")
            print(f"   Shape (rows, cols): {src.shape}")
            print(f"   Data type: {src.dtypes[0]}")
            print(f"   nodata value: {src.nodata}")
            
            # Check overlap
            print(f"\n   Checking spatial overlap:")
            print(f"   ├─ Portugal bounds: X=[{shape.total_bounds[0]:.2f}, {shape.total_bounds[2]:.2f}], Y=[{shape.total_bounds[1]:.2f}, {shape.total_bounds[3]:.2f}]")
            print(f"   └─ Raster bounds:   X=[{src.bounds[0]:.2f}, {src.bounds[2]:.2f}], Y=[{src.bounds[1]:.2f}, {src.bounds[3]:.2f}]")
            
            # Check if bounds overlap
            x_overlap = not (shape.total_bounds[2] < src.bounds[0] or shape.total_bounds[0] > src.bounds[2])
            y_overlap = not (shape.total_bounds[3] < src.bounds[1] or shape.total_bounds[1] > src.bounds[3])
            
            if x_overlap and y_overlap:
                print(f"   ✅ SPATIAL OVERLAP CONFIRMED")
            else:
                print(f"   ❌ NO SPATIAL OVERLAP")
                print(f"      X overlap: {x_overlap}, Y overlap: {y_overlap}")
    except Exception as e:
        print(f"   ❌ Error reading raster: {e}")
else:
    print(f"   ❌ No CORINE files found in {corine_path}")
    print(f"   Available files in copernicus-glc:")
    for f in corine_path.glob("*"):
        print(f"      - {f.name}")

# ============================================================================
# 3. WDPA PROTECTED AREAS
# ============================================================================
print("\n3️⃣ WDPA PROTECTED AREAS:")
wdpa_path = DATA_RAW / "wdpa"
wdpa_gdb = list(wdpa_path.glob("*.gdb"))
wdpa_shp = list(wdpa_path.rglob("*polygon*.shp"))

if wdpa_gdb:
    print(f"   File: {wdpa_gdb[0].name} (GDB)")
    try:
        wdpa = gpd.read_file(str(wdpa_gdb[0]))
        print(f"   CRS: {wdpa.crs}")
        print(f"   Features: {len(wdpa)}")
        print(f"   Bounds (minx, miny, maxx, maxy): {wdpa.total_bounds}")
    except Exception as e:
        print(f"   ⚠️  Could not read GDB: {e}")
elif wdpa_shp:
    print(f"   File: {wdpa_shp[0].name} (Shapefile)")
    try:
        wdpa = gpd.read_file(str(wdpa_shp[0]))
        print(f"   CRS: {wdpa.crs}")
        print(f"   Features: {len(wdpa)}")
        print(f"   Bounds (minx, miny, maxx, maxy): {wdpa.total_bounds}")
    except Exception as e:
        print(f"   ⚠️  Could not read shapefile: {e}")
else:
    print(f"   ℹ️  No WDPA data found")

# ============================================================================
# 4. WEATHER DATA (ERA5 CUTOUT)
# ============================================================================
print("\n4️⃣ WEATHER DATA (ERA5 CUTOUT):")
weather_file = DATA_RAW / "weather" / "portugal-2024.nc"

if weather_file.exists():
    print(f"   File: {weather_file.name}")
    print(f"   Size: {weather_file.stat().st_size / 1024 / 1024:.1f} MB")
    
    try:
        ds = xr.open_dataset(weather_file)
        print(f"   Dimensions: {dict(ds.dims)}")
        print(f"   Coordinates: {list(ds.coords.keys())}")
        
        if 'x' in ds.coords and 'y' in ds.coords:
            x_min, x_max = float(ds.x.min()), float(ds.x.max())
            y_min, y_max = float(ds.y.min()), float(ds.y.max())
            print(f"   X range: [{x_min:.2f}, {x_max:.2f}]")
            print(f"   Y range: [{y_min:.2f}, {y_max:.2f}]")
            print(f"   X cells: {len(ds.x)}")
            print(f"   Y cells: {len(ds.y)}")
            
            # Check overlap with Portugal
            print(f"\n   Checking overlap with Portugal:")
            x_overlap = not (shape.total_bounds[2] < x_min or shape.total_bounds[0] > x_max)
            y_overlap = not (shape.total_bounds[3] < y_min or shape.total_bounds[1] > y_max)
            
            if x_overlap and y_overlap:
                print(f"   ✅ WEATHER GRID COVERS PORTUGAL")
            else:
                print(f"   ❌ NO OVERLAP")
    except Exception as e:
        print(f"   ❌ Error reading weather data: {e}")
else:
    print(f"   ⚠️  File not found: {weather_file}")

# ============================================================================
# 5. COORDINATE SYSTEM ANALYSIS
# ============================================================================
print("\n5️⃣ COORDINATE SYSTEM ANALYSIS:")
print(f"   Portugal boundary CRS: {shape.crs}")

if corine_files:
    with rasterio.open(corine_files[0]) as src:
        print(f"   CORINE raster CRS:    {src.crs}")
        
        if shape.crs == src.crs:
            print(f"   ✅ CRS MATCH: Both are {shape.crs}")
        else:
            print(f"   ⚠️  CRS MISMATCH!")
            print(f"      Shape CRS:  {shape.crs}")
            print(f"      Raster CRS: {src.crs}")
            print(f"      This could cause the overlap error")

# ============================================================================
# 6. SOLUTION SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("SOLUTION RECOMMENDATIONS:")
print("=" * 80)
print("""
If there's a CRS mismatch, the fix is:
1. In Section 3.1, pass the CRS of the raster to excluder.add_raster()
2. Example: excluder.add_raster(str(corine_file), codes=codes_to_exclude, crs=4326, ...)
3. Let atlite handle the reprojection automatically (it will reproject to CRS 3035)

If there's a spatial extent issue:
1. Check that both datasets actually cover the Portugal region
2. The CRS 3035 (LAEA Europe) requires that all input datasets be in 4326 first
3. Make sure DATA_RAW paths point to actual downloaded files
""")

print("\n" + "=" * 80)
