        with st.spinner("Simulating satellite data analysis..."):
            # Create simulated NDVI data
            ndvi = np.random.uniform(-0.2, 0.9, (100, 100))
            
            # Add some patterns to make it look more realistic
            x, y = np.mgrid[0:100, 0:100]
            pattern = np.sin(x/10) * np.cos(y/10) * 0.3
            ndvi = np.clip(ndvi + pattern, -0.2, 0.9)
            
            # Simulate QA60 cloud mask if enabled
            if enable_cloud_masking:
                cloud_mask = simulate_qa60_cloud_mask((100, 100), cloud_coverage, cloud_size)
                
                # Apply cloud masking based on selected method
                if cloud_handling == "Mask Clouds (Show)":
                    # Set cloudy pixels to a specific value indicating clouds (-0.3)
                    masked_ndvi = apply_cloud_mask(ndvi, cloud_mask, mask_value=-0.3)
                elif cloud_handling == "Remove Clouds (Hide)":
                    # Set cloudy pixels to NaN so they're not included in calculations
                    masked_ndvi = apply_cloud_mask(ndvi, cloud_mask, mask_value=np.nan)
                else:  # Interpolate
                    # Start with NaN for cloudy pixels
                    masked_ndvi = apply_cloud_mask(ndvi, cloud_mask, mask_value=np.nan)
                    # This is a simplified approach - real satellite data would use more complex interpolation
                    from scipy import ndimage
                    masked_ndvi_filled = masked_ndvi.copy()
                    
                    # Create a mask for NaN values
                    nan_mask = np.isnan(masked_ndvi)
                    
                    # Use a simple interpolation method
                    # This is a very basic approach - just takes mean of surrounding valid pixels
                    kernel = np.ones((5, 5)) / 25  # Simple 5x5 averaging kernel
                    masked_ndvi_filled[nan_mask] = 0  # Replace NaNs with 0 temporarily for convolution
                    
                    # Convolve with the kernel
                    smoothed = ndimage.convolve(masked_ndvi_filled, kernel, mode='reflect')
                    
                    # Only use the interpolated values for cloudy pixels
                    masked_ndvi_filled[nan_mask] = smoothed[nan_mask]
                    masked_ndvi = masked_ndvi_filled
                
                # For statistics and classification, use the cloud-masked data
                analysis_ndvi = np.copy(masked_ndvi)
                
                # Replace NaNs with mean NDVI for statistical calculations if needed
                if cloud_handling == "Remove Clouds (Hide)":
                    valid_mask = ~np.isnan(analysis_ndvi)
                    if np.any(valid_mask):
                        mean_valid = np.mean(analysis_ndvi[valid_mask])
                        analysis_ndvi[np.isnan(analysis_ndvi)] = mean_valid
            else:
                # No cloud masking, just use the original NDVI
                masked_ndvi = ndvi
                analysis_ndvi = ndvi
                cloud_mask = np.zeros_like(ndvi, dtype=np.uint8)
            
            # Display results
            st.subheader(f"Analysis Results for {location_name}")
            
            if selection_method == "Predefined Locations":
                st.write(f"Area center: {center_lat:.4f}°N, {center_lon:.4f}°E with {area_size} coverage")
            else:
                # Display information based on the drawn area
                try:
                    feature_type = st.session_state.drawn_features.get("geometry", {}).get("type", "unknown")
                    st.write(f"Analysis for drawn {feature_type} at center: {center_lat:.4f}°N, {center_lon:.4f}°E")
                    
                    # If it's a polygon, try to calculate the area
                    if feature_type in ["Polygon", "Rectangle"]:
                        coordinates = st.session_state.drawn_features["geometry"]["coordinates"][0]
                        
                        # Calculate approximate area in square kilometers
                        lats = [coord[1] for coord in coordinates]
                        lons = [coord[0] for coord in coordinates]
                        
                        min_lat = min(lats)
                        max_lat = max(lats)
                        min_lon = min(lons)
                        max_lon = max(lons)
                        
                        # Approximate distance calculation
                        lat_km = abs(max_lat - min_lat) * 111
                        lon_km = abs(max_lon - min_lon) * 111 * np.cos(np.radians(center_lat))
                        area_km2 = lat_km * lon_km
                        
                        st.write(f"Approximate area: {area_km2:.2f} km²")
                except Exception as e:
                    st.write("Could not calculate detailed area information.")
            
            # Show cloud coverage info if enabled
            if enable_cloud_masking:
                cloud_percentage = (np.sum(cloud_mask) / cloud_mask.size) * 100
                st.write(f"Detected cloud coverage: {cloud_percentage:.1f}% of the area")
                st.write(f"Cloud handling method: {cloud_handling}")
            
            # Create classification map
            classified_map = np.zeros((100, 100, 3), dtype=np.uint8)
            class_counts = {class_info["label"]: 0 for _, class_info in NDVI_CLASSES.items()}
            
            # Track total valid (non-cloud) pixels
            total_valid_pixels = 0
            
            # Classify each pixel and count classes
            for i in range(ndvi.shape[0]):
                for j in range(ndvi.shape[1]):
                    # Skip classification for NaN values (clouds removed)
                    if np.isnan(masked_ndvi[i, j]):
                        # Color clouds in white for visualization
                        classified_map[i, j] = [255, 255, 255]
                        continue
                    
                    # Color clouds in light blue if they're shown
                    if masked_ndvi[i, j] <= -0.3:  # Cloud mask value
                        classified_map[i, j] = [200, 200, 255]  # Light blue for clouds
                        continue
                    
                    # Normal classification for valid pixels
                    class_info = classify_ndvi(masked_ndvi[i, j])
                    classified_map[i, j] = class_info["color"]
                    class_counts[class_info["label"]] += 1
                    total_valid_pixels += 1
            
            # Calculate percentages based on valid pixels only
            class_percentages = {label: (count / max(total_valid_pixels, 1)) * 100 
                              for label, count in class_counts.items()}
            
            # Create standard NDVI visualization with cloud masking
            vis = np.zeros((100, 100, 3), dtype=np.uint8)
            
            for i in range(ndvi.shape[0]):
                for j in range(ndvi.shape[1]):
                    if np.isnan(masked_ndvi[i, j]):
                        # White for removed clouds
                        vis[i, j] = [255, 255, 255]
                    elif masked_ndvi[i, j] <= -0.3:  # Cloud mask value
                        # Light blue for shown clouds
                        vis[i, j] = [200, 200, 255]
                    else:
                        # Standard NDVI colorization for valid pixels
                        vis[i, j, 0] = np.clip((1 - masked_ndvi[i, j]) * 255, 0, 255).astype(np.uint8)  # Red
                        vis[i, j, 1] = np.clip(masked_ndvi[i, j] * 255, 0, 255).astype(np.uint8)  # Green
            
            # Convert to PIL Images
            ndvi_image = Image.fromarray(vis)
            classified_image = Image.fromarray(classified_map)
            
            # Create cloud mask visualization
            if enable_cloud_masking:
                cloud_vis = np.zeros((100, 100, 3), dtype=np.uint8)
                # Set non-cloud areas to light gray
                cloud_vis[cloud_mask == 0] = [240, 240, 240]
                # Set cloud areas to blue
                cloud_vis[cloud_mask == 1] = [100, 149, 237]  # Cornflower blue
                cloud_image = Image.fromarray(cloud_vis)
            
            # Display visualizations based on user selection
            if enable_cloud_masking:
                st.subheader("Cloud Mask from QA60 Band")
                st.image(cloud_image, caption="Simulated QA60 Cloud Mask (Blue = Cloud)", use_container_width=True)
            
            if viz_options == "Colorized NDVI":
                st.image(ndvi_image, caption="Colorized NDVI Map (Cloud-Masked)" if enable_cloud_masking else "Colorized NDVI Map", use_container_width=True)
            elif viz_options == "Classification Map":
                st.image(classified_image, caption="Vegetation Classification Map (Cloud-Masked)" if enable_cloud_masking else "Vegetation Classification Map", use_container_width=True)
            else:  # Both
                col1, col2 = st.columns(2)
                with col1:
                    st.image(ndvi_image, caption="Colorized NDVI Map" + (" (Cloud-Masked)" if enable_cloud_masking else ""), use_container_width=True)
                with col2:
                    st.image(classified_image, caption="Vegetation Classification Map" + (" (Cloud-Masked)" if enable_cloud_masking else ""), use_container_width=True)