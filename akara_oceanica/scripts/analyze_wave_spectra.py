"""
Analyze wave spectra to compute integrated parameters and partition sea states.

This module provides functions to:
- Compute integrated wave parameters (SWH, Tp, mean direction, spread)
- Partition spectra into wind sea and swell components
- Analyze spectral evolution during Akará cyclone
"""

import numpy as np
import pandas as pd
import xarray as xr
from typing import Dict, Tuple, List


class SpectraAnalyzer:
    """Analyze directional wave spectra."""
    
    def __init__(self, frequencies: np.ndarray, directions: np.ndarray):
        """
        Initialize spectra analyzer.
        
        Args:
            frequencies: Array of frequencies (Hz)
            directions: Array of directions (degrees)
        """
        self.frequencies = frequencies
        self.directions = directions
        self.df = np.diff(frequencies)[0] if len(frequencies) > 1 else 0.01  # Approximate frequency step
        self.dtheta = np.diff(directions)[0] if len(directions) > 1 else 15.0  # Direction step in degrees
        
    def compute_swh(self, spectrum: np.ndarray) -> float:
        """
        Compute Significant Wave Height (SWH) from spectrum.
        
        SWH = 4 * sqrt(m0)
        where m0 is the zeroth moment (total energy)
        
        Args:
            spectrum: 2D array (frequency x direction) in m²/Hz/deg
            
        Returns:
            Significant wave height in meters
        """
        # Integrate over directions and frequencies
        # spectrum is in m²/Hz/deg, need to integrate
        m0 = np.sum(spectrum) * self.df * self.dtheta
        swh = 4.0 * np.sqrt(m0)
        return swh
    
    def compute_peak_period(self, spectrum: np.ndarray) -> float:
        """
        Compute peak period (Tp) from spectrum.
        
        Tp = 1 / fp, where fp is the frequency with maximum energy
        
        Args:
            spectrum: 2D array (frequency x direction)
            
        Returns:
            Peak period in seconds
        """
        # Integrate over directions to get frequency spectrum
        freq_spectrum = np.sum(spectrum, axis=1) * self.dtheta
        
        # Find peak frequency
        peak_idx = np.argmax(freq_spectrum)
        fp = self.frequencies[peak_idx]
        
        if fp > 0:
            tp = 1.0 / fp
        else:
            tp = 0.0
        
        return tp
    
    def compute_mean_direction(self, spectrum: np.ndarray) -> float:
        """
        Compute mean wave direction.
        
        Args:
            spectrum: 2D array (frequency x direction)
            
        Returns:
            Mean direction in degrees (0-360)
        """
        # Convert directions to radians
        theta_rad = np.deg2rad(self.directions)
        
        # Compute total energy per direction
        dir_spectrum = np.sum(spectrum, axis=0) * self.df
        
        # Compute mean direction using circular statistics
        sin_sum = np.sum(dir_spectrum * np.sin(theta_rad))
        cos_sum = np.sum(dir_spectrum * np.cos(theta_rad))
        
        mean_dir_rad = np.arctan2(sin_sum, cos_sum)
        mean_dir = np.rad2deg(mean_dir_rad)
        
        # Ensure 0-360 range
        if mean_dir < 0:
            mean_dir += 360
        
        return mean_dir
    
    def compute_directional_spread(self, spectrum: np.ndarray) -> float:
        """
        Compute directional spreading.
        
        Args:
            spectrum: 2D array (frequency x direction)
            
        Returns:
            Directional spread in degrees
        """
        # Convert directions to radians
        theta_rad = np.deg2rad(self.directions)
        
        # Compute total energy per direction
        dir_spectrum = np.sum(spectrum, axis=0) * self.df
        total_energy = np.sum(dir_spectrum)
        
        if total_energy == 0:
            return 0.0
        
        # Compute mean direction
        mean_dir = self.compute_mean_direction(spectrum)
        mean_dir_rad = np.deg2rad(mean_dir)
        
        # Compute circular variance
        r = np.sqrt(
            (np.sum(dir_spectrum * np.cos(theta_rad)) / total_energy) ** 2 +
            (np.sum(dir_spectrum * np.sin(theta_rad)) / total_energy) ** 2
        )
        
        # Directional spread
        spread_rad = np.sqrt(2 * (1 - r))
        spread = np.rad2deg(spread_rad)
        
        return spread
    
    def compute_all_parameters(self, spectrum: np.ndarray) -> Dict:
        """
        Compute all integrated wave parameters.
        
        Args:
            spectrum: 2D array (frequency x direction)
            
        Returns:
            Dictionary with all parameters
        """
        return {
            'swh': self.compute_swh(spectrum),
            'tp': self.compute_peak_period(spectrum),
            'mean_dir': self.compute_mean_direction(spectrum),
            'dir_spread': self.compute_directional_spread(spectrum)
        }
    
    def partition_spectrum(self, spectrum: np.ndarray, 
                          wind_sea_threshold: float = 0.13) -> Tuple[np.ndarray, np.ndarray]:
        """
        Partition spectrum into wind sea and swell components.
        
        Simple partitioning based on frequency threshold:
        - Wind sea: f > 0.13 Hz (T < ~7.7 s)
        - Swell: f < 0.13 Hz (T > ~7.7 s)
        
        Args:
            spectrum: 2D array (frequency x direction)
            wind_sea_threshold: Frequency threshold (Hz) separating wind sea from swell
            
        Returns:
            Tuple of (wind_sea_spectrum, swell_spectrum)
        """
        # Find threshold index
        threshold_idx = np.argmin(np.abs(self.frequencies - wind_sea_threshold))
        
        # Create partitioned spectra
        swell_spectrum = spectrum.copy()
        wind_sea_spectrum = spectrum.copy()
        
        # Zero out appropriate parts
        swell_spectrum[threshold_idx:, :] = 0.0
        wind_sea_spectrum[:threshold_idx, :] = 0.0
        
        return wind_sea_spectrum, swell_spectrum
    
    def analyze_dataset(self, ds: xr.Dataset) -> pd.DataFrame:
        """
        Analyze full dataset of spectra.
        
        Args:
            ds: xarray Dataset with 'spectrum' variable (time, frequency, direction)
            
        Returns:
            DataFrame with computed parameters for each spectrum
        """
        results = []
        
        for i, time in enumerate(ds.time.values):
            spectrum = ds.spectrum.isel(time=i).values
            
            # Compute integrated parameters
            params = self.compute_all_parameters(spectrum)
            
            # Partition spectrum
            wind_sea, swell = self.partition_spectrum(spectrum)
            
            # Compute parameters for partitions
            wind_sea_swh = self.compute_swh(wind_sea)
            swell_swh = self.compute_swh(swell)
            
            # Convert longitude to -180 to 180 format
            lon = float(ds.lon.isel(time=i).values)
            if lon > 180:
                lon = lon - 360
            
            results.append({
                'datetime': pd.Timestamp(time),
                'lon': lon,
                'lat': float(ds.lat.isel(time=i).values),
                'swh_total': params['swh'],
                'tp': params['tp'],
                'mean_dir': params['mean_dir'],
                'dir_spread': params['dir_spread'],
                'swh_wind_sea': wind_sea_swh,
                'swh_swell': swell_swh,
                'swell_fraction': swell_swh / params['swh'] if params['swh'] > 0 else 0.0
            })
        
        return pd.DataFrame(results)


def analyze_swim_data(swim_spectra: List[Dict]) -> pd.DataFrame:
    """
    Analyze SWIM spectra.
    
    Args:
        swim_spectra: List of parsed SWIM spectra
        
    Returns:
        DataFrame with analyzed parameters
    """
    # Create analyzer
    frequencies = np.array([0.0345 * (1.1 ** i) for i in range(30)])
    directions = np.arange(7.5, 360, 15)
    analyzer = SpectraAnalyzer(frequencies, directions)
    
    results = []
    
    for spec in swim_spectra:
        spectrum = spec['spectrum']
        params = analyzer.compute_all_parameters(spectrum)
        
        # Partition
        wind_sea, swell = analyzer.partition_spectrum(spectrum)
        wind_sea_swh = analyzer.compute_swh(wind_sea)
        swell_swh = analyzer.compute_swh(swell)
        
        # Convert longitude to -180 to 180 format
        lon = spec['lon']
        if lon > 180:
            lon = lon - 360
        
        results.append({
            'datetime': spec['datetime'],
            'lon': lon,
            'lat': spec['lat'],
            'swh_total': params['swh'],
            'tp': params['tp'],
            'mean_dir': params['mean_dir'],
            'dir_spread': params['dir_spread'],
            'swh_wind_sea': wind_sea_swh,
            'swh_swell': swell_swh,
            'swell_fraction': swell_swh / params['swh'] if params['swh'] > 0 else 0.0
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    return df


def analyze_sar_data(sar_spectra: List[Dict]) -> pd.DataFrame:
    """
    Analyze SAR spectra.
    
    Args:
        sar_spectra: List of parsed SAR spectra
        
    Returns:
        DataFrame with analyzed parameters
    """
    # Create analyzer
    frequencies = np.array([0.0345 * (1.1 ** i) for i in range(30)])
    directions = np.arange(7.5, 360, 15)
    analyzer = SpectraAnalyzer(frequencies, directions)
    
    results = []
    
    for spec in sar_spectra:
        spectrum = spec['spectrum']
        params = analyzer.compute_all_parameters(spectrum)
        
        # Partition
        wind_sea, swell = analyzer.partition_spectrum(spectrum)
        wind_sea_swh = analyzer.compute_swh(wind_sea)
        swell_swh = analyzer.compute_swh(swell)
        
        # Convert longitude to -180 to 180 format
        lon = spec['lon']
        if lon > 180:
            lon = lon - 360
        
        results.append({
            'datetime': spec['datetime'],
            'lon': lon,
            'lat': spec['lat'],
            'swh_total': params['swh'],
            'tp': params['tp'],
            'mean_dir': params['mean_dir'],
            'dir_spread': params['dir_spread'],
            'swh_wind_sea': wind_sea_swh,
            'swh_swell': swell_swh,
            'swell_fraction': swell_swh / params['swh'] if params['swh'] > 0 else 0.0
        })
    
    df = pd.DataFrame(results)
    df = df.sort_values('datetime').reset_index(drop=True)
    
    return df


def main():
    """Test the analyzer."""
    from pathlib import Path
    import sys
    
    # Add parent directory to path for imports
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Try different import methods
    try:
        from scripts.analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser
    except ModuleNotFoundError:
        try:
            from analysis_parse_wave_spectra import SwimSpectraParser, SarSpectraParser
        except ModuleNotFoundError:
            # If running from scripts directory
            import analysis_parse_wave_spectra
            SwimSpectraParser = analysis_parse_wave_spectra.SwimSpectraParser
            SarSpectraParser = analysis_parse_wave_spectra.SarSpectraParser
    
    # Parse and analyze SWIM data
    print("\n" + "="*60)
    print("ANALYZING CFOSAT SWIM DATA")
    print("="*60)
    
    swim_file = project_root / 'data' / 'wave_spectra' / 'SWI_WV1'
    swim_parser = SwimSpectraParser(swim_file)
    swim_spectra = swim_parser.parse_file()
    
    swim_results = analyze_swim_data(swim_spectra)
    print(f"\n📊 SWIM Analysis Results:")
    print(f"Number of spectra: {len(swim_results)}")
    print("\nStatistics:")
    print(swim_results[['swh_total', 'tp', 'mean_dir', 'swh_wind_sea', 'swh_swell', 'swell_fraction']].describe())
    
    # Save results
    output_file = project_root / 'data' / 'swim_analysis_results.csv'
    swim_results.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    # Parse and analyze SAR data
    print("\n" + "="*60)
    print("ANALYZING SENTINEL-1A SAR DATA")
    print("="*60)
    
    sar_dir = project_root / 'data' / 'wave_spectra' / 'SENT1'
    sar_parser = SarSpectraParser(sar_dir)
    sar_spectra = sar_parser.parse_all_files()
    
    sar_results = analyze_sar_data(sar_spectra)
    print(f"\n📊 SAR Analysis Results:")
    print(f"Number of spectra: {len(sar_results)}")
    print("\nStatistics:")
    print(sar_results[['swh_total', 'tp', 'mean_dir', 'swh_wind_sea', 'swh_swell', 'swell_fraction']].describe())
    
    # Save results
    output_file = project_root / 'data' / 'sar_analysis_results.csv'
    sar_results.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == '__main__':
    main()
