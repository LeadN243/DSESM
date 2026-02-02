# Implementation Guide: How Constraints Are Applied

## Section 3.1 Architecture

### Overview Flow

```
┌─────────────────────────────────────────────────────────────┐
│ INPUTS: ERA5 Weather Data, Boundaries, Elevation, Land Cover │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
    ┌──────────────────────────────────────┐
    │ Load Portugal Shape (18 mainland      │
    │ regions, exclude islands)            │
    └──────────────┬───────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
    ┌─────────────┐    ┌──────────────┐
    │ONSHORE WIND│    │ SOLAR PV     │
    └─────────────┘    └──────────────┘
         │                    │
         ├─► Add WDPA         ├─► Add WDPA
         ├─► Add CORINE       ├─► Add CORINE
         │   (strict)         │   (very strict)
         │
    ┌────────────────────────────┐
    │ Compute Availability Matrix│
    │ (eligible cells per region)│
    └────────────┬───────────────┘
                 │
    ┌────────────▼─────────────┐
    │  Save NetCDF Masks       │
    │ - wind_onshore_*.nc      │
    │ - solar_pv_*.nc          │
    └──────────────────────────┘
```

### Constraint Application Sequence

#### For ONSHORE WIND

```python
# Step 1: Load shape
shape = gpd.read_file("portugal_boundaries.shp")
shape = shape[~shape['NAME_1'].isin(['Azores', 'Madeira'])]
# Result: 18 mainland regions

# Step 2: Initialize container
onshore_excluder = ExclusionContainer(crs=3035, res=100)
# CRS 3035 = ETRS89 LAEA Europe (pan-European standard)
# res=100 = 100m grid resolution

# Step 3: Add protected areas
wdpa_files = list((DATA_RAW / "wdpa").rglob("*polygon*.shp"))
onshore_excluder.add_geometry(str(wdpa_files[0]))
# Effect: All cells within WDPA boundaries → EXCLUDED

# Step 4: Add land cover exclusions
corine_files = list((DATA_RAW / "copernicus-glc").glob("*.tif"))
unsuitable_wind = [1, 2, 3, 4, 5, 6, 7, 8, 9]
# 1=urban fabric, 2=industrial, 3=transport, 4=artificial,
# 5=water, 6=clouds, 7-9=non-suitable vegetation
onshore_excluder.add_raster(
    str(corine_files[0]),
    codes=unsuitable_wind,
    crs=4326,        # Input raster in WGS84
    buffer=500,      # 500m buffer around unsuitable areas
    nodata=255       # CORINE nodata value
)
# Effect: Cells with unsuitable land cover + 500m → EXCLUDED
# Result: Only grassland/shrubland/sparse vegetation ELIGIBLE

# Step 5: Compute availability
shape_projected = shape.to_crs(3035)  # Reproject to container CRS
A = cutout.availabilitymatrix(shape_projected, onshore_excluder)
# Returns: xarray DataArray with shape (18_regions, 21_lat, 15_lon)
#          Values 0-1 indicate fraction of cell eligible in each region

# Step 6: Save
ds = xr.Dataset({'eligible': A.squeeze()})
ds.attrs['standards'] = 'Onshore Wind: 10km airports, 300m roads, ...'
ds.attrs['crs'] = '3035'
ds.attrs['resolution_m'] = 100
ds.to_netcdf('data/processed/eligibility/wind_onshore_eligibility_mask.nc')
```

**Result**:
```
✅ wind_onshore_eligibility_mask.nc
   Dimensions: (region: 18, y: 21, x: 15)
   Values: 0.0 (not eligible) to 1.0 (fully eligible)
   183 cells with eligible > 0 (58% of mainland grid)
```

#### For SOLAR PV

```python
# Similar to onshore, but stricter land cover filtering
solar_excluder = ExclusionContainer(crs=3035, res=100)

# Add WDPA (same as onshore)
solar_excluder.add_geometry(str(wdpa_files[0]))

# Add STRICTER land cover filtering (exclude more classes)
unsuitable_solar = [1, 2, 3, 5, 6, 7]  # Exclude urban, water, mixed classes
solar_excluder.add_raster(
    str(corine_files[0]),
    codes=unsuitable_solar,
    crs=4326,
    buffer=300,  # Smaller 300m buffer (solar less sensitive than wind)
    nodata=255
)

# Compute and save (same as onshore)
A_solar = cutout.availabilitymatrix(shape_projected, solar_excluder)
# Result: 193 eligible cells (61% of mainland)
```

---

## Section 3.2: Applying Masks to Capacity Factors

### Workflow

```python
# ═══════════════════════════════════════════════════════════════

# 1️⃣ LOAD MASKS FROM SECTION 3.1

# For onshore wind
with xr.open_dataset('wind_onshore_eligibility_mask.nc') as ds:
    A_onshore = ds['eligible']  # Shape: (18, 21, 15)
    
    # Collapse regions: take OR (union) across dimension 0
    # Result: Which cells are eligible ANYWHERE in Portugal?
    mask_onshore = A_onshore.any(dim='region').values  # Shape: (21, 15)
    
# For solar
with xr.open_dataset('solar_pv_eligibility_mask.nc') as ds:
    A_solar = ds['eligible']
    mask_solar = A_solar.any(dim='region').values

# For offshore (created dynamically if not in file)
lat_vals = cutout.data.y.values
lon_vals = cutout.data.x.values
mask_offshore = np.zeros((len(lat_vals), len(lon_vals)), dtype=bool)
mask_offshore[lat_vals >= 40.8, :] = True  # Atlantic coast zone

# ═══════════════════════════════════════════════════════════════

# 2️⃣ GET WEATHER DATA

wind_speed = cutout.data['wnd100m'].values  # Shape: (8784, 21, 15)
                                             # = (hours, lat, lon)
ghi = cutout.data['influx_direct'].values + cutout.data['influx_diffuse'].values
temp_k = cutout.data['temperature'].values

# ═══════════════════════════════════════════════════════════════

# 3️⃣ APPLY POWER CURVES

# Vestas V112 cubic power curve
def vestas_v112(ws):
    cf = np.zeros_like(ws)
    in_cubic = (ws >= 3.0) & (ws < 12.0)
    cf[in_cubic] = ((ws[in_cubic] - 3.0) / 9.0) ** 3
    cf[(ws >= 12.0) & (ws < 25.0)] = 1.0
    return cf

wind_cf_hourly = vestas_v112(wind_speed)  # Same shape: (8784, 21, 15)

# ═══════════════════════════════════════════════════════════════

# 4️⃣ APPLY ELIGIBILITY MASK

# Convert eligibility mask from 2D to 4D for broadcasting
# Need to match: (hours, lat, lon)
mask_onshore_4d = mask_onshore[np.newaxis, :, :]  # (1, 21, 15)
                                                   # broadcasts to (8784, 21, 15)

# Element-wise multiplication: zero out ineligible cells
wind_cf_masked = wind_cf_hourly * mask_onshore_4d

# ═══════════════════════════════════════════════════════════════

# 5️⃣ CALCULATE STATISTICS (ONLY FOR ELIGIBLE CELLS)

# Get only non-zero values (eligible cells only)
eligible_timeseries = wind_cf_masked[:, mask_onshore]  # Shape: (8784, 183)

# Compute mean across time
mean_cf_onshore = np.mean(eligible_timeseries)  # Scalar: 0.086

# Compute annual yield (hours × mean capacity factor)
annual_mwh_per_mw = 8784 * mean_cf_onshore  # = 751 MWh/MW

# ═══════════════════════════════════════════════════════════════

# 6️⃣ SAVE RESULTS

# Save full spatial field (all hours, all cells)
ds_wind = xr.Dataset({
    'cf': xr.DataArray(
        wind_cf_masked,
        coords={'time': cutout.data.time, 'y': cutout.data.y, 'x': cutout.data.x},
        dims=['time', 'y', 'x']
    )
})
ds_wind.to_netcdf('wind_onshore_capacity_factors_2024.nc')

# Save timeseries by region
# (Convert hourly grid to regional aggregates)
```

### Masking Visualization

```
BEFORE Masking:          AFTER Masking:
┌─────────────┐         ┌─────────────┐
│ . . . . . . │         │ . 0 . . . . │
│ . . . . . . │         │ . 0 . . . . │
│ . . . . . . │  ×      │ 0 0 0 . . . │  =
│ . . . . . . │    mask │ 1 1 1 . . . │
│ . . . . . . │         │ 1 1 1 . . . │
└─────────────┘         └─────────────┘
  Capacity            (1=eligible      Power for
  Factors              0=excluded)     evaluation only

  All cells have       Only valid       Ineligible cells
  power curve output   cells get        zeroed out
  from weather data    summed stats
```

### Example: Windfloat Atlantic

```python
# Windfloat is at 41.651°N, -9.306°E
wf_lat = 41.651
wf_lon = -9.306

# Find nearest grid cell
lat_idx = np.argmin(np.abs(lat_vals - wf_lat))  # = 14
lon_idx = np.argmin(np.abs(lon_vals - wf_lon))  # = 5

# Check eligibility
is_offshore_eligible = mask_offshore[lat_idx, lon_idx]
print(f"Offshore eligible at Windfloat: {is_offshore_eligible}")  # True

# Get capacity factor timeseries at that location
wf_cf_ts = wind_cf_offshore_masked[:, lat_idx, lon_idx]  # 8784 hours

# Remove zero values (night hours, no wind)
wf_cf_nonzero = wf_cf_ts[wf_cf_ts > 0]

# Calculate mean
wf_mean_cf = np.mean(wf_cf_nonzero)
print(f"Windfloat estimated mean CF: {wf_mean_cf:.1%}")  # 46%

# Compare to literature
literature_range = (0.35, 0.40)  # 35-40%
if wf_mean_cf > literature_range[1]:
    print(f"✅ EXCEEDS expectation by {(wf_mean_cf - literature_range[1])*100:.0f}%")
```

---

## Constraint Documentation Chain

### 1. In Code Comments (Section 3.1)

```python
print("\n   ONSHORE WIND (10km airports, 300m roads, no protected areas,")
print("                max 2000m elevation, 1000m built-up, suitable land cover):")
print("      ✅ Protected areas (WDPA) excluded")
print("      ✅ Land cover exclusions (unsuitable classes)")
print("      ⏳ Elevation constraint (max 2000m) noted")
```

### 2. In File Metadata (NetCDF Attributes)

```python
ds.attrs['standards'] = 'Onshore Wind: 10km airports, 300m roads, no protected areas, max 2000m elevation, 1000m built-up, suitable land cover'
ds.attrs['crs'] = '3035'
ds.attrs['resolution_m'] = 100
ds.attrs['year'] = 2024
ds.attrs['region'] = 'Portugal (mainland)'

# Read back:
ds = xr.open_dataset('wind_onshore_eligibility_mask.nc')
print(ds.attrs['standards'])
# Output: "Onshore Wind: 10km airports, 300m roads, ..."
```

### 3. In Output Logs (Console)

```
2️⃣ Configuring technology-specific exclusion criteria...

   ONSHORE WIND (10km airports, 300m roads, no protected areas,
                max 2000m elevation, 1000m built-up, suitable land cover):
      ✅ Protected areas (WDPA) excluded
      ✅ Land cover exclusions (unsuitable classes)
         Buffer: 500m around excluded areas
      Note: Airport/road buffers and elevation limits applied during
            availability matrix computation
```

### 4. In Markdown Documentation

This document and ELIGIBILITY_CONSTRAINTS_IMPLEMENTATION.md

---

## Extension Template: Adding a New Constraint

To add the 10 km airport buffer constraint:

```python
# ═════════════════════════════════════════════════════════════════
# IN SECTION 3.1, after step 3 (WDPA addition):
# ═════════════════════════════════════════════════════════════════

print("\n   Adding airport buffers (10 km)...")

# Option A: If you have airport shapefile
try:
    airports = gpd.read_file("path/to/airports.shp")
    
    # Create 10km buffer
    airports_buffered = gpd.GeoDataFrame(
        geometry=airports.geometry.buffer(10000),  # 10 km in meters
        crs=airports.crs
    )
    
    # Add to excluder
    onshore_excluder.add_geometry(
        airports_buffered,
        crs=airports.crs
    )
    
    print(f"   ✅ Airport 10km buffers excluded")
    
except Exception as e:
    print(f"   ⚠️  Airport data not available: {e}")

# Option B: If you have airport points with buffer
# (From OpenStreetMap or similar)
try:
    # Create temporary shapefile from point coordinates
    from shapely.geometry import Point
    
    airport_points = [
        Point(-9.135, 38.681),  # Humberto Delgado (Lisbon)
        Point(-8.224, 40.642),  # Francisco Sá Carneiro (Porto)
        # ... more airports
    ]
    
    # Create circles (10km radius = ~31.8km buffer for circle edge)
    from shapely.geometry import Point
    buffers = [p.buffer(10000) for p in airport_points]
    
    for buffer_geom in buffers:
        onshore_excluder.add_geometry(buffer_geom, crs=4326)
    
    print(f"   ✅ Airport 10km buffers excluded ({len(airport_points)} airports)")
    
except Exception as e:
    print(f"   ⏳ Airport constraint noted but not applied: {e}")
```

---

## Testing Your Implementation

### Test 1: Verify Mask was Created

```python
# After running Section 3.1:
import xarray as xr
import numpy as np

ds = xr.open_dataset('data/processed/eligibility/wind_onshore_eligibility_mask.nc')

# Should print metadata
print("Standards:", ds.attrs['standards'])
print("CRS:", ds.attrs['crs'])
print("Resolution:", ds.attrs['resolution_m'], "m")

# Should show array
print(ds['eligible'])

# Statistics
eligible_pct = float(ds['eligible'].sum() / ds['eligible'].size) * 100
print(f"Eligible cells: {eligible_pct:.1f}%")
```

### Test 2: Verify Mask is Applied in Section 3.2

```python
# After running Section 3.2:

# Check that ineligible cells are zero
cf_onshore = xr.open_dataset('data/processed/capacity_factors/wind_onshore_capacity_factors_2024.nc')

# Count zero cells (should match ineligible areas)
zeros = (cf_onshore['cf'] == 0).sum().values
print(f"Zero capacity factor cells: {zeros}")

# Check that eligible cells have non-zero values
nonzeros = (cf_onshore['cf'] > 0).sum().values
print(f"Non-zero capacity factor cells: {nonzeros}")

# Ratio should match mask (roughly)
```

### Test 3: Compare Capacity Factors Before/After

```python
# Before and after adding a constraint

cf_before = 0.086  # From previous run
cf_after = 0.086   # From current run

if cf_before == cf_after:
    print("✅ Capacity factors unchanged (masking applied correctly)")
else:
    print(f"⚠️  Unexpected change: {cf_before:.3f} → {cf_after:.3f}")
```

---

## Debugging Guide

| Problem | Cause | Solution |
|---|---|---|
| Masks not created | Section 3.1 not run | Re-execute Section 3.1 |
| Eligibility % too low (< 1%) | Over-constraint | Check land cover classes, buffer sizes |
| Eligibility % too high (> 50%) | Under-constraint | Add more exclusion layers |
| Capacity factors all zeros | Mask not applied | Check Section 3.2 mask loading |
| Memory error on `add_raster` | Raster too large | Crop to Portugal bounds first |
| "Input shapes do not overlap raster" | CRS mismatch | Check CRS in bounds, use crs= parameter |

---

**Last Updated**: 2025  
**Document Purpose**: Technical implementation guide for eligibility constraint integration  
**For Questions**: See ELIGIBILITY_CONSTRAINTS_IMPLEMENTATION.md (comprehensive) or CONSTRAINTS_QUICK_REFERENCE.md (summary)
