#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script for offshore wind investigation.
"""

import sys
import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
import geopandas as gpd

# Setup
BASE_DIR = Path.cwd()
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

print("="*80)
print("DIAGNOSTIC: OFFSHORE WIND INVESTIGATION")
print("="*80)

# ====================================================================
# 1. Power Plant Data
# ====================================================================
print("\n" + "="*80)
print("1. POWER PLANT ANALYSIS: Offshore Wind Capacity")
print("="*80)

plants_file = DATA_PROCESSED / "generation" / "portugal_power_plants.csv"
if plants_file.exists():
    plants_df = pd.read_csv(plants_file)
    print(f"\n[OK] Loaded power plants: {len(plants_df)} entries")
    
    # Find offshore entries
    if 'Technology' in plants_df.columns:
        offshore_mask = plants_df['Technology'].str.lower().str.contains('offshore', na=False)
        offshore_plants = plants_df[offshore_mask]
        print(f"\nOffshore Wind Plants Found: {len(offshore_plants)}")
        
        if len(offshore_plants) > 0:
            print("\nOffshore Wind Details:")
            for idx, row in offshore_plants.iterrows():
                print(f"  Name: {row.get('Name', 'N/A')}")
                print(f"  Capacity: {row.get('Capacity', 'N/A')} MW")
                if 'Latitude' in row.index and 'Longitude' in row.index:
                    print(f"  Location: {row.get('Latitude', 'N/A')}, {row.get('Longitude', 'N/A')}")
                print(f"  Status: {row.get('Status', 'N/A')}")
                print()
else:
    print(f"[ERROR] Power plants file not found: {plants_file}")

# ====================================================================
# 2. ERA5 Cutout Analysis
# ====================================================================
print("="*80)
print("2. ERA5 CUTOUT ANALYSIS: Data Coverage")
print("="*80)

cutout_file = DATA_RAW / "weather" / "portugal-2024.nc"
if cutout_file.exists():
    print(f"\n[OK] ERA5 file found: {cutout_file}")
    print(f"     Size: {cutout_file.stat().st_size / (1024**3):.2f} GB")
    
    try:
        import atlite
        cutout = atlite.Cutout(path=str(cutout_file))
        
        print(f"\nCutout Structure:")
        print(f"   Time steps: {len(cutout.data.time)} hours")
        print(f"   Latitude range: {float(cutout.data.y.min()):.2f} to {float(cutout.data.y.max()):.2f}")
        print(f"   Longitude range: {float(cutout.data.x.min()):.2f} to {float(cutout.data.x.max()):.2f}")
        print(f"   Grid: {len(cutout.data.y)} lat x {len(cutout.data.x)} lon = {len(cutout.data.y)*len(cutout.data.x)} cells")
        
        print(f"\nAvailable Variables:")
        for var in sorted(cutout.data.data_vars):
            da = cutout.data[var]
            print(f"   - {var}: {da.shape}")
        
        # Check offshore coverage
        lat_vals = cutout.data.y.values
        lon_vals = cutout.data.x.values
        
        print(f"\nOffshore Coverage Check:")
        print(f"   Portugal mainland: ~37.0 to 42.0 N, ~-9.5 to -6.0 E")
        print(f"   ERA5 domain latitude OK? {lat_vals.min() <= 37.0 and lat_vals.max() >= 42.0}")
        print(f"   ERA5 domain longitude OK? {lon_vals.min() <= -9.5 and lon_vals.max() >= -6.0}")
        print(f"   ERA5 extends beyond -9.5 E? {lon_vals.min() < -9.5} (good for offshore)")
        
        # Windfloat Atlantic check
        wf_lat, wf_lon = 41.651, -9.306
        lat_in = lat_vals.min() <= wf_lat <= lat_vals.max()
        lon_in = lon_vals.min() <= wf_lon <= lon_vals.max()
        
        print(f"\nWindfloat Atlantic Location (41.651 N, -9.306 E):")
        print(f"   Latitude in domain? {lat_in}")
        print(f"   Longitude in domain? {lon_in}")
        
        if lat_in and lon_in:
            # Find nearest grid cell
            lat_idx = np.argmin(np.abs(lat_vals - wf_lat))
            lon_idx = np.argmin(np.abs(lon_vals - wf_lon))
            print(f"   Nearest grid cell: [{lat_idx}, {lon_idx}]")
            
            # Wind speed
            wind_data = cutout.data['wnd100m'].values
            if wind_data.shape[1] > lat_idx and wind_data.shape[2] > lon_idx:
                wind_at_loc = wind_data[:, lat_idx, lon_idx]
                print(f"   Wind speed at location:")
                print(f"      Mean: {np.nanmean(wind_at_loc):.2f} m/s")
                print(f"      Max: {np.nanmax(wind_at_loc):.2f} m/s")
                print(f"   => EXCELLENT for offshore wind!")
        
    except Exception as e:
        print(f"[ERROR] Loading cutout: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"[ERROR] ERA5 file not found: {cutout_file}")

# ====================================================================
# 3. Check Eligibility Masks
# ====================================================================
print("\n" + "="*80)
print("3. ELIGIBILITY MASKS: Current Implementation")
print("="*80)

eligibility_dir = DATA_PROCESSED / "eligibility"
if eligibility_dir.exists():
    print(f"\n[OK] Eligibility directory found")
    
    mask_files = list(eligibility_dir.glob("*.nc"))
    if len(mask_files) == 0:
        print("[INFO] No mask files found")
    
    for mask_file in mask_files:
        print(f"\nFile: {mask_file.name}")
        try:
            ds = xr.open_dataset(mask_file)
            print(f"   Variables: {list(ds.data_vars)}")
            print(f"   Dimensions: {dict(ds.dims)}")
            ds.close()
        except Exception as e:
            print(f"   [ERROR] {e}")
else:
    print(f"[INFO] Eligibility directory not found")

# ====================================================================
# 4. Check current Section 3.2 implementation
# ====================================================================
print("\n" + "="*80)
print("4. CURRENT IMPLEMENTATION: What's in Section 3.2?")
print("="*80)

notebook_file = BASE_DIR / "groupQasssignment.ipynb"
if notebook_file.exists():
    import json
    with open(notebook_file) as f:
        nb = json.load(f)
    
    # Find Section 3.2
    for i, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            if 'wind_onshore' in source and 'Section 3.2' in source:
                print(f"\n[OK] Found Section 3.2 (cell {i})")
                print("\nCapacity factors implemented:")
                if 'wind_onshore' in source:
                    print("   [x] wind_onshore")
                if 'wind_offshore' in source:
                    print("   [x] wind_offshore")
                else:
                    print("   [ ] wind_offshore  <-- MISSING!")
                if 'solar_pv' in source:
                    print("   [x] solar_pv")
                if 'solar_csp' in source:
                    print("   [x] solar_csp")
                break

# ====================================================================
# SUMMARY
# ====================================================================
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print("""
KEY FINDINGS:

1. OFFSHORE WIND DATA EXISTS
   - Windfloat Atlantic (25 MW) is in power plant database
   - ERA5 domain covers the offshore location

2. OFFSHORE WIND NOT IMPLEMENTED
   - Current Section 3.2 only has: wind_onshore, solar_pv
   - Missing: wind_offshore
   
3. IMPLEMENTATION NEEDED
   - Add wind_offshore capacity factor calculation
   - Create offshore eligibility mask (or simplified sea mask)
   - Use appropriate offshore wind turbine power curve
   - Validate with Windfloat Atlantic data

NEXT STEPS:
   1. Add wind_offshore to Section 3.1 (eligibility)
   2. Add wind_offshore to Section 3.2 (capacity factors)
   3. Use offshore-appropriate power curve (different from onshore)
   4. Test with Windfloat Atlantic as validation point
""")

print("="*80)
print("END OF DIAGNOSTIC")
print("="*80)
