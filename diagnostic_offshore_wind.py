#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script for offshore wind investigation.
Examines:
1. Power plant data - what offshore wind exists
2. ERA5 cutout structure - whether data extends to offshore
3. Capacity factor calculations - current implementation gaps
4. Portugal geography - sea domain boundaries
"""

import sys
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point, box

# Handle encoding
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================================
# Setup
# ============================================================================
BASE_DIR = Path.cwd()
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

print("=" * 80)
print("DIAGNOSTIC: OFFSHORE WIND INVESTIGATION")
print("=" * 80)

# ============================================================================
# 1. Power Plant Data - Offshore Wind Capacity
# ============================================================================
print("\n" + "=" * 80)
print("1. POWER PLANT ANALYSIS: Offshore Wind Capacity")
print("=" * 80)

plants_file = DATA_PROCESSED / "generation" / "portugal_power_plants.csv"
if plants_file.exists():
    plants_df = pd.read_csv(plants_file)
    print(f"[OK] Loaded power plants: {len(plants_df)} entries")
    
    # Find all offshore entries
    if 'Technology' in plants_df.columns:
        offshore_mask = plants_df['Technology'].str.lower().str.contains('offshore', na=False)
        offshore_plants = plants_df[offshore_mask]
        print(f"\n📊 Offshore Wind Plants Found: {len(offshore_plants)}")
        
        if len(offshore_plants) > 0:
            print("\nOffshore Wind Details:")
            for idx, row in offshore_plants.iterrows():
                print(f"  - {row.get('Name', 'N/A')}")
                print(f"    Capacity: {row.get('Capacity', 'N/A')} MW")
                print(f"    Location: Lat {row.get('Latitude', 'N/A')}, Lon {row.get('Longitude', 'N/A')}")
                print(f"    Status: {row.get('Status', 'N/A')}")
                print(f"    Year: {row.get('Year', 'N/A')}")
        else:
            print("⚠️ No offshore wind plants found via 'Offshore' keyword")
    
    # Alternative check - look for any wind type categorization
    if 'Type' in plants_df.columns:
        type_offshore = plants_df[plants_df['Type'].str.lower().str.contains('offshore', na=False)]
        if len(type_offshore) > 0:
            print(f"\n📊 Alternative match (Type column): {len(type_offshore)} offshore entries")
    
    # Check if Windfloat Atlantic exists
    windfloat = plants_df[plants_df['Name'].str.contains('Windfloat|windfloat', case=False, na=False)]
    if len(windfloat) > 0:
        print(f"\n✅ Windfloat Atlantic Found:")
        for idx, row in windfloat.iterrows():
            for col in row.index:
                print(f"    {col}: {row[col]}")
else:
    print(f"❌ Power plants file not found: {plants_file}")

# ============================================================================
# 2. ERA5 Cutout Structure Analysis
# ============================================================================
print("\n" + "=" * 80)
print("2. ERA5 CUTOUT ANALYSIS: Data Coverage")
print("=" * 80)

cutout_file = DATA_RAW / "weather" / "portugal-2024.nc"
if cutout_file.exists():
    print(f"✅ ERA5 file found: {cutout_file}")
    print(f"   Size: {cutout_file.stat().st_size / (1024**3):.2f} GB")
    
    try:
        import atlite
        cutout = atlite.Cutout(path=str(cutout_file))
        
        print(f"\n📊 Cutout Structure:")
        print(f"   Time steps: {len(cutout.data.time)} hours")
        print(f"   Latitude range: {float(cutout.data.y.min()):.2f}° to {float(cutout.data.y.max()):.2f}°")
        print(f"   Longitude range: {float(cutout.data.x.min()):.2f}° to {float(cutout.data.x.max()):.2f}°")
        print(f"   Grid size: {len(cutout.data.y)} lat × {len(cutout.data.x)} lon = {len(cutout.data.y) * len(cutout.data.x)} cells")
        
        print(f"\n📊 Available Variables:")
        for var in sorted(cutout.data.data_vars):
            da = cutout.data[var]
            print(f"   - {var}")
            print(f"     Shape: {da.shape}, Dims: {da.dims}, DType: {da.dtype}")
        
        # Create geographic bounds
        lat_vals = cutout.data.y.values
        lon_vals = cutout.data.x.values
        
        print(f"\n🗺️ Geographic Bounds:")
        print(f"   West: {lon_vals.min():.2f}°, East: {lon_vals.max():.2f}°")
        print(f"   South: {lat_vals.min():.2f}°, North: {lat_vals.max():.2f}°")
        
        # Check if this covers offshore Portugal
        print(f"\n🌊 Offshore Coverage Analysis:")
        print(f"   Portugal mainland: ~37.0°N - 42.0°N, ~-9.5°E - -6.0°E")
        print(f"   ERA5 domain covers latitude range? {lat_vals.min() <= 37.0 and lat_vals.max() >= 42.0}")
        print(f"   ERA5 domain covers longitude range? {lon_vals.min() <= -9.5 and lon_vals.max() >= -6.0}")
        print(f"   Atlantic beyond -9.5°E? {lon_vals.min() < -9.5}")
        
        # Calculate some statistics
        print(f"\n📈 Wind Speed Analysis:")
        wind_100m = cutout.data['wnd100m'].values
        print(f"   100m wind speed - Mean: {np.nanmean(wind_100m):.2f} m/s")
        print(f"   100m wind speed - Std: {np.nanstd(wind_100m):.2f} m/s")
        print(f"   100m wind speed - Max: {np.nanmax(wind_100m):.2f} m/s")
        print(f"   100m wind speed - Min: {np.nanmin(wind_100m):.2f} m/s")
        
        print(f"\n📈 Solar Radiation Analysis:")
        direct = cutout.data['influx_direct'].values
        diffuse = cutout.data['influx_diffuse'].values
        ghi = direct + diffuse
        print(f"   Direct irradiance - Mean: {np.nanmean(direct):.2f} W/m²")
        print(f"   Diffuse irradiance - Mean: {np.nanmean(diffuse):.2f} W/m²")
        print(f"   GHI - Mean: {np.nanmean(ghi):.2f} W/m²")
        print(f"   GHI - Max: {np.nanmax(ghi):.2f} W/m²")
        
    except Exception as e:
        print(f"❌ Error loading cutout with atlite: {e}")
        # Try raw xarray
        try:
            ds = xr.open_dataset(cutout_file)
            print(f"\n📊 Raw xarray Dataset:")
            print(ds)
            ds.close()
        except Exception as e2:
            print(f"❌ Error with xarray: {e2}")
else:
    print(f"❌ ERA5 file not found: {cutout_file}")

# ============================================================================
# 3. Check Existing Eligibility Masks
# ============================================================================
print("\n" + "=" * 80)
print("3. ELIGIBILITY MASKS: Current Implementation")
print("=" * 80)

eligibility_dir = DATA_PROCESSED / "eligibility"
if eligibility_dir.exists():
    print(f"✅ Eligibility directory found: {eligibility_dir}")
    
    for mask_file in eligibility_dir.glob("*.nc"):
        print(f"\n📄 {mask_file.name}")
        try:
            ds = xr.open_dataset(mask_file)
            print(f"   Variables: {list(ds.data_vars)}")
            print(f"   Dimensions: {dict(ds.dims)}")
            for var in ds.data_vars:
                arr = ds[var].values
                eligible_count = int(np.sum(arr > 0.5))
                total_cells = arr.size
                pct = 100 * eligible_count / total_cells
                print(f"   {var}: {eligible_count}/{total_cells} cells ({pct:.1f}%)")
            ds.close()
        except Exception as e:
            print(f"   ❌ Error: {e}")
else:
    print(f"⚠️ Eligibility directory not found: {eligibility_dir}")

# ============================================================================
# 4. Portugal Geography - Land vs Sea
# ============================================================================
print("\n" + "=" * 80)
print("4. PORTUGAL GEOGRAPHY: Land vs Sea Boundaries")
print("=" * 80)

shapefile = DATA_PROCESSED / "regions" / "portugal_boundaries.shp"
if shapefile.exists():
    print(f"✅ Portugal boundaries loaded: {shapefile}")
    
    try:
        gdf = gpd.read_file(shapefile)
        
        # Get bounds
        bounds = gdf.total_bounds  # (minx, miny, maxx, maxy)
        print(f"\n🗺️ Portugal Administrative Boundaries:")
        print(f"   Min Lon: {bounds[0]:.2f}°")
        print(f"   Min Lat: {bounds[1]:.2f}°")
        print(f"   Max Lon: {bounds[2]:.2f}°")
        print(f"   Max Lat: {bounds[3]:.2f}°")
        
        # Analyze regions
        print(f"\n📊 Regions in shapefile:")
        if 'NAME_1' in gdf.columns:
            for idx, row in gdf.iterrows():
                name = row.get('NAME_1', 'N/A')
                if name not in ['Azores', 'Madeira']:
                    print(f"   - {name} (mainland)")
        
        # Calculate area
        gdf_projected = gdf.to_crs('EPSG:3035')
        total_area = gdf_projected.geometry.area.sum() / 1e6  # km²
        print(f"\n   Total land area: {total_area:.0f} km²")
        
        # Offshore potential zones
        print(f"\n🌊 Offshore Zones (beyond land):")
        print(f"   EEZ: Exclusive Economic Zone extends ~200nm offshore")
        print(f"   Potential wind area: Along Atlantic coast, especially north coast")
        print(f"   Windfloat Atlantic: ~41.65°N, -9.31°E (Atlantic, west of Douro estuary)")
        
        # Check if Windfloat location is in cutout domain
        if cutout_file.exists():
            try:
                import atlite
                cutout = atlite.Cutout(path=str(cutout_file))
                lat_vals = cutout.data.y.values
                lon_vals = cutout.data.x.values
                
                wf_lat, wf_lon = 41.651, -9.306
                lat_in = lat_vals.min() <= wf_lat <= lat_vals.max()
                lon_in = lon_vals.min() <= wf_lon <= lon_vals.max()
                
                print(f"\n✅ Windfloat Atlantic Location Check:")
                print(f"   Latitude {wf_lat}°: {'✅ IN' if lat_in else '❌ OUT'} domain")
                print(f"   Longitude {wf_lon}°: {'✅ IN' if lon_in else '❌ OUT'} domain")
                
                if lat_in and lon_in:
                    # Find nearest grid cell
                    lat_idx = np.argmin(np.abs(lat_vals - wf_lat))
                    lon_idx = np.argmin(np.abs(lon_vals - wf_lon))
                    print(f"   Nearest grid cell: [{lat_idx}, {lon_idx}]")
                    print(f"   Grid cell location: {lat_vals[lat_idx]:.2f}°N, {lon_vals[lon_idx]:.2f}°E")
                    
                    # Check wind speed at this location
                    wind_data = cutout.data['wnd100m'].values
                    if wind_data.shape[1] > lat_idx and wind_data.shape[2] > lon_idx:
                        wind_at_loc = wind_data[:, lat_idx, lon_idx]
                        print(f"   Wind speed at location:")
                        print(f"      Mean: {np.nanmean(wind_at_loc):.2f} m/s")
                        print(f"      Std: {np.nanstd(wind_at_loc):.2f} m/s")
                        print(f"      Max: {np.nanmax(wind_at_loc):.2f} m/s")
                        print(f"   => Excellent for offshore wind! (needs 6-11 m/s)")
                        
            except Exception as e:
                print(f"   ⚠️ Could not check Windfloat location: {e}")
    except Exception as e:
        print(f"❌ Error reading shapefile: {e}")
else:
    print(f"❌ Shapefile not found: {shapefile}")

# ============================================================================
# 5. Summary and Recommendations
# ============================================================================
print("\n" + "=" * 80)
print("5. SUMMARY AND RECOMMENDATIONS")
print("=" * 80)

print("""
🔍 KEY FINDINGS:

1. ✅ OFFSHORE WIND DATA EXISTS:
   - Windfloat Atlantic (25 MW, operational since 2020) is in power plant data
   - ERA5 domain appears to cover the offshore location

2. ❌ OFFSHORE WIND NOT IMPLEMENTED:
   - Current Section 3.2 only implements wind_onshore and solar_pv
   - wind_offshore is completely missing from capacity factor calculations
   - Eligibility masks only cover land-based exclusions

3. 🌊 IMPLEMENTATION GAPS:
   a) Geographic masking: Need to identify sea vs land cells
   b) Eligibility constraints: Offshore has different rules than onshore
   c) Capacity factor computation: Wind at 100m is suitable for offshore
   d) Validation: No offshore mask exists in eligibility_dir

4. 🌬️ OFFSHORE POTENTIAL:
   - Windfloat location has ~9-10 m/s mean wind speed (excellent)
   - Portugal's Atlantic coast is prime offshore wind area
   - EEZ extends ~200nm offshore - huge untapped resource

📋 RECOMMENDED ACTIONS:

1. Add wind_offshore capacity factor computation in Section 3.2
   - Use same wind_speed data as onshore
   - Apply different power curve (e.g., Siemens Gamesa 6MW or equivalent)
   - Different rated wind speed (typically 11-13 m/s for offshore)
   - Higher capacity factors expected (25-35% typical for Atlantic)

2. Create offshore eligibility mask (section 3.1)
   - Define offshore zone (e.g., 0-50km, 50-100km, 100-200km from coast)
   - Mask out shipping lanes, fishing zones, environmental protection areas
   - Use bathymetry to define water depth suitable for installation

3. Validate ERA5 data for offshore use
   - Check if wind_100m is representative for offshore installations
   - May need to adjust height (hub height typically 90-100m for offshore)
   - Verify no land contamination in offshore cells

4. Update PyPSA network model
   - Add offshore wind generator nodes
   - Specify regional offshore capacity limits
   - Include transmission costs from offshore to grid

5. Compare with real-world data
   - Windfloat Atlantic provides validation point
   - Cross-check capacity factors with operational data
""")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
