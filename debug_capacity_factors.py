"""
Comprehensive diagnostic script to investigate capacity factor calculation issues
"""

import atlite
import xarray as xr
import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 80)
print("DEBUGGING CAPACITY FACTOR CALCULATION")
print("=" * 80)

DATA_RAW = Path("data") / "raw"
DATA_PROCESSED = Path("data") / "processed"
CUTOUT_FILE = DATA_RAW / "weather" / "portugal-2024.nc"

# 1. Check cutout file exists and structure
print("\n1️⃣ CHECKING CUTOUT FILE")
print("-" * 80)
if CUTOUT_FILE.exists():
    print(f"✅ File exists: {CUTOUT_FILE}")
    print(f"   Size: {CUTOUT_FILE.stat().st_size / (1024**2):.1f} MB")
    
    # Load with xarray directly
    print("\n2️⃣ LOADING WITH XARRAY")
    print("-" * 80)
    with xr.open_dataset(CUTOUT_FILE) as ds:
        print(f"Dimensions: {dict(ds.dims)}")
        print(f"Coordinates: {list(ds.coords.keys())}")
        print(f"Variables: {list(ds.data_vars.keys())}")
        print(f"\nTime range: {ds.time.values[0]} to {ds.time.values[-1]}")
        print(f"Lat range: {float(ds.y.min()):.2f} to {float(ds.y.max()):.2f}")
        print(f"Lon range: {float(ds.x.min()):.2f} to {float(ds.x.max()):.2f}")
        print(f"Grid shape: {len(ds.y)} x {len(ds.x)}")
        
        # Check key variables
        print(f"\nKey variable shapes:")
        for var in ['wnd100m', 'influx_direct', 'influx_diffuse', 'temperature']:
            if var in ds.data_vars:
                print(f"  {var}: {ds[var].shape}")
    
    # 3. Load with atlite
    print("\n3️⃣ LOADING WITH ATLITE")
    print("-" * 80)
    try:
        cutout = atlite.Cutout(path=str(CUTOUT_FILE))
        print(f"✅ Cutout loaded successfully")
        print(f"   Path: {cutout.path}")
        print(f"   Time steps: {len(cutout.data.time)}")
        print(f"   Grid: {len(cutout.data.y)} x {len(cutout.data.x)}")
        print(f"   Variables: {list(cutout.data.data_vars.keys())[:8]}")
        
        # 4. Test wind calculation
        print("\n4️⃣ TESTING WIND CALCULATION")
        print("-" * 80)
        try:
            print("Computing wind with cutout.wind()...")
            wind_cf = cutout.wind(turbine='Vestas_V112_3MW')
            print(f"✅ Wind calculation successful!")
            print(f"   Type: {type(wind_cf)}")
            print(f"   Dims: {wind_cf.dims if hasattr(wind_cf, 'dims') else 'N/A'}")
            print(f"   Shape: {wind_cf.shape if hasattr(wind_cf, 'shape') else 'N/A'}")
            print(f"   Size: {wind_cf.sizes if hasattr(wind_cf, 'sizes') else 'N/A'}")
            if hasattr(wind_cf, 'values'):
                print(f"   Data dtype: {wind_cf.values.dtype}")
                print(f"   Min: {np.nanmin(wind_cf.values):.4f}, Max: {np.nanmax(wind_cf.values):.4f}")
                print(f"   Mean: {np.nanmean(wind_cf.values):.4f}")
            
            # Get first 3 cells stats
            if len(wind_cf.shape) == 3:
                print(f"\n   First cell (0,0) sample values: {wind_cf.values[:5, 0, 0]}")
                
        except Exception as e:
            print(f"❌ Wind calculation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # 5. Test solar calculation
        print("\n5️⃣ TESTING SOLAR CALCULATION")
        print("-" * 80)
        try:
            print("Computing solar with cutout.pv()...")
            solar_cf = cutout.pv(panel='CSi', orientation='latitude_optimal')
            print(f"✅ Solar calculation successful!")
            print(f"   Type: {type(solar_cf)}")
            print(f"   Dims: {solar_cf.dims if hasattr(solar_cf, 'dims') else 'N/A'}")
            print(f"   Shape: {solar_cf.shape if hasattr(solar_cf, 'shape') else 'N/A'}")
            print(f"   Size: {solar_cf.sizes if hasattr(solar_cf, 'sizes') else 'N/A'}")
            if hasattr(solar_cf, 'values'):
                print(f"   Data dtype: {solar_cf.values.dtype}")
                print(f"   Min: {np.nanmin(solar_cf.values):.4f}, Max: {np.nanmax(solar_cf.values):.4f}")
                print(f"   Mean: {np.nanmean(solar_cf.values):.4f}")
                
            if len(solar_cf.shape) == 3:
                print(f"\n   First cell (0,0) sample values: {solar_cf.values[:5, 0, 0]}")
                
        except Exception as e:
            print(f"❌ Solar calculation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # 6. Check eligibility masks
        print("\n6️⃣ CHECKING ELIGIBILITY MASKS")
        print("-" * 80)
        for tech in ['wind_onshore', 'solar_pv']:
            mask_file = DATA_PROCESSED / "eligibility" / f"{tech}_eligibility_mask.nc"
            if mask_file.exists():
                with xr.open_dataset(mask_file) as ds:
                    mask = ds['eligible'].values
                    print(f"{tech}:")
                    print(f"  Shape: {mask.shape}")
                    print(f"  Eligible cells: {mask.sum()} out of {mask.size}")
                    print(f"  Eligible %: {mask.sum() / mask.size * 100:.1f}%")
            else:
                print(f"{tech}: ❌ NOT FOUND")
        
        # 7. Portugal coordinates check
        print("\n7️⃣ PORTUGAL COORDINATES CHECK")
        print("-" * 80)
        PORTUGAL_COORDS = {
            'lat_min': 37.0,
            'lat_max': 42.0,
            'lon_min': -9.5,
            'lon_max': -6.0
        }
        print(f"Expected Portugal bounds:")
        print(f"  Lat: {PORTUGAL_COORDS['lat_min']}° to {PORTUGAL_COORDS['lat_max']}°")
        print(f"  Lon: {PORTUGAL_COORDS['lon_min']}° to {PORTUGAL_COORDS['lon_max']}°")
        print(f"\nActual cutout bounds:")
        print(f"  Lat: {float(cutout.data.y.min()):.2f}° to {float(cutout.data.y.max()):.2f}°")
        print(f"  Lon: {float(cutout.data.x.min()):.2f}° to {float(cutout.data.x.max()):.2f}°")
        
    except Exception as e:
        print(f"❌ Atlite loading failed: {e}")
        import traceback
        traceback.print_exc()

else:
    print(f"❌ File not found: {CUTOUT_FILE}")
    print(f"   Expected path: {CUTOUT_FILE.resolve()}")
    
print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
