import geopandas as gpd
from pathlib import Path

DATA_PROCESSED = Path.cwd() / "data" / "processed"

shape = gpd.read_file(DATA_PROCESSED / "regions" / "portugal_boundaries.shp")

print("Portugal Regions:")
for idx, row in shape.iterrows():
    bounds = row.geometry.bounds
    print(f"  {row['NAME_1']:15s} - X: [{bounds[0]:7.2f}, {bounds[2]:7.2f}], Y: [{bounds[1]:6.2f}, {bounds[3]:6.2f}]")

print("\nNote: Regions with X < -12 (far west) should be excluded (Azores, Madeira)")
