#!/usr/bin/env python3
"""
Download SWOT WindWave data with progress tracking
"""

import subprocess
import sys
import time
import os
from pathlib import Path
from datetime import datetime
import requests

class SWOTWindWaveDownloader:
    def __init__(self):
        self.base_dir = Path("/Users/danilocoutodesouza/Documents/Programs_and_scripts/akara_analysis/SWOT")
        self.output_dir = self.base_dir / "data" / "raw" / "SWOT_L2_LR_SSH_WINDWAVE_2.0"
        self.collection = "SWOT_L2_LR_SSH_WINDWAVE_2.0"
        self.bbox = "-50.0,-45.0,-20.0,-15.0"  # Região Akará
        self.start_date = "2024-02-14T00:00:00Z"
        self.end_date = "2024-02-22T23:59:59Z"
        
    def estimate_total_files(self):
        """
        Estimate total number of expected files based on SWOT Basic data
        """
        basic_dir = self.base_dir / "data" / "raw" / "SWOT_L2_LR_SSH_Basic_2.0"
        
        if basic_dir.exists():
            basic_files = list(basic_dir.glob("*.nc"))
            estimated_total = len(basic_files)
            print(f"📊 Estimativa baseada em dados Basic: ~{estimated_total} arquivos")
            return estimated_total
        else:
            # Fallback estimate for 8 days of SWOT data
            # SWOT has ~3-4 passes per day in our region
            estimated_total = 8 * 4  # 32 files approximately
            print(f"📊 Estimativa para período: ~{estimated_total} arquivos")
            return estimated_total
    
    def check_current_status(self):
        """
        Check what files are already downloaded
        """
        print("🔍 VERIFICANDO STATUS ATUAL")
        print("-" * 50)
        
        if not self.output_dir.exists():
            print("📁 Diretório ainda não existe - primeiro download")
            return [], 0
            
        downloaded_files = list(self.output_dir.glob("*.nc"))
        downloaded_count = len(downloaded_files)
        
        if downloaded_count == 0:
            print("📁 Diretório existe mas vazio")
            return [], 0
            
        print(f"✅ {downloaded_count} arquivos já baixados")
        
        # Check file sizes to ensure they're complete
        incomplete_files = []
        total_size = 0
        
        for file in downloaded_files:
            file_size = file.stat().st_size
            total_size += file_size
            
            # Files smaller than 1MB are probably incomplete
            if file_size < 1024 * 1024:  # 1MB
                incomplete_files.append(file)
                
        if incomplete_files:
            print(f"⚠️ {len(incomplete_files)} arquivos podem estar incompletos (< 1MB)")
            for file in incomplete_files[:3]:
                size_mb = file.stat().st_size / (1024*1024)
                print(f"   {file.name}: {size_mb:.2f} MB")
        
        total_size_gb = total_size / (1024**3)
        avg_size_mb = (total_size / downloaded_count) / (1024**2) if downloaded_count > 0 else 0
        
        print(f"📊 Tamanho total: {total_size_gb:.2f} GB")
        print(f"📊 Tamanho médio: {avg_size_mb:.1f} MB por arquivo")
        
        # Show date range of downloaded files
        if downloaded_files:
            # Extract dates from filenames
            dates = []
            for file in downloaded_files:
                try:
                    # Format: SWOT_L2_LR_SSH_WindWave_XXX_XXX_YYYYMMDDTHHMMSS_...
                    parts = file.name.split('_')
                    if len(parts) >= 6:
                        date_str = parts[5]  # YYYYMMDDTHHMMSS
                        date_part = date_str[:8]  # YYYYMMDD
                        if len(date_part) == 8:
                            date_obj = datetime.strptime(date_part, '%Y%m%d')
                            dates.append(date_obj)
                except:
                    continue
                    
            if dates:
                dates.sort()
                print(f"📅 Período baixado: {dates[0].strftime('%Y-%m-%d')} a {dates[-1].strftime('%Y-%m-%d')}")
                
                # Count files per day
                dates_str = [d.strftime('%Y-%m-%d') for d in dates]
                from collections import Counter
                daily_counts = Counter(dates_str)
                
                print("📊 Arquivos por dia:")
                for date_str, count in sorted(daily_counts.items()):
                    print(f"   {date_str}: {count} arquivos")
        
        return downloaded_files, downloaded_count
    
    def run_download_with_progress(self):
        """
        Run download with progress monitoring
        """
        print("🌊 INICIANDO DOWNLOAD SWOT WINDWAVE")
        print("=" * 60)
        
        # Check current status
        downloaded_files, current_count = self.check_current_status()
        estimated_total = self.estimate_total_files()
        
        if current_count > 0:
            print(f"\\n📈 Progresso atual: {current_count}/{estimated_total} arquivos ({100*current_count/estimated_total:.1f}%)")
            
            if current_count >= estimated_total:
                print("✅ Download parece estar completo!")
                print("🔄 Executando novamente para verificar atualizações...")
            else:
                remaining = estimated_total - current_count
                print(f"⏳ Estimativa de arquivos restantes: {remaining}")
        
        # Prepare command
        cmd = [
            "podaac-data-subscriber",
            "-c", self.collection,
            "-d", str(self.output_dir),
            "--start-date", self.start_date,
            "--end-date", self.end_date,
            "-b", self.bbox,
            "-f"  # Force download
        ]
        
        print(f"\\n🚀 Comando de download:")
        print(f"   {' '.join(cmd)}")
        print()
        
        # Show what will be downloaded
        print("📋 Parâmetros:")
        print(f"   Coleção: {self.collection}")
        print(f"   Período: {self.start_date} a {self.end_date}")
        print(f"   Região: {self.bbox}")
        print(f"   Destino: {self.output_dir}")
        print()
        
        # Start download
        print("⬇️ Iniciando download...")
        print("💡 Pressione Ctrl+C para interromper")
        print("-" * 60)
        
        start_time = time.time()
        
        try:
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor progress
            self.monitor_download_progress(process, start_time, current_count, estimated_total)
            
            # Wait for completion
            return_code = process.wait()
            
            if return_code == 0:
                self.show_final_status(start_time, current_count)
                return True
            else:
                print(f"\\n❌ Download terminou com erro (código: {return_code})")
                return False
                
        except KeyboardInterrupt:
            print("\\n⏹️ Download interrompido pelo usuário")
            process.terminate()
            return False
        except Exception as e:
            print(f"\\n❌ Erro durante download: {e}")
            return False
    
    def monitor_download_progress(self, process, start_time, initial_count, estimated_total):
        """
        Monitor download progress in real-time
        """
        last_count = initial_count
        last_check = time.time()
        
        print("📊 Monitoramento em tempo real:")
        print("   [tempo] arquivos_atuais/estimado (novos) - taxa - tamanho")
        print()
        
        while process.poll() is None:
            current_time = time.time()
            
            # Check every 30 seconds
            if current_time - last_check >= 30:
                try:
                    current_files = list(self.output_dir.glob("*.nc")) if self.output_dir.exists() else []
                    current_count = len(current_files)
                    
                    # Calculate stats
                    elapsed_time = current_time - start_time
                    new_files = current_count - last_count
                    
                    # Progress percentage
                    progress_pct = (current_count / estimated_total * 100) if estimated_total > 0 else 0
                    
                    # Download rate
                    rate = current_count / (elapsed_time / 60) if elapsed_time > 0 else 0
                    
                    # Total size
                    total_size = sum(f.stat().st_size for f in current_files) / (1024**2)  # MB
                    
                    # ETA calculation
                    if rate > 0 and current_count < estimated_total:
                        remaining_files = estimated_total - current_count
                        eta_minutes = remaining_files / rate
                        eta_str = f"ETA: {eta_minutes:.0f}min"
                    else:
                        eta_str = "ETA: --"
                    
                    # Status line
                    elapsed_str = f"{elapsed_time/60:.0f}min"
                    print(f"   [{elapsed_str:>4}] {current_count:>3}/{estimated_total} ({progress_pct:>4.1f}%) (+{new_files}) - {rate:.1f}/min - {total_size:.0f}MB - {eta_str}")
                    
                    last_count = current_count
                    last_check = current_time
                    
                except Exception as e:
                    print(f"   ⚠️ Erro no monitoramento: {e}")
            
            time.sleep(5)  # Check process status every 5 seconds
    
    def show_final_status(self, start_time, initial_count):
        """
        Show final download status
        """
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        print("\\n" + "=" * 60)
        print("✅ DOWNLOAD CONCLUÍDO")
        print("=" * 60)
        
        # Final file count
        final_files, final_count = self.check_current_status()
        new_files = final_count - initial_count
        
        print(f"⏱️ Tempo total: {elapsed_time/60:.1f} minutos")
        print(f"📁 Arquivos iniciais: {initial_count}")
        print(f"📁 Arquivos finais: {final_count}")
        print(f"📥 Novos arquivos: {new_files}")
        
        if new_files > 0:
            rate = new_files / (elapsed_time / 60) if elapsed_time > 0 else 0
            print(f"⚡ Taxa de download: {rate:.1f} arquivos/min")
        
        # Verify a sample file
        if final_files:
            print("\\n🔍 Verificando arquivo de exemplo...")
            sample_file = final_files[0]
            
            try:
                import xarray as xr
                import numpy as np
                ds = xr.open_dataset(sample_file)
                swh_vars = [var for var in ds.data_vars if 'swh' in var.lower()]
                
                print(f"✅ Arquivo válido: {sample_file.name}")
                print(f"🌊 Variáveis SWH: {len(swh_vars)} encontradas")
                
                if 'swh_karin' in ds.data_vars:
                    swh_data = ds.swh_karin.values
                    valid_swh = swh_data[~np.isnan(swh_data)]
                    if len(valid_swh) > 0:
                        print(f"📊 SWH range: {valid_swh.min():.2f} - {valid_swh.max():.2f} m")
                        
            except Exception as e:
                print(f"⚠️ Erro na verificação: {e}")

def main():
    """
    Main function
    """
    downloader = SWOTWindWaveDownloader()
    
    success = downloader.run_download_with_progress()
    
    if success:
        print("\\n🎯 PRÓXIMOS PASSOS:")
        print("1. Executar: python scripts/processing/process_swot_windwave.py")
        print("2. Criar visualizações combinadas SWOT SWH + ERA5 SWH")
        print("3. Análise comparativa das alturas de onda")
    else:
        print("\\n💡 DICAS:")
        print("- Verifique sua conexão com a internet")
        print("- Execute novamente para continuar download interrompido")
        print("- Use Ctrl+C para interromper se necessário")

if __name__ == "__main__":
    main()