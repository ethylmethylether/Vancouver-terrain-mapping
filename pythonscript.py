# -*- coding: utf-8 -*-
"""
Created on Tue Jul 22 19:22:11 2025

@author: Uzair
"""

import rasterio
import geopandas as gpd                      
from rasterio.merge import merge    
import numpy as np                   
import matplotlib.pyplot as plt      
import glob                         
import os                           
from matplotlib.colors import LightSource

# Vancouver Boundary
boundary = gpd.read_file("local-area-boundary.geojson")


# Path to GeoTIFF files
path = "vancouver_aster_tiles/"

tif_files = glob.glob(os.path.join(path, "*.tif"))

# Opening raster tiles and storing them in a list
src_files = [rasterio.open(fp) for fp in tif_files]

# Merge all tiles into a single mosaic raster and storing GeoData
mosaic, out_trans = merge(src_files)

for src in src_files:
    src.close()

# Extract the first band from the merged raster, which contains elevation data
elevation = mosaic[0]

with rasterio.open(tif_files[0]) as src:
    raster_crs = src.crs
if boundary.crs!= raster_crs:
    boundary = boundary.to_crs(raster_crs)

# Define terrain zones based on elevation ranges (meters) and assign IDs
zones = [
    (0, 200, 1),     # Lowlands: elevation between 0 and 200 meters
    (200, 500, 2),   # Uplands: elevation between 200 and 500 meters
    (500, 1000, 3),  # Highlands: elevation between 500 and 1000 meters
    (1000, 2000, 4), # Hills: elevation between 1000 and 2000 meters
    (2000, 4000, 5), # Mountains: elevation between 2000 and 4000 meters
    (4000, 9000, 6)  # High Mountains: elevation between 4000 and 9000 meters
]

# An empty array same size as elevation, filled with -1 (meaning unclassified)
classified = np.full(elevation.shape, -1)

# Loop through each elevation zone and assign zone IDs to pixels within the range
for low, high, zone_id in zones:
    mask = (elevation >= low) & (elevation < high)  # Create boolean mask for this zone
    classified[mask] = zone_id                       # Assign zone_id to those pixels

# Find unique zone IDs and counts of pixels for each zone (ignoring unclassified pixels)
unique, counts = np.unique(classified[classified > 0], return_counts=True)

# Calculate area of one pixel in square kilometers (30m x 30m = 900 m² = 0.0009 km²)
pixel_area_km2 = (30 * 30) / 1e6

# Dictionary to map zone IDs to their names
zone_names = {
    1: 'Lowlands',
    2: 'Uplands',
    3: 'Highlands',
    4: 'Hills',
    5: 'Mountains',
    6: 'High Mountains'
}

# Print the total area of each terrain zone in square kilometers
print("Area per Terrain Zone (Vancouver Region)\n")
for zone_id, count in zip(unique, counts):
    area = count * pixel_area_km2
    print(f"{zone_names.get(zone_id, 'Unknown')}: {area:.2f} km²")

# ----------------- Plotting Section -----------------

plt.figure(figsize=(11, 10))
cmap = plt.get_cmap("terrain", len(zones))

def get_bounds(transform, width, height):
    left = transform.c
    top = transform.f
    right = left + transform.a * width
    bottom = top + transform.e * height
    return (left, right, bottom, top)

left, right, bottom, top = get_bounds(out_trans, mosaic.shape[2], mosaic.shape[1])

img = plt.imshow(classified, cmap=cmap, extent=[left, right, bottom, top])

plt.xlabel("Longitude")
plt.ylabel("Latitude")

cbar = plt.colorbar(img, ticks=range(1, len(zones)+1))
cbar.ax.set_yticklabels([
    'Lowlands', 'Uplands', 'Highlands', 'Hills', 'Mountains', 'High Mountains'
])

ls = LightSource(azdeg=315, altdeg=45)
hillshade = ls.shade(elevation, cmap=plt.cm.terrain, blend_mode='overlay')
plt.imshow(hillshade, alpha=0.5, extent=[left, right, bottom, top])
plt.title("Vancouver Area Terrain Zones")
plt.savefig("figures/terrain_map.png", dpi=300)
plt.tight_layout()
plt.show()

# ----------------- Bar Chart of Terrain Zone Areas -----------------

labels = [zone_names[z] for z in unique]
areas = [c * pixel_area_km2 for c in counts]

cmap = plt.get_cmap("terrain", len(zones))
bar_colors = [cmap(z - 1) for z in unique]

plt.figure(figsize=(10, 6))
plt.bar(labels, areas, color=bar_colors)
plt.ylabel("Area (km²)")
plt.title("Terrain Zone Area – Vancouver Region")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("figures/terrain_area.png", dpi=300)
plt.show()

