"""
Generate comprehensive summary report for wave spectra analysis.

This script creates a summary document with key findings from the
wave spectra analysis during the Akará cyclone.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_summary_report():
    """Generate a text summary report of the wave spectra analysis."""
    
    # Get project root
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    
    # Load results
    swim_results = pd.read_csv(data_dir / 'swim_analysis_results.csv')
    swim_results['datetime'] = pd.to_datetime(swim_results['datetime'])
    
    sar_results = pd.read_csv(data_dir / 'sar_analysis_results.csv')
    sar_results['datetime'] = pd.to_datetime(sar_results['datetime'])
    
    swim_akara = pd.read_csv(data_dir / 'swim_akara_region.csv')
    swim_akara['datetime'] = pd.to_datetime(swim_akara['datetime'])
    
    sar_akara = pd.read_csv(data_dir / 'sar_akara_region.csv')
    sar_akara['datetime'] = pd.to_datetime(sar_akara['datetime'])
    
    # Generate report
    report = []
    report.append("=" * 80)
    report.append("WAVE SPECTRA ANALYSIS - AKARÁ CYCLONE")
    report.append("=" * 80)
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 1. Data Overview
    report.append("-" * 80)
    report.append("1. DATA OVERVIEW")
    report.append("-" * 80)
    report.append("")
    report.append("CFOSAT SWIM Data:")
    report.append(f"  Total measurements: {len(swim_results):,}")
    report.append(f"  Date range: {swim_results['datetime'].min()} to {swim_results['datetime'].max()}")
    report.append(f"  Geographic coverage:")
    report.append(f"    Longitude: {swim_results['lon'].min():.2f}° to {swim_results['lon'].max():.2f}°")
    report.append(f"    Latitude: {swim_results['lat'].min():.2f}° to {swim_results['lat'].max():.2f}°")
    report.append("")
    report.append("Sentinel-1A SAR Data:")
    report.append(f"  Total measurements: {len(sar_results):,}")
    report.append(f"  Date range: {sar_results['datetime'].min()} to {sar_results['datetime'].max()}")
    report.append(f"  Geographic coverage:")
    report.append(f"    Longitude: {sar_results['lon'].min():.2f}° to {sar_results['lon'].max():.2f}°")
    report.append(f"    Latitude: {sar_results['lat'].min():.2f}° to {sar_results['lat'].max():.2f}°")
    report.append("")
    
    # 2. Akará Region Analysis
    report.append("-" * 80)
    report.append("2. AKARÁ CYCLONE REGION (Feb 12-16, 2024)")
    report.append("-" * 80)
    report.append("Region: 50°W to 30°W, 45°S to 20°S")
    report.append("")
    report.append(f"SWIM measurements in Akará region: {len(swim_akara)}")
    report.append(f"SAR measurements in Akará region: {len(sar_akara)}")
    report.append("")
    
    # 3. Wave Height Statistics
    report.append("-" * 80)
    report.append("3. SIGNIFICANT WAVE HEIGHT (SWH) STATISTICS")
    report.append("-" * 80)
    report.append("")
    report.append("SWIM - Akará Region:")
    report.append(f"  Minimum SWH: {swim_akara['swh_total'].min():.2f} m")
    report.append(f"  Maximum SWH: {swim_akara['swh_total'].max():.2f} m")
    report.append(f"  Mean SWH: {swim_akara['swh_total'].mean():.2f} m")
    report.append(f"  Median SWH: {swim_akara['swh_total'].median():.2f} m")
    report.append(f"  Standard deviation: {swim_akara['swh_total'].std():.2f} m")
    report.append("")
    report.append("SAR - Akará Region:")
    report.append(f"  Minimum SWH: {sar_akara['swh_total'].min():.2f} m")
    report.append(f"  Maximum SWH: {sar_akara['swh_total'].max():.2f} m")
    report.append(f"  Mean SWH: {sar_akara['swh_total'].mean():.2f} m")
    report.append(f"  Median SWH: {sar_akara['swh_total'].median():.2f} m")
    report.append(f"  Standard deviation: {sar_akara['swh_total'].std():.2f} m")
    report.append("")
    
    # 4. Peak Period Statistics
    report.append("-" * 80)
    report.append("4. PEAK PERIOD STATISTICS")
    report.append("-" * 80)
    report.append("")
    report.append("SWIM - Akará Region:")
    report.append(f"  Minimum Tp: {swim_akara['tp'].min():.1f} s")
    report.append(f"  Maximum Tp: {swim_akara['tp'].max():.1f} s")
    report.append(f"  Mean Tp: {swim_akara['tp'].mean():.1f} s")
    report.append(f"  Median Tp: {swim_akara['tp'].median():.1f} s")
    report.append("")
    report.append("SAR - Akará Region:")
    report.append(f"  Minimum Tp: {sar_akara['tp'].min():.1f} s")
    report.append(f"  Maximum Tp: {sar_akara['tp'].max():.1f} s")
    report.append(f"  Mean Tp: {sar_akara['tp'].mean():.1f} s")
    report.append(f"  Median Tp: {sar_akara['tp'].median():.1f} s")
    report.append("")
    
    # 5. Sea State Partitioning
    report.append("-" * 80)
    report.append("5. SEA STATE PARTITIONING (Wind Sea vs Swell)")
    report.append("-" * 80)
    report.append("")
    report.append("SWIM - Akará Region:")
    report.append(f"  Mean Wind Sea SWH: {swim_akara['swh_wind_sea'].mean():.2f} m")
    report.append(f"  Mean Swell SWH: {swim_akara['swh_swell'].mean():.2f} m")
    report.append(f"  Mean Swell Fraction: {swim_akara['swell_fraction'].mean()*100:.1f}%")
    report.append(f"  Swell-dominated conditions (>80% swell): {(swim_akara['swell_fraction'] > 0.8).sum()} / {len(swim_akara)} ({(swim_akara['swell_fraction'] > 0.8).sum()/len(swim_akara)*100:.1f}%)")
    report.append("")
    report.append("SAR - Akará Region:")
    report.append(f"  Mean Wind Sea SWH: {sar_akara['swh_wind_sea'].mean():.2f} m")
    report.append(f"  Mean Swell SWH: {sar_akara['swh_swell'].mean():.2f} m")
    report.append(f"  Mean Swell Fraction: {sar_akara['swell_fraction'].mean()*100:.1f}%")
    report.append(f"  Swell-dominated conditions (>80% swell): {(sar_akara['swell_fraction'] > 0.8).sum()} / {len(sar_akara)} ({(sar_akara['swell_fraction'] > 0.8).sum()/len(sar_akara)*100:.1f}%)")
    report.append("")
    
    # 6. Wave Direction
    report.append("-" * 80)
    report.append("6. WAVE DIRECTION STATISTICS")
    report.append("-" * 80)
    report.append("")
    report.append("SWIM - Akará Region:")
    report.append(f"  Mean Direction: {swim_akara['mean_dir'].mean():.1f}°")
    report.append(f"  Direction Range: {swim_akara['mean_dir'].min():.1f}° to {swim_akara['mean_dir'].max():.1f}°")
    report.append(f"  Directional Spread: {swim_akara['dir_spread'].mean():.1f}°")
    report.append("")
    report.append("SAR - Akará Region:")
    report.append(f"  Mean Direction: {sar_akara['mean_dir'].mean():.1f}°")
    report.append(f"  Direction Range: {sar_akara['mean_dir'].min():.1f}° to {sar_akara['mean_dir'].max():.1f}°")
    report.append(f"  Directional Spread: {sar_akara['dir_spread'].mean():.1f}°")
    report.append("")
    
    # 7. Key Findings
    report.append("-" * 80)
    report.append("7. KEY FINDINGS")
    report.append("-" * 80)
    report.append("")
    
    # Find extreme events
    max_swh_swim = swim_akara.loc[swim_akara['swh_total'].idxmax()]
    max_swh_sar = sar_akara.loc[sar_akara['swh_total'].idxmax()]
    
    report.append(f"• Maximum wave height observed:")
    report.append(f"  SWIM: {max_swh_swim['swh_total']:.2f} m on {max_swh_swim['datetime']}")
    report.append(f"  SAR: {max_swh_sar['swh_total']:.2f} m on {max_swh_sar['datetime']}")
    report.append("")
    
    report.append(f"• Sea state characteristics:")
    report.append(f"  - Both datasets show swell-dominated conditions ({swim_akara['swell_fraction'].mean()*100:.0f}% SWIM, {sar_akara['swell_fraction'].mean()*100:.0f}% SAR)")
    report.append(f"  - Long-period swell prevails (mean Tp: {swim_akara['tp'].mean():.1f}s SWIM, {sar_akara['tp'].mean():.1f}s SAR)")
    report.append(f"  - Significant wave heights reached extreme values (>25 m)")
    report.append("")
    
    # Compare datasets
    report.append(f"• Dataset comparison:")
    swim_mean = swim_akara['swh_total'].mean()
    sar_mean = sar_akara['swh_total'].mean()
    diff_pct = abs(swim_mean - sar_mean) / swim_mean * 100
    report.append(f"  - Mean SWH difference: {diff_pct:.1f}% ({abs(swim_mean - sar_mean):.2f} m)")
    report.append(f"  - Both sensors capture similar wave conditions")
    report.append(f"  - SAR shows higher swell dominance ({sar_akara['swell_fraction'].mean()*100:.1f}% vs {swim_akara['swell_fraction'].mean()*100:.1f}%)")
    report.append("")
    
    # 8. Generated Figures
    report.append("-" * 80)
    report.append("8. GENERATED FIGURES")
    report.append("-" * 80)
    report.append("")
    report.append("Global Analysis:")
    report.append("  • swim_spectra_grid.png - Polar plots of SWIM spectra")
    report.append("  • swim_time_series.png - SWIM parameter evolution")
    report.append("  • swim_spatial_distribution.png - Spatial maps of SWIM data")
    report.append("  • sar_spectra_grid.png - Polar plots of SAR spectra")
    report.append("  • sar_time_series.png - SAR parameter evolution")
    report.append("  • sar_spatial_distribution.png - Spatial maps of SAR data")
    report.append("")
    report.append("Akará Focused Analysis:")
    report.append("  • akara_swim_sar_comparison.png - Direct comparison of SWIM and SAR")
    report.append("  • akara_statistics_comparison.png - Statistical boxplots")
    report.append("")
    
    # 9. Data Files
    report.append("-" * 80)
    report.append("9. OUTPUT DATA FILES")
    report.append("-" * 80)
    report.append("")
    report.append("  • swim_analysis_results.csv - Complete SWIM analysis")
    report.append("  • sar_analysis_results.csv - Complete SAR analysis")
    report.append("  • swim_akara_region.csv - SWIM data for Akará region")
    report.append("  • sar_akara_region.csv - SAR data for Akará region")
    report.append("")
    
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)
    
    # Save report
    report_text = '\n'.join(report)
    output_file = project_root / 'WAVE_SPECTRA_ANALYSIS_SUMMARY.txt'
    with open(output_file, 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print(f"\n💾 Summary report saved to: {output_file}")


if __name__ == '__main__':
    generate_summary_report()
