

from pathlib import Path
import os
import sys
sys.path.append(str(Path(__file__).parent))


import rasterio
# import arcpy
import pyproj



# arcpy.env.workspace = r'I:\Projects\Josh\Regional Monitoring\ArcPro_sup\Accessibility\Accessibility.gdb'
file_gdb = r'I:\Projects\Josh\Regional Monitoring\ArcPro_sup\Accessibility\Accessibility.gdb'

try:
    print(rasterio.show_versions()); print()
    
    print(f"Pyproj version: {pyproj.__version__}")
    print(f"PROJ data path: {pyproj.datadir}")
    print(f"PROJ lib path: {os.environ.get('PROJ_LIB')}")
    print(f"PROJ data path (environ): {os.environ.get('PROJ_DATA')}")
except AttributeError:
    print("Pyproj not installed or older version")
except Exception as e:
    print(f"An error occurred: {e}")