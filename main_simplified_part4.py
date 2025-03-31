            # Create legend for classification
            st.subheader("Vegetation Classification Legend")
            
            # Add one more column for clouds if cloud masking is enabled
            num_columns = len(NDVI_CLASSES) + (1 if enable_cloud_masking else 0)
            legend_cols = st.columns(num_columns)
            
            for i, ((min_val, max_val), class_info) in enumerate(sorted(NDVI_CLASSES.items())):
                with legend_cols[i]:
                    # Create a small colored box for the legend
                    color = 'rgb({}, {}, {})'.format(*class_info["color"])
                    html = f"""
                    <div style="
                        background-color: {color}; 
                        width: 20px; 
                        height: 20px; 
                        display: inline-block;
                        margin-right: 5px;
                        "></div>
                    <span><b>{class_info["label"]}</b></span>
                    <br><span>NDVI: {min_val:.1f} to {max_val:.1f}</span>
                    <br><span style="font-size: 0.8em;">{class_percentages[class_info["label"]]:.1f}% of area</span>
                    """
                    st.markdown(html, unsafe_allow_html=True)
                    st.write(class_info["description"])
            
            # Add cloud column if cloud masking is enabled
            if enable_cloud_masking:
                with legend_cols[-1]:
                    html = f"""
                    <div style="
                        background-color: rgb(200, 200, 255); 
                        width: 20px; 
                        height: 20px; 
                        display: inline-block;
                        margin-right: 5px;
                        "></div>
                    <span><b>Clouds</b></span>
                    <br><span>QA60 Band</span>
                    <br><span style="font-size: 0.8em;">{cloud_percentage:.1f}% of area</span>
                    """
                    st.markdown(html, unsafe_allow_html=True)
                    st.write("Areas detected as clouds using the QA60 band")
            
            # Display statistics
            st.subheader("NDVI Statistics (Excluding Clouds)")
            
            # Calculate statistics on non-cloud pixels
            valid_mask = ~np.isnan(masked_ndvi) if cloud_handling == "Remove Clouds (Hide)" else masked_ndvi > -0.3
            
            if np.any(valid_mask):
                valid_ndvi = masked_ndvi[valid_mask]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Min NDVI", f"{np.min(valid_ndvi):.2f}")
                with col2:
                    st.metric("Mean NDVI", f"{np.mean(valid_ndvi):.2f}")
                with col3:
                    st.metric("Max NDVI", f"{np.max(valid_ndvi):.2f}")
            else:
                st.warning("No valid (non-cloud) pixels available for statistics.")
            
            # Add histogram of NDVI values (excluding clouds)
            fig, ax = plt.subplots(figsize=(10, 4))
            
            if np.any(valid_mask):
                valid_ndvi_flat = masked_ndvi[valid_mask].flatten()
                n, bins, patches = ax.hist(valid_ndvi_flat, bins=20, alpha=0.7)
                
                # Color the histogram bars according to NDVI value
                cmap = create_ndvi_colormap()
                bin_centers = 0.5 * (bins[:-1] + bins[1:])
                # Normalize the bin centers to [0, 1] for the colormap
                norm_centers = (bin_centers - (-0.2)) / (0.9 - (-0.2))
                
                for i, patch in enumerate(patches):
                    if norm_centers[i] < 0:
                        # For values below our range, use a light blue color
                        patch.set_facecolor([0.8, 0.8, 1.0])
                    else:
                        color = cmap(min(max(norm_centers[i], 0), 1))
                        patch.set_facecolor(color)
                
                ax.set_xlabel('NDVI Value')
                ax.set_ylabel('Pixel Count')
                ax.set_title('Distribution of NDVI Values (Excluding Clouds)')
                ax.grid(alpha=0.3)
                
                # Add vertical lines for class thresholds
                for (min_val, max_val), class_info in NDVI_CLASSES.items():
                    if min_val > -0.2:  # Skip the lowest bound
                        ax.axvline(x=min_val, color='gray', linestyle='--', alpha=0.7)
                        ax.text(min_val, ax.get_ylim()[1]*0.9, f"{min_val}", 
                              rotation=90, verticalalignment='top')
                
                # Create custom legend patches
                legend_patches = []
                for (min_val, max_val), class_info in sorted(NDVI_CLASSES.items()):
                    color = [c/255 for c in class_info["color"]]
                    patch = mpatches.Patch(color=color, label=class_info["label"])
                    legend_patches.append(patch)
                
                if enable_cloud_masking:
                    cloud_patch = mpatches.Patch(color=[0.8, 0.8, 1.0], label="Clouds (excluded)")
                    legend_patches.append(cloud_patch)
                    
                ax.legend(handles=legend_patches, loc='upper right')
                
                st.pyplot(fig)
            else:
                st.warning("No valid data available for histogram after cloud masking.")
            
            # Use comprehensive NDVI-based health classification on non-cloud areas
            if np.any(valid_mask):
                # Calculate dominant class (excluding clouds)
                dominant_class = max(class_percentages.items(), key=lambda x: x[1])[0]
                
                # Calculate health score (weighted by class percentages)
                # Higher weights for better vegetation classes
                weights = {
                    "Water/Non-Vegetation": 0.0,
                    "Sparse Vegetation": 0.25,
                    "Moderate Vegetation": 0.5,
                    "Good Vegetation": 0.75,
                    "Dense Vegetation": 1.0
                }
                
                health_score = sum(weights[label] * pct for label, pct in class_percentages.items())
                
                # Display health classification
                st.subheader("Crop Health Assessment")
                
                # Show cloud impact warning if significant
                if enable_cloud_masking and cloud_percentage > 30:
                    st.warning(f"⚠️ High cloud coverage ({cloud_percentage:.1f}%) may affect analysis accuracy.")
                
                st.progress(health_score / 100)
                st.write(f"Overall Health Score: {health_score:.1f}%")
                st.write(f"Dominant Vegetation Class: {dominant_class} ({class_percentages[dominant_class]:.1f}%)")
                
                # Health status message
                if health_score > 70:
                    st.success("Crop health is excellent! The vegetation in this area shows optimal photosynthetic activity.")
                elif health_score > 50:
                    st.success("Crop health is good. Most of the area has healthy vegetation.")
                elif health_score > 30:
                    st.warning("Crop health is moderate. Consider monitoring irrigation and nutrient levels.")
                else:
                    st.error("Crop health is poor. Immediate attention may be required to address potential issues.")
                
                # Detailed analysis
                st.subheader("Detailed Analysis")
                
                if enable_cloud_masking and cloud_percentage > 10:
                    st.write(f"Analysis performed on {100-cloud_percentage:.1f}% of the area (cloud-free pixels).")
                
                st.write("Based on the NDVI classification, we've identified the following insights:")
                
                # Generate insights based on classification
                insights = []
                
                # Water/non-vegetation insights
                water_pct = class_percentages["Water/Non-Vegetation"]
                if water_pct > 15:
                    insights.append(f"Significant non-vegetative area detected ({water_pct:.1f}%). This may include water bodies, bare soil, or artificial surfaces.")
                
                # Sparse vegetation insights
                sparse_pct = class_percentages["Sparse Vegetation"]
                if sparse_pct > 30:
                    insights.append(f"Large portions of sparse vegetation ({sparse_pct:.1f}%) indicate potential crop stress or early growth stages.")
                
                # Moderate vegetation insights
                moderate_pct = class_percentages["Moderate Vegetation"]
                if moderate_pct > 40:
                    insights.append(f"Predominant moderate vegetation ({moderate_pct:.1f}%) suggests developing crops that may benefit from additional nutrients.")
                
                # Good vegetation insights
                good_pct = class_percentages["Good Vegetation"]
                if good_pct > 40:
                    insights.append(f"Significant healthy vegetation ({good_pct:.1f}%) indicates well-maintained crops with good photosynthetic activity.")
                
                # Dense vegetation insights
                dense_pct = class_percentages["Dense Vegetation"]
                if dense_pct > 30:
                    insights.append(f"High proportion of dense vegetation ({dense_pct:.1f}%) shows excellent crop development and optimal growing conditions.")
                
                # Cloud impact insights
                if enable_cloud_masking and cloud_percentage > 20:
                    insights.append(f"Significant cloud coverage ({cloud_percentage:.1f}%) detected. Consider acquiring additional imagery with lower cloud coverage for more accurate analysis.")
                
                if not insights:
                    insights.append("The area shows a mixed pattern of vegetation health. Regular monitoring is recommended.")
                
                for insight in insights:
                    st.write(f"• {insight}")
                
                # Sample recommendations
                st.subheader("Recommendations")
                st.write("Based on the NDVI classification analysis, here are some recommendations:")
                
                recommendations = [
                    f"Focus irrigation on areas showing sparse vegetation (orange regions - {sparse_pct:.1f}% of area)",
                    f"Apply targeted fertilizer to boost moderate vegetation areas (yellow regions - {moderate_pct:.1f}% of area)",
                    "Monitor temporal changes in NDVI to track crop development over time",
                    "Consider soil testing in areas with consistently low NDVI values",
                    "Implement crop rotation strategies for the next season in underperforming regions"
                ]
                
                # Add cloud-specific recommendations if needed
                if enable_cloud_masking and cloud_percentage > 30:
                    recommendations.insert(0, "Acquire additional satellite imagery with lower cloud coverage for more accurate analysis")
                    
                for i, rec in enumerate(recommendations):
                    st.write(f"{i+1}. {rec}")
            else:
                st.error("Unable to perform analysis due to excessive cloud coverage. Please try a different date or area.")

if __name__ == "__main__":
    main() 