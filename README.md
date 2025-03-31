# Crop Health Monitoring System

A sophisticated application for monitoring crop health using NDVI visualization, cloud masking, and analysis techniques.

## Author Information

- **Student:** Mital Talhan
- **Mentor:** Ajay Sahu
- **Institute:** Bajaj Institute of Technology, Wardha

## Project Overview

This project implements a comprehensive crop health monitoring system that addresses the challenge of cloud interference in satellite-based NDVI analysis. The system simulates the QA60 band from Sentinel-2 imagery to identify and handle clouds, providing more accurate crop health assessments.

## Key Features

- **Interactive Map Interface:** Select agricultural regions directly on an interactive map of India with drawing tools
- **Cloud Masking:** Three methods to handle cloud cover - visualize, remove, or interpolate cloud-affected areas
- **NDVI Classification:** Detailed vegetation classification with 5 health categories
- **Comprehensive Analysis:** Statistical analysis with cloud exclusion for more accurate results
- **Smart Recommendations:** Targeted agricultural management suggestions based on NDVI patterns

## Technology Stack

- **Python** with libraries:
  - Streamlit for the web interface
  - NumPy for numerical operations
  - Matplotlib for visualization
  - Folium for interactive maps
  - PIL for image processing
  - SciPy for interpolation operations

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/crop-health-monitoring-system-2025.git
   cd crop-health-monitoring-system-2025
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run main_simplified.py
   ```

## Cloud Detection and Handling

### Detection Method
- Simulates Sentinel-2's QA60 band for cloud identification
- Configurable cloud coverage percentage and cloud cluster size
- Realistic cloud edge simulation with randomization

### Handling Methods
- **Mask Clouds (Show)**: Visualize clouds as light blue in the image
- **Remove Clouds (Hide)**: Completely exclude cloud pixels from analysis
- **Interpolate**: Fill cloud pixels using surrounding valid pixel averages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

The authors would like to thank the Bajaj Institute of Technology, Wardha, for providing the infrastructure and support for this research.