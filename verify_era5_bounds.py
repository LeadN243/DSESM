"""Verify ERA5 weather data bounds against assignment requirements"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("GEOGRAPHIC BOUNDS VERIFICATION")
print("="*70)

# Portugal mainland bounds (from GADM data)
portugal_lon_min = -9.55
portugal_lon_max = -6.19
portugal_lat_min = 36.96
portugal_lat_max = 42.15
buffer = 0.25

print("\nPortugal mainland bounds (from GADM):")
print(f"  Lon: {portugal_lon_min} to {portugal_lon_max}")
print(f"  Lat: {portugal_lat_min} to {portugal_lat_max}")

# Required bounds with 0.25 buffer
expected_lon_min = portugal_lon_min - buffer
expected_lon_max = portugal_lon_max + buffer
expected_lat_min = portugal_lat_min - buffer
expected_lat_max = portugal_lat_max + buffer

print(f"\nRequired with 0.25 buffer:")
print(f"  Lon: {expected_lon_min:.2f} to {expected_lon_max:.2f}")
print(f"  Lat: {expected_lat_min:.2f} to {expected_lat_max:.2f}")

# Current cutout bounds
actual_lon_min = -9.5
actual_lon_max = -6.0
actual_lat_min = 37.0
actual_lat_max = 42.0

print("\nCurrent cutout bounds:")
print(f"  Lon: {actual_lon_min} to {actual_lon_max}")
print(f"  Lat: {actual_lat_min} to {actual_lat_max}")

print("\nISSUE ANALYSIS:")
issues = []

if actual_lon_min <= expected_lon_min:
    print("  [OK] Western boundary ok")
else:
    print(f"  [ISSUE] Western: need {expected_lon_min:.2f}, have {actual_lon_min}")
    issues.append("west")

if actual_lon_max >= expected_lon_max:
    print("  [OK] Eastern boundary ok")
else:
    print(f"  [ISSUE] Eastern: need {expected_lon_max:.2f}, have {actual_lon_max}")
    issues.append("east")

if actual_lat_min <= expected_lat_min:
    print("  [OK] Southern boundary ok")
else:
    print(f"  [ISSUE] Southern: need {expected_lat_min:.2f}, have {actual_lat_min}")
    issues.append("south")

if actual_lat_max >= expected_lat_max:
    print("  [OK] Northern boundary ok")
else:
    print(f"  [ISSUE] Northern: need {expected_lat_max:.2f}, have {actual_lat_max}")
    issues.append("north")

print("\n" + "="*70)
if issues:
    print(f"RESULT: Bounds need adjustment ({', '.join(issues)} boundary/ies)")
else:
    print("RESULT: All bounds are sufficient")
print("="*70)
