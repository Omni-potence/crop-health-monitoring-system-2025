import streamlit as st
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import folium
from folium.plugins import Draw, MousePosition
from streamlit_folium import st_folium, folium_static
import json
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import pandas as pd
from scipy import ndimage

# Define India's outline coordinates - simplified version
INDIA_OUTLINE = [
    [77.8369140625, 35.6037187406973],
    [78.9111328125, 35.53222622770337],
    [80.7275390625, 34.08877366134954],
    [79.1455078125, 32.99023555965106],
    [78.6767578125, 31.57853542647338],
    [79.3798828125, 30.713503990354965],
    [80.7275390625, 29.954934549656144],
    [81.3720703125, 30.107117887092357],
    [82.353515625, 30.107117887092357],
    [83.583984375, 29.458731185355344],
    [84.462890625, 28.613459424004414],
    [85.869140625, 28.304380682962783],
    [86.923828125, 27.994401411046148],
    [88.2421875, 27.916766641249065],
    [89.296875, 28.14950321154457],
    [90.3515625, 28.14950321154457],
    [91.58203125, 27.994401411046148],
    [92.28515625, 27.059125784374068],
    [93.251953125, 26.902476886279832],
    [94.21875, 27.371767300523047],
    [95.44921875, 26.902476886279832],
    [96.15234375, 27.371767300523047],
    [97.03125, 27.683528083787763],
    [97.3828125, 28.613459424004414],
    [98.876953125, 27.059125784374068],
    [97.734375, 24.367113562651276],
    [98.173828125, 23.885837699862005],
    [98.876953125, 22.431340156360684],
    [96.50390625, 21.94304553343818],
    [95.625, 19.973348786110602],
    [94.833984375, 17.644022027872712],
    [94.7412109375, 15.961329081596647],
    [93.8623046875, 15.282400104387573],
    [92.8759765625, 12.382928338487396],
    [93.1982421875, 10.833305983642491],
    [94.482421875, 8.059229627200192],
    [95.2734375, 8.407168163601076],
    [95.361328125, 9.795677582829743],
    [96.416015625, 8.754794702435618],
    [96.767578125, 7.36246686553575],
    [94.39453125, 6.751896464843375],
    [92.197265625, 8.189742344299745],
    [91.0986328125, 9.622414142924805],
    [88.9013671875, 10.660607953624762],
    [87.5927734375, 12.82866505819387],
    [87.5927734375, 14.519780046326085],
    [88.7109375, 15.961329081596647],
    [88.4326171875, 17.14079039331665],
    [87.1826171875, 17.56024650540857],
    [85.1220703125, 19.394067895396613],
    [83.1494140625, 20.715015145512098],
    [81.82617187499999, 21.248422235627014],
    [78.2666015625, 22.998851594142913],
    [77.5634765625, 25.48295117535531],
    [78.0322265625, 27.371767300523047],
    [77.4609375, 29.916852233070173],
    [76.9921875, 30.713503990354965],
    [73.828125, 31.95216223802496],
    [74.35546875, 33.65120829920497],
    [74.8828125, 34.813802729634], 
    [77.8369140625, 35.6037187406973]
]

# Predefined locations for easy selection
LOCATION_OPTIONS = {
    "Select a location": {"lat": 20.5937, "lon": 78.9629, "zoom": 5},  # Default - India
    "Punjab (Wheat Belt)": {"lat": 30.9010, "lon": 75.8573, "zoom": 8},
    "Karnataka (Coffee Region)": {"lat": 12.9716, "lon": 75.6099, "zoom": 9},
    "Maharashtra (Cotton Belt)": {"lat": 20.7128, "lon": 77.0020, "zoom": 8},
    "Tamil Nadu (Rice Fields)": {"lat": 11.1271, "lon": 78.6569, "zoom": 8},
    "Uttar Pradesh (Sugarcane Region)": {"lat": 28.0000, "lon": 79.0000, "zoom": 8},
}

# Major cities for reference
MAJOR_CITIES = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Bangalore": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867)
}

# Define NDVI classification thresholds and categories
NDVI_CLASSES = {
    (-0.2, 0.0): {"label": "Water/Non-Vegetation", "color": [0, 0, 128], "description": "Bodies of water, bare soil, or artificial surfaces"},
    (0.0, 0.2): {"label": "Sparse Vegetation", "color": [255, 165, 0], "description": "Very sparse vegetation, stressed crops, or barren areas"},
    (0.2, 0.4): {"label": "Moderate Vegetation", "color": [255, 255, 0], "description": "Moderate vegetation, potentially with mild stress or early growth stages"},
    (0.4, 0.6): {"label": "Good Vegetation", "color": [144, 238, 144], "description": "Healthy vegetation with good leaf area coverage"},
    (0.6, 0.9): {"label": "Dense Vegetation", "color": [0, 128, 0], "description": "Very healthy, dense vegetation with optimal photosynthetic activity"}
}

def simulate_qa60_cloud_mask(shape, cloud_coverage=0.2, cloud_size=10):
    """
    Simulate QA60 band from Sentinel-2 for cloud masking.
    
    Args:
        shape: Tuple, shape of the image (height, width)
        cloud_coverage: Float, percentage of the image covered by clouds (0-1)
        cloud_size: Int, approximate size of cloud clusters in pixels
        
    Returns:
        Binary mask where 1 = cloud, 0 = clear
    """
    height, width = shape
    # Start with all clear
    mask = np.zeros(shape, dtype=np.uint8)
    
    # Number of cloud clusters
    num_clusters = int((height * width * cloud_coverage) / (cloud_size * cloud_size))
    
    # Create random cloud clusters
    for _ in range(num_clusters):
        # Random center for cloud cluster
        center_y = np.random.randint(0, height)
        center_x = np.random.randint(0, width)
        
        # Create cloud cluster with random radius
        cluster_radius = np.random.randint(cloud_size//2, cloud_size)
        
        # Add cloud to mask
        y_indices, x_indices = np.ogrid[:height, :width]
        dist_from_center = np.sqrt((y_indices - center_y)**2 + (x_indices - center_x)**2)
        
        # Core clouds (always cloudy)
        core_cloud = dist_from_center <= cluster_radius * 0.7
        mask[core_cloud] = 1
        
        # Cloud edges (partially cloudy with gradient)
        cloud_edge = (dist_from_center > cluster_radius * 0.7) & (dist_from_center <= cluster_radius)
        
        # Random scatter at edges to make it look more natural
        edge_rand = np.random.random(shape) < 0.7
        mask[cloud_edge & edge_rand] = 1
    
    return mask

def apply_cloud_mask(ndvi, cloud_mask, mask_value=-0.3):
    """
    Apply cloud mask to NDVI data
    
    Args:
        ndvi: NDVI data array
        cloud_mask: Binary mask (1 = cloud, 0 = clear)
        mask_value: Value to assign to cloudy pixels
        
    Returns:
        Masked NDVI array
    """
    # Make a copy to avoid modifying the original
    masked_ndvi = ndvi.copy()
    
    # Set cloudy pixels to mask_value
    masked_ndvi[cloud_mask == 1] = mask_value
    
    return masked_ndvi

def classify_ndvi(ndvi_value):
    """Classify NDVI value into vegetation categories"""
    for (min_val, max_val), class_info in NDVI_CLASSES.items():
        if min_val <= ndvi_value < max_val:
            return class_info
    # Default fallback - use the last class if the value is above our highest threshold
    if ndvi_value >= 0.9:
        return NDVI_CLASSES[(0.6, 0.9)]
    # Or the first class if it's below our lowest threshold
    return NDVI_CLASSES[(-0.2, 0.0)]

def create_ndvi_colormap():
    """Create a custom colormap for NDVI visualization"""
    colors = []
    positions = []
    
    # Sort thresholds
    sorted_thresholds = sorted(NDVI_CLASSES.items())
    
    # Create normalized positions and corresponding colors
    min_ndvi = -0.2
    max_ndvi = 0.9
    ndvi_range = max_ndvi - min_ndvi
    
    for (min_val, max_val), class_info in sorted_thresholds:
        # Normalize the threshold values to [0, 1]
        pos_min = (min_val - min_ndvi) / ndvi_range
        pos_max = (max_val - min_ndvi) / ndvi_range
        
        # Convert RGB [0-255] to [0-1] for matplotlib
        color = [c/255 for c in class_info["color"]]
        
        if len(colors) == 0:
            positions.append(pos_min)
            colors.append(color)
        
        positions.append(pos_max)
        colors.append(color)
    
    return LinearSegmentedColormap.from_list('ndvi_cmap', list(zip(positions, colors)))