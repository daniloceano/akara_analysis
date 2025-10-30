# Wave Spectra Analysis - Akará Cyclone

This directory contains scripts for analyzing directional wave spectra data from CFOSAT SWIM and Sentinel-1A SAR during the Akará cyclone event (February 12-16, 2024).

## Overview

The wave spectra analysis enhances the understanding of sea state components during the Akará cyclone by:
- Parsing directional wave spectra from satellite measurements
- Computing integrated wave parameters (SWH, peak period, direction)
- Partitioning the wave field into wind sea and swell components
- Visualizing spectral evolution and spatial patterns
- Comparing SWIM and SAR observations

## Data Sources

### CFOSAT SWIM
- **File**: `data/wave_spectra/SWI_WV1`
- **Coverage**: Global, 35,672 spectra
- **Period**: Feb 12-16, 2024
- **Format**: Header + 30 frequencies × 24 directions matrix

### Sentinel-1A SAR
- **Directory**: `data/wave_spectra/SENT1/`
- **Coverage**: Global, 6,080 spectra in 29 files
- **Period**: Feb 12-16, 2024
- **Format**: Similar to SWIM with additional parameters

## Scripts

### 1. `parse_wave_spectra.py`
Parses wave spectra files into structured data.

**Classes**:
- `SwimSpectraParser`: Parse CFOSAT SWIM data
- `SarSpectraParser`: Parse Sentinel-1A SAR data

**Features**:
- Reads header information (datetime, location, parameters)
- Extracts 30×24 spectral matrices
- Builds frequency array: f(1)=0.0345 Hz, f(i) = 1.1 × f(i-1)
- Builds direction array: 7.5° to 352.5° in 15° steps
- Converts to pandas DataFrame or xarray Dataset

**Usage**:
```bash
python scripts/parse_wave_spectra.py
```

### 2. `analyze_wave_spectra.py`
Computes integrated wave parameters from spectra.

**Class**: `SpectraAnalyzer`

**Computed Parameters**:
- **SWH (Significant Wave Height)**: 4√m₀, where m₀ is the zeroth moment
- **Tp (Peak Period)**: 1/fp, where fp is the peak frequency
- **Mean Direction**: Circular mean of directional spectrum
- **Directional Spread**: Circular variance of directions
- **Wind Sea/Swell Partition**: Based on 0.13 Hz threshold (≈7.7s period)

**Important**: 
- All longitude values are automatically converted from 0-360° to -180-180° format
- This ensures proper regional filtering and compatibility with standard mapping conventions

**Usage**:
```bash
python scripts/analyze_wave_spectra.py
```

**Outputs**:
- `data/swim_analysis_results.csv`
- `data/sar_analysis_results.csv`

### 3. `visualize_wave_spectra.py`
Creates comprehensive visualizations of wave spectra.

**Visualizations**:
1. **Polar Spectral Plots**: Frequency-direction energy distribution
2. **Time Series**: Evolution of SWH, Tp, direction, spread, swell fraction
3. **Spatial Distribution**: Maps of wave parameters

**Usage**:
```bash
python scripts/visualize_wave_spectra.py
```

**Outputs** (in `figures/`):
- `swim_spectra_grid.png` - 3×3 grid of SWIM polar spectra
- `swim_time_series.png` - Time evolution of SWIM parameters
- `swim_spatial_distribution.png` - Spatial maps of SWIM data
- `sar_spectra_grid.png` - 3×3 grid of SAR polar spectra
- `sar_time_series.png` - Time evolution of SAR parameters
- `sar_spatial_distribution.png` - Spatial maps of SAR data

### 4. `analyze_akara_spectra.py`
Focused analysis for the Akará cyclone region.

**Region**: 50°W to 30°W, 45°S to 20°S
**Period**: Feb 12-16, 2024

**Features**:
- Filters global data for Akará region
- Compares SWIM and SAR measurements
- Statistical analysis of regional data
- Side-by-side comparison plots

**Usage**:
```bash
python scripts/analyze_akara_spectra.py
```

**Outputs**:
- `data/swim_akara_region.csv` - SWIM data for Akará (418 measurements)
- `data/sar_akara_region.csv` - SAR data for Akará (95 measurements)
- `figures/akara_swim_sar_comparison.png` - Time series comparison
- `figures/akara_statistics_comparison.png` - Statistical boxplots

### 5. `generate_spectra_summary.py`
Generates comprehensive text summary report.

**Usage**:
```bash
python scripts/generate_spectra_summary.py
```

**Output**: `WAVE_SPECTRA_ANALYSIS_SUMMARY.txt`

## Key Findings

### Akará Region Statistics

**SWIM Data (418 measurements)**:
- SWH range: 4.27 - 28.08 m
- Mean SWH: 10.42 m
- Peak period: 5.7 - 18.0 s (mean: 12.9 s)
- Swell fraction: 85.8% (swell-dominated)

**SAR Data (95 measurements)**:
- SWH range: 0.73 - 25.06 m
- Mean SWH: 9.55 m
- Peak period: 7.6 - 16.4 s (mean: 12.7 s)
- Swell fraction: 96.1% (highly swell-dominated)

### Extreme Events
- **Maximum SWH**: 28.08 m (SWIM, Feb 14 09:24)
- **Maximum SWH**: 25.06 m (SAR, Feb 15 07:30)

### Sea State Characteristics
- Both datasets show **swell-dominated conditions** (86% SWIM, 96% SAR)
- **Long-period swell** prevails (mean Tp ≈ 12.8 s)
- Significant wave heights reached **extreme values** (>25 m)
- Mean SWH difference between datasets: **8.4%** (0.87 m)

## Workflow

Complete analysis workflow:

```bash
# 1. Parse wave spectra data
python scripts/parse_wave_spectra.py

# 2. Compute wave parameters
python scripts/analyze_wave_spectra.py

# 3. Create visualizations
python scripts/visualize_wave_spectra.py

# 4. Focused Akará analysis
python scripts/analyze_akara_spectra.py

# 5. Generate summary report
python scripts/generate_spectra_summary.py
```

## Output Structure

```
data/
  wave_spectra/
    SWI_WV1                          # SWIM raw data
    SENT1/                           # SAR raw data (29 files)
  swim_analysis_results.csv          # Global SWIM analysis
  sar_analysis_results.csv           # Global SAR analysis
  swim_akara_region.csv              # SWIM Akará region
  sar_akara_region.csv               # SAR Akará region

figures/
  swim_spectra_grid.png              # SWIM polar plots
  swim_time_series.png               # SWIM time series
  swim_spatial_distribution.png      # SWIM spatial maps
  sar_spectra_grid.png               # SAR polar plots
  sar_time_series.png                # SAR time series
  sar_spatial_distribution.png       # SAR spatial maps
  akara_swim_sar_comparison.png      # Akará comparison
  akara_statistics_comparison.png    # Akará statistics

WAVE_SPECTRA_ANALYSIS_SUMMARY.txt    # Summary report
```

## Technical Details

### Spectral Format
- **Frequencies**: 30 bins, geometric progression
  - f(1) = 0.0345 Hz
  - f(i) = 1.1 × f(i-1)
  - Range: ~0.034 to ~0.75 Hz (periods: ~1.3 to ~29 s)

- **Directions**: 24 bins
  - 7.5° to 352.5° in 15° steps
  - Oceanographic convention (direction from which waves travel)

### Wave Partitioning
- **Threshold**: 0.13 Hz (≈7.7 s period)
- **Wind sea**: f > 0.13 Hz (shorter periods)
- **Swell**: f < 0.13 Hz (longer periods)

### Coordinate Systems
- **Longitude**: Automatically converted from 0-360° to -180-180° during analysis
  - Input data: 0° to 360° (from raw satellite files)
  - Output data: -180° to 180° (in all CSV files and visualizations)
  - Conversion: lon = lon - 360 if lon > 180
- **Latitude**: -90° to 90°
- **Direction**: 0° (from North) clockwise to 360° (oceanographic convention)

## Dependencies

All required packages are in the `akara` conda environment:
- numpy
- pandas
- matplotlib
- cartopy
- xarray

## Notes

- All scripts use English for text outputs
- Turbo colormap for wave height visualization
- All dates in UTC
- Analysis scripts are modular and can be run independently after parsing

## References

- CFOSAT SWIM: Wave spectrometer for ocean monitoring
- Sentinel-1A: SAR-derived wave spectra
- Akará Cyclone: South Atlantic subtropical cyclone, Feb 12-16, 2024
