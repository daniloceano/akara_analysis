"""
Parse wave spectra data from CFOSAT SWIM and Sentinel-1A SAR.

This module provides functions to read and parse directional wave spectra
from different satellite sources during the Akará cyclone event.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import xarray as xr


class SwimSpectraParser:
    """Parser for CFOSAT SWIM wave spectra data."""
    
    def __init__(self, filepath: str):
        """
        Initialize SWIM spectra parser.
        
        Args:
            filepath: Path to SWI_WV1 file
        """
        self.filepath = Path(filepath)
        self.n_frequencies = 30
        self.n_directions = 24
        
        # Frequency array: f(1) = 0.0345 Hz, f(i) = 1.1 * f(i-1)
        self.frequencies = np.array([0.0345 * (1.1 ** i) for i in range(self.n_frequencies)])
        
        # Direction array: 7.5° to 352.5° in 15° steps
        self.directions = np.arange(7.5, 360, 15)
        
    def parse_file(self) -> List[Dict]:
        """
        Parse all spectra from SWIM file.
        
        Returns:
            List of dictionaries, each containing:
                - datetime: pandas Timestamp
                - lon: longitude
                - lat: latitude
                - param1, param2: additional parameters
                - spectrum: 2D array (frequencies x directions)
        """
        spectra = []
        
        with open(self.filepath, 'r') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is a header line (starts with timestamp)
            if line and line[0].isdigit() and len(line.split()) >= 5:
                parts = line.split()
                
                # Parse header
                timestamp = datetime.strptime(parts[0], '%Y%m%d%H%M')
                lon = float(parts[1])
                lat = float(parts[2])
                param1 = float(parts[3])
                param2 = float(parts[4])
                
                # Read next 30 lines for spectrum matrix
                spectrum_data = []
                for j in range(1, self.n_frequencies + 1):
                    if i + j < len(lines):
                        row = [float(x) for x in lines[i + j].split()]
                        # Handle cases where row might have more/less than 24 values
                        if len(row) >= self.n_directions:
                            spectrum_data.append(row[:self.n_directions])
                        else:
                            # Pad with zeros if needed
                            spectrum_data.append(row + [0.0] * (self.n_directions - len(row)))
                
                if len(spectrum_data) == self.n_frequencies:
                    spectrum = np.array(spectrum_data)
                    
                    spectra.append({
                        'datetime': pd.Timestamp(timestamp),
                        'lon': lon,
                        'lat': lat,
                        'param1': param1,
                        'param2': param2,
                        'spectrum': spectrum
                    })
                
                # Move to next potential header
                i += self.n_frequencies + 1
            else:
                i += 1
        
        print(f"✅ Parsed {len(spectra)} SWIM spectra from {self.filepath.name}")
        return spectra
    
    def to_dataframe(self, spectra: List[Dict]) -> pd.DataFrame:
        """
        Convert parsed spectra to DataFrame (without spectrum matrix).
        
        Args:
            spectra: List of parsed spectra dictionaries
            
        Returns:
            DataFrame with metadata for each spectrum
        """
        df = pd.DataFrame([
            {
                'datetime': s['datetime'],
                'lon': s['lon'],
                'lat': s['lat'],
                'param1': s['param1'],
                'param2': s['param2']
            }
            for s in spectra
        ])
        return df
    
    def to_xarray(self, spectra: List[Dict]) -> xr.Dataset:
        """
        Convert parsed spectra to xarray Dataset.
        
        Args:
            spectra: List of parsed spectra dictionaries
            
        Returns:
            xarray Dataset with dimensions (time, frequency, direction)
        """
        times = [s['datetime'] for s in spectra]
        lons = [s['lon'] for s in spectra]
        lats = [s['lat'] for s in spectra]
        param1s = [s['param1'] for s in spectra]
        param2s = [s['param2'] for s in spectra]
        
        # Stack all spectra
        spectra_array = np.stack([s['spectrum'] for s in spectra])
        
        ds = xr.Dataset({
            'spectrum': (['time', 'frequency', 'direction'], spectra_array),
            'lon': (['time'], lons),
            'lat': (['time'], lats),
            'param1': (['time'], param1s),
            'param2': (['time'], param2s),
        }, coords={
            'time': times,
            'frequency': self.frequencies,
            'direction': self.directions
        })
        
        # Add attributes
        ds['spectrum'].attrs = {
            'long_name': 'Wave Energy Spectrum',
            'units': 'm²/Hz/deg'
        }
        ds['frequency'].attrs = {
            'long_name': 'Wave Frequency',
            'units': 'Hz'
        }
        ds['direction'].attrs = {
            'long_name': 'Wave Direction',
            'units': 'degrees'
        }
        
        return ds


class SarSpectraParser:
    """Parser for Sentinel-1A SAR wave spectra data."""
    
    def __init__(self, directory: str):
        """
        Initialize SAR spectra parser.
        
        Args:
            directory: Path to SENT1 directory containing SAR files
        """
        self.directory = Path(directory)
        self.n_frequencies = 30
        self.n_directions = 24
        
        # Same frequency/direction arrays as SWIM
        self.frequencies = np.array([0.0345 * (1.1 ** i) for i in range(self.n_frequencies)])
        self.directions = np.arange(7.5, 360, 15)
    
    def parse_file(self, filepath: Path) -> List[Dict]:
        """
        Parse spectra from a single SAR file.
        
        Args:
            filepath: Path to SAR file
            
        Returns:
            List of dictionaries with parsed spectra
        """
        spectra = []
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this is a header line (timestamp at start)
            parts = line.split()
            if len(parts) >= 8 and parts[0].isdigit():
                # Parse header
                timestamp = datetime.strptime(parts[0], '%Y%m%d%H%M')
                lon = float(parts[1])
                lat = float(parts[2])
                # Additional parameters
                params = [float(p) for p in parts[3:8]] if len(parts) >= 8 else []
                
                # Read next 30 lines for spectrum matrix
                spectrum_data = []
                for j in range(1, self.n_frequencies + 1):
                    if i + j < len(lines):
                        row_values = []
                        row_line = lines[i + j].strip()
                        # Handle potential inline headers in the matrix
                        for val in row_line.split():
                            try:
                                row_values.append(float(val))
                            except ValueError:
                                break
                        
                        if len(row_values) >= self.n_directions:
                            spectrum_data.append(row_values[:self.n_directions])
                        elif len(row_values) > 0:
                            # Pad with zeros
                            spectrum_data.append(row_values + [0.0] * (self.n_directions - len(row_values)))
                
                if len(spectrum_data) == self.n_frequencies:
                    spectrum = np.array(spectrum_data)
                    
                    spectra.append({
                        'datetime': pd.Timestamp(timestamp),
                        'lon': lon,
                        'lat': lat,
                        'params': params,
                        'spectrum': spectrum
                    })
                
                # Move to next potential header
                i += self.n_frequencies + 1
            else:
                i += 1
        
        return spectra
    
    def parse_all_files(self) -> List[Dict]:
        """
        Parse all SAR files in directory.
        
        Returns:
            List of all parsed spectra from all files
        """
        all_spectra = []
        
        sar_files = sorted(self.directory.glob('SAR*'))
        
        for sar_file in sar_files:
            spectra = self.parse_file(sar_file)
            all_spectra.extend(spectra)
        
        print(f"✅ Parsed {len(all_spectra)} SAR spectra from {len(sar_files)} files")
        return all_spectra
    
    def to_dataframe(self, spectra: List[Dict]) -> pd.DataFrame:
        """
        Convert parsed spectra to DataFrame (without spectrum matrix).
        
        Args:
            spectra: List of parsed spectra dictionaries
            
        Returns:
            DataFrame with metadata for each spectrum
        """
        df = pd.DataFrame([
            {
                'datetime': s['datetime'],
                'lon': s['lon'],
                'lat': s['lat'],
                **{f'param{i+1}': p for i, p in enumerate(s.get('params', []))}
            }
            for s in spectra
        ])
        return df
    
    def to_xarray(self, spectra: List[Dict]) -> xr.Dataset:
        """
        Convert parsed spectra to xarray Dataset.
        
        Args:
            spectra: List of parsed spectra dictionaries
            
        Returns:
            xarray Dataset with dimensions (time, frequency, direction)
        """
        times = [s['datetime'] for s in spectra]
        lons = [s['lon'] for s in spectra]
        lats = [s['lat'] for s in spectra]
        
        # Stack all spectra
        spectra_array = np.stack([s['spectrum'] for s in spectra])
        
        ds = xr.Dataset({
            'spectrum': (['time', 'frequency', 'direction'], spectra_array),
            'lon': (['time'], lons),
            'lat': (['time'], lats),
        }, coords={
            'time': times,
            'frequency': self.frequencies,
            'direction': self.directions
        })
        
        # Add attributes
        ds['spectrum'].attrs = {
            'long_name': 'Wave Energy Spectrum',
            'units': 'm²/Hz/deg'
        }
        ds['frequency'].attrs = {
            'long_name': 'Wave Frequency',
            'units': 'Hz'
        }
        ds['direction'].attrs = {
            'long_name': 'Wave Direction',
            'units': 'degrees'
        }
        
        return ds


def main():
    """Test the parsers."""
    import sys
    from pathlib import Path
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Parse SWIM data
    print("\n" + "="*60)
    print("PARSING CFOSAT SWIM DATA")
    print("="*60)
    
    swim_file = project_root / 'data' / 'wave_spectra' / 'SWI_WV1'
    swim_parser = SwimSpectraParser(swim_file)
    swim_spectra = swim_parser.parse_file()
    
    if swim_spectra:
        swim_df = swim_parser.to_dataframe(swim_spectra)
        print(f"\n📊 SWIM DataFrame shape: {swim_df.shape}")
        print(f"📅 Date range: {swim_df['datetime'].min()} to {swim_df['datetime'].max()}")
        print(f"🌍 Location range:")
        print(f"   Lon: {swim_df['lon'].min():.2f} to {swim_df['lon'].max():.2f}")
        print(f"   Lat: {swim_df['lat'].min():.2f} to {swim_df['lat'].max():.2f}")
        print("\nFirst few records:")
        print(swim_df.head())
    
    # Parse SAR data
    print("\n" + "="*60)
    print("PARSING SENTINEL-1A SAR DATA")
    print("="*60)
    
    sar_dir = project_root / 'data' / 'wave_spectra' / 'SENT1'
    sar_parser = SarSpectraParser(sar_dir)
    sar_spectra = sar_parser.parse_all_files()
    
    if sar_spectra:
        sar_df = sar_parser.to_dataframe(sar_spectra)
        print(f"\n📊 SAR DataFrame shape: {sar_df.shape}")
        print(f"📅 Date range: {sar_df['datetime'].min()} to {sar_df['datetime'].max()}")
        print(f"🌍 Location range:")
        print(f"   Lon: {sar_df['lon'].min():.2f} to {sar_df['lon'].max():.2f}")
        print(f"   Lat: {sar_df['lat'].min():.2f} to {sar_df['lat'].max():.2f}")
        print("\nFirst few records:")
        print(sar_df.head())


if __name__ == '__main__':
    main()
