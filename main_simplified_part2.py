def main():
    """Main function to set up the Streamlit app for the Crop Health Monitoring System"""
    
    # Set up initial session state if not already set
    if "clicks" not in st.session_state:
        st.session_state.clicks = []
    if "click_count" not in st.session_state:
        st.session_state.click_count = 0
    if "drawn_features" not in st.session_state:
        st.session_state.drawn_features = None
    
    # Set page config
    st.set_page_config(
        page_title="Crop Health Monitoring System",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # App header
    st.title("Crop Health Monitoring System")
    st.markdown("""
    This application simulates crop health monitoring using NDVI (Normalized Difference Vegetation Index) analysis with **Sentinel-2 satellite imagery**. 
    Select an area of interest and analyze vegetation health with cloud masking support.
    """)
    
    # Sidebar for controls
    st.sidebar.title("Controls")
    
    # Selection method: predefined locations or map selection
    selection_method = st.sidebar.radio(
        "Area Selection Method",
        ["Predefined Locations", "Map Selection"]
    )
    
    # Default values for map center
    center_lat = 20.5937
    center_lon = 78.9629
    zoom = 5
    location_name = "India"
    
    # Location selection based on method
    if selection_method == "Predefined Locations":
        # Dropdown for predefined locations
        location_name = st.sidebar.selectbox(
            "Select Location",
            list(LOCATION_OPTIONS.keys())
        )
        
        if location_name != "Select a location":
            center_lat = LOCATION_OPTIONS[location_name]["lat"]
            center_lon = LOCATION_OPTIONS[location_name]["lon"]
            zoom = LOCATION_OPTIONS[location_name]["zoom"]
        
        # Allow manual adjustment
        with st.sidebar.expander("Adjust coordinates"):
            center_lat = st.number_input("Latitude", value=center_lat, format="%.4f")
            center_lon = st.number_input("Longitude", value=center_lon, format="%.4f")
            
    else:  # Map Selection
        st.sidebar.write("Use the tools on the map to draw your area of interest.")
        
        # If we have a drawn feature, extract its center
        if st.session_state.drawn_features:
            try:
                # Extract coordinates from the drawn feature
                geometry = st.session_state.drawn_features.get("geometry", {})
                geometry_type = geometry.get("type", "")
                
                if geometry_type == "Point":
                    # If it's a point, use its coordinates directly
                    center_lon, center_lat = geometry.get("coordinates", [center_lon, center_lat])
                    
                elif geometry_type == "Circle":
                    # Circle has a center point
                    center_lon, center_lat = geometry.get("coordinates", [center_lon, center_lat])
                    
                elif geometry_type in ["Polygon", "Rectangle"]:
                    # For polygons/rectangles, calculate the centroid
                    coordinates = geometry.get("coordinates", [[]])[0]
                    
                    # Calculate the centroid as the average of all points
                    lats = [coord[1] for coord in coordinates]
                    lons = [coord[0] for coord in coordinates]
                    
                    center_lat = sum(lats) / len(lats)
                    center_lon = sum(lons) / len(lons)
                    
                    # Calculate approximate area in square kilometers
                    min_lat = min(lats)
                    max_lat = max(lats)
                    min_lon = min(lons)
                    max_lon = max(lons)
                    
                    # Approximate distance calculation
                    lat_km = abs(max_lat - min_lat) * 111  # 111 km per degree of latitude
                    lon_km = abs(max_lon - min_lon) * 111 * np.cos(np.radians(center_lat))  # Longitude depends on latitude
                    area_km2 = lat_km * lon_km
                    
                    area_description = f"Selected area: ~{area_km2:.2f} km²\nCenter: {center_lat:.4f}, {center_lon:.4f}"
                    st.sidebar.info(area_description)
                    
                    # Allow manual adjustment
                    with st.sidebar.expander("Adjust coordinates manually"):
                        st.number_input("Center Latitude", value=center_lat, step=0.01, format="%.4f", key="adj_lat")
                        st.number_input("Center Longitude", value=center_lon, step=0.01, format="%.4f", key="adj_lon")
                
                # Mark that we have valid coordinates for analysis
                zoom = 10  # Zoom in on selected area
            except Exception as e:
                st.sidebar.warning(f"Could not process drawn shape: {e}")
    
    # Allow users to specify area size (only for predefined locations)
    if selection_method == "Predefined Locations":
        area_size_options = {
            "Small (1 hectare)": 0.01,
            "Medium (10 hectares)": 0.03,
            "Large (100 hectares)": 0.1,
            "Very Large (1000 hectares)": 0.3
        }
        
        area_size = st.sidebar.selectbox(
            "Select area size", 
            list(area_size_options.keys())
        )
        area_radius = area_size_options[area_size]
    
    # Clear selection button
    if st.sidebar.button("Clear Selection"):
        st.session_state.clicks = []
        st.session_state.click_count = 0
        st.session_state.drawn_features = None
        st.rerun()
    
    # Map View section with Leaflet maps
    st.subheader("Map View")
    
    # Create a folium map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB positron"
    )
    
    # Add India outline as a polygon
    folium.Polygon(
        locations=INDIA_OUTLINE,
        color='blue',
        weight=2,
        fill=True,
        fill_color='#86c67c',
        fill_opacity=0.2,
        tooltip="India"
    ).add_to(m)
    
    # Add major cities as markers
    for city, (lat, lon) in MAJOR_CITIES.items():
        folium.Marker(
            [lat, lon],
            tooltip=city,
            icon=folium.Icon(icon="info", prefix="fa", color="blue")
        ).add_to(m)
    
    # Add drawing tools for map selection
    if selection_method == "Map Selection":
        draw = Draw(
            draw_options={
                'polyline': False,
                'circle': True,
                'rectangle': True,
                'polygon': True,
                'marker': False,
                'circlemarker': False,
            },
            edit_options={
                'poly': {'allowIntersection': False}
            }
        )
        draw.add_to(m)
        
        # Add mouse position display
        MousePosition().add_to(m)
    
    # For predefined locations, add circle marker showing selected area
    if selection_method == "Predefined Locations":
        folium.Circle(
            location=[center_lat, center_lon],
            radius=area_radius * 111000,  # Convert degrees to meters (approx)
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.2,
            tooltip=f"{location_name}: {area_radius}° radius"
        ).add_to(m)
        
        # Add marker at center
        folium.Marker(
            [center_lat, center_lon],
            tooltip=f"Center: {center_lat:.4f}, {center_lon:.4f}",
            icon=folium.Icon(color="red", icon="info")
        ).add_to(m)
    
    # If we have drawn features, display them on the map
    if selection_method == "Map Selection" and st.session_state.drawn_features:
        try:
            feature_group = folium.FeatureGroup(name="Selected Area")
            
            # Add the drawn features as GeoJSON
            folium.GeoJson(
                st.session_state.drawn_features,
                style_function=lambda x: {
                    'fillColor': 'red',
                    'color': 'red',
                    'weight': 2,
                    'fillOpacity': 0.2
                }
            ).add_to(feature_group)
            
            feature_group.add_to(m)
        except Exception as e:
            st.warning(f"Error displaying drawn area: {e}")
    
    # Display the map with streamlit-folium
    map_data = st_folium(
        m, 
        width=700,
        height=500,
        returned_objects=["last_active_drawing"],
        key="map"
    )
    
    # Process map interactions
    if selection_method == "Map Selection" and map_data and "last_active_drawing" in map_data and map_data["last_active_drawing"]:
        st.session_state.drawn_features = map_data["last_active_drawing"]
        st.rerun()
    
    # Map selection instructions
    if selection_method == "Map Selection":
        with st.expander("Map Selection Instructions"):
            st.markdown("""
            ### How to select an area on the map:
            1. Use the drawing tools in the top right corner of the map
            2. Choose one of the following tools:
               - Circle: Click on the center and drag to set the radius
               - Rectangle: Click and drag to draw a rectangle
               - Polygon: Click multiple points to create a custom shape
            3. Once you've drawn your area, it will be saved for analysis
            4. Click 'Analyze Area' in the sidebar when ready
            """)
    else:
        # Instructions for predefined area selection
        with st.expander("How to select an area"):
            st.write("""
            1. Choose a predefined location from the dropdown
            2. Adjust latitude and longitude if needed
            3. Select the area size that best fits your analysis needs
            4. The red circle on the map shows your selected area
            5. Click 'Analyze Area' in the sidebar when ready
            """)
    
    # Analysis controls
    st.sidebar.subheader("Analysis")
    today = datetime.now().date()
    start_date = st.sidebar.date_input("Start Date", value=today - timedelta(days=30))
    end_date = st.sidebar.date_input("End Date", value=today)
    
    # Add NDVI visualization options
    viz_options = st.sidebar.radio(
        "Visualization Type",
        ["Colorized NDVI", "Classification Map", "Both"],
        index=2
    )
    
    # Cloud masking options
    st.sidebar.subheader("Cloud Handling")
    enable_cloud_masking = st.sidebar.checkbox("Enable Cloud Masking (QA60)", value=True)
    
    if enable_cloud_masking:
        cloud_coverage = st.sidebar.slider("Simulated Cloud Coverage", 0.0, 1.0, 0.2, 0.05)
        cloud_size = st.sidebar.slider("Simulated Cloud Size", 5, 30, 10, 1)
        cloud_handling = st.sidebar.radio(
            "Cloud Handling Method",
            ["Mask Clouds (Show)", "Remove Clouds (Hide)", "Interpolate"]
        )
    
    if st.sidebar.button("Analyze Area"):
        # Save the selected area for analysis
        if selection_method == "Predefined Locations":
            selected_area = {
                "center": {"lat": center_lat, "lon": center_lon},
                "radius": area_radius,
                "location_name": location_name,
                "type": "circle"
            }
        else:
            if not st.session_state.drawn_features:
                st.sidebar.error("Please select an area on the map first")
                return
            
            selected_area = {
                "drawn_features": st.session_state.drawn_features,
                "center": {"lat": center_lat, "lon": center_lon},
                "location_name": location_name,
                "type": "drawn"
            }
        
        # Store in session state
        st.session_state.selected_area = selected_area