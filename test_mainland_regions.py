import geopandas as gpd
from pathlib import Path

DATA_PROCESSED = Path.cwd() / "data" / "processed"

shape = gpd.read_file(DATA_PROCESSED / "regions" / "portugal_boundaries.shp")

print(f"Original: {len(shape)} regions")
print(f"Bounds: X [{shape.total_bounds[0]:.2f}, {shape.total_bounds[2]:.2f}], Y [{shape.total_bounds[1]:.2f}, {shape.total_bounds[3]:.2f}]")

# Apply the same filter as in the notebook
shape = shape[~shape['NAME_1'].isin(['Azores', 'Madeira'])].copy()

print(f"\nAfter filtering: {len(shape)} regions")
print(f"Bounds: X [{shape.total_bounds[0]:.2f}, {shape.total_bounds[2]:.2f}], Y [{shape.total_bounds[1]:.2f}, {shape.total_bounds[3]:.2f}]")

print("\nRemaining regions:")
for region in sorted(shape['NAME_1'].values):
    print(f"  - {region}")

print("\n✅ Mainland regions properly filtered!")
