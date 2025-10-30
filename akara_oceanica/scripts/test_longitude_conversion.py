"""
Test script to validate longitude conversion and regional filtering for SAR and SWIM.

This script verifies that:
1. Longitude is properly converted to -180 to 180 format
2. Regional filtering works correctly for Akará region
3. All output files use consistent longitude format
"""

import pandas as pd
from pathlib import Path


def test_longitude_conversion():
    """Test that longitude conversion is working correctly."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    
    print("="*70)
    print("LONGITUDE CONVERSION VALIDATION TEST")
    print("="*70)
    print()
    
    # Test 1: Check SWIM analysis results
    print("Test 1: SWIM Analysis Results")
    print("-" * 70)
    swim_df = pd.read_csv(data_dir / 'swim_analysis_results.csv')
    print(f"Total records: {len(swim_df)}")
    print(f"Longitude range: {swim_df['lon'].min():.2f}° to {swim_df['lon'].max():.2f}°")
    
    # Check if any longitude is > 180 (should be false)
    invalid_lon = swim_df[swim_df['lon'] > 180]
    if len(invalid_lon) > 0:
        print(f"❌ FAILED: Found {len(invalid_lon)} records with lon > 180°")
        print(invalid_lon[['datetime', 'lon', 'lat']].head())
    else:
        print("✅ PASSED: All longitudes are in -180 to 180 format")
    print()
    
    # Test 2: Check SAR analysis results
    print("Test 2: SAR Analysis Results")
    print("-" * 70)
    sar_df = pd.read_csv(data_dir / 'sar_analysis_results.csv')
    print(f"Total records: {len(sar_df)}")
    print(f"Longitude range: {sar_df['lon'].min():.2f}° to {sar_df['lon'].max():.2f}°")
    
    invalid_lon = sar_df[sar_df['lon'] > 180]
    if len(invalid_lon) > 0:
        print(f"❌ FAILED: Found {len(invalid_lon)} records with lon > 180°")
        print(invalid_lon[['datetime', 'lon', 'lat']].head())
    else:
        print("✅ PASSED: All longitudes are in -180 to 180 format")
    print()
    
    # Test 3: Check Akará region filtering
    print("Test 3: Akará Region Filtering")
    print("-" * 70)
    akara_lon_min, akara_lon_max = -50.0, -30.0
    akara_lat_min, akara_lat_max = -45.0, -20.0
    
    swim_akara = pd.read_csv(data_dir / 'swim_akara_region.csv')
    print(f"SWIM Akará records: {len(swim_akara)}")
    print(f"Longitude range: {swim_akara['lon'].min():.2f}° to {swim_akara['lon'].max():.2f}°")
    print(f"Latitude range: {swim_akara['lat'].min():.2f}° to {swim_akara['lat'].max():.2f}°")
    
    # Check if all points are within bounds
    swim_outside = swim_akara[
        (swim_akara['lon'] < akara_lon_min) | 
        (swim_akara['lon'] > akara_lon_max) |
        (swim_akara['lat'] < akara_lat_min) |
        (swim_akara['lat'] > akara_lat_max)
    ]
    
    if len(swim_outside) > 0:
        print(f"❌ FAILED: Found {len(swim_outside)} SWIM records outside Akará region")
        print(swim_outside[['datetime', 'lon', 'lat']].head())
    else:
        print("✅ PASSED: All SWIM records are within Akará region bounds")
    print()
    
    sar_akara = pd.read_csv(data_dir / 'sar_akara_region.csv')
    print(f"SAR Akará records: {len(sar_akara)}")
    print(f"Longitude range: {sar_akara['lon'].min():.2f}° to {sar_akara['lon'].max():.2f}°")
    print(f"Latitude range: {sar_akara['lat'].min():.2f}° to {sar_akara['lat'].max():.2f}°")
    
    sar_outside = sar_akara[
        (sar_akara['lon'] < akara_lon_min) | 
        (sar_akara['lon'] > akara_lon_max) |
        (sar_akara['lat'] < akara_lat_min) |
        (sar_akara['lat'] > akara_lat_max)
    ]
    
    if len(sar_outside) > 0:
        print(f"❌ FAILED: Found {len(sar_outside)} SAR records outside Akará region")
        print(sar_outside[['datetime', 'lon', 'lat']].head())
    else:
        print("✅ PASSED: All SAR records are within Akará region bounds")
    print()
    
    # Test 4: Verify negative longitudes (western hemisphere)
    print("Test 4: Western Hemisphere Data (Negative Longitudes)")
    print("-" * 70)
    swim_west = swim_df[swim_df['lon'] < 0]
    sar_west = sar_df[sar_df['lon'] < 0]
    
    print(f"SWIM records with negative longitude: {len(swim_west)} ({len(swim_west)/len(swim_df)*100:.1f}%)")
    print(f"SAR records with negative longitude: {len(sar_west)} ({len(sar_west)/len(sar_df)*100:.1f}%)")
    
    if len(swim_west) > 0 and len(sar_west) > 0:
        print("✅ PASSED: Both datasets contain western hemisphere data")
    else:
        print("⚠️  WARNING: One or both datasets lack western hemisphere data")
    print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_tests_passed = (
        len(swim_df[swim_df['lon'] > 180]) == 0 and
        len(sar_df[sar_df['lon'] > 180]) == 0 and
        len(swim_outside) == 0 and
        len(sar_outside) == 0
    )
    
    if all_tests_passed:
        print("✅ ALL TESTS PASSED")
        print()
        print("Longitude conversion is working correctly!")
        print("Regional filtering is accurate!")
        print("Data files are ready for analysis!")
    else:
        print("❌ SOME TESTS FAILED")
        print()
        print("Please review the errors above and re-run the analysis scripts.")
    
    print("="*70)


if __name__ == '__main__':
    test_longitude_conversion()
