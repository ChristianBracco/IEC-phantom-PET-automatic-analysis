# VOI_identification_IQ
# 3D Coordinates with Sphere Midpoint Identification

This tool enables users to interactively identify and analyze spherical regions of interest (ROIs), such as target spheres in medical imaging (e.g., PET scans), by clicking on 3D DICOM image slices. The script automates the process of finding the optimal center and extracting pixel data/statistics for each sphere, saving results and visualizations for further analysis.

---

## Features

- **DICOM Import**: Loads a folder containing DICOM slices (2D images from a 3D scan).
- **Slice Navigation & Visualization**: Displays slices and allows interactive navigation via mouse scroll.
- **User-Guided Midpoint Selection**: Prompts the user to click on the approximate center of each sphere, recording (x, y, z) coordinates.
- **Automatic 3D Midpoint Optimization**: Refines each user click to the local 3D maximum mean intensity, improving accuracy.
- **Region Extraction & Analysis**: For each sphere and slice, extracts circular (or cylindrical) regions, calculating statistics (mean, max, variance, etc.).
- **Image & Data Output**: Saves annotated slice images and exports statistics/data to Excel files.
- **Fully Scripted Workflow**: Reproducible and customizable for different scan folders or target setups.

---

## How It Works

### 1. DICOM Image Loading
- The script recursively loads all DICOM files in a specified folder and sorts them by slice location.
- Images are rescaled using DICOM metadata.

### 2. Finding the Center Slice
- The slice with the highest mean intensity is automatically selected as the starting point for user interaction.

### 3. User-Guided Midpoint Selection
- A graphical window opens to display the center slice.
- You can scroll through slices with your mouse wheel.
- For each target sphere, click once on the image at the estimated center of the sphere.
- The script expects a fixed number of clicks (default is 6).
- After all clicks are made, the GUI closes and the coordinates are used for further analysis.

### 4. 3D Midpoint Optimization
- Around each user-supplied (x, y, z), the script searches in a small 3D neighborhood to find the point with the highest mean intensity within a sphere of the specified diameter.
- This step increases the accuracy of region extraction.

### 5. Region Extraction & Statistics
- For each sphere, the code:
  - Extracts circular/cylindrical pixel regions from relevant slices.
  - Calculates metrics such as mean, max, variance, and number of pixels.
  - Stores the pixel values and statistics for post-processing.

### 6. Output
- **Annotated Images**: Slices with overlaid circles are saved to an output folder.
- **Excel Files**: Several Excel files are generated, containing:
  - Pixel values for each sphere and slice.
  - Optimized midpoint coordinates and their statistics.
  - Aggregate statistics per sphere and slice.

---

## Usage Instructions

### Requirements

- Python 3.8+
- Packages: `numpy`, `pandas`, `matplotlib`, `pydicom`, `Pillow`, `tkinter`, `openpyxl`

Install dependencies (if needed):
```sh
pip install numpy pandas matplotlib pydicom Pillow openpyxl
```

### Running the Script

1. Place your DICOM image folder (containing all slices) at a known location.
2. Edit the script at the top to set:
   - `folder_path`: Path to your DICOM folder.
   - Output directory and file names (optional).
   - Sphere diameters (if not using defaults).
3. Run the script:
   ```sh
   python 3d_coordinates_with_sphere_midpoint.py
   ```
4. A window will appear, showing the center slice.
5. Scroll to navigate slices; click once per sphere to mark its center.
6. When all required clicks are made, the script closes the window and processes the data.
7. Results (images and Excel files) are saved in the output directory.

---

## Output Files

- **output_images/**: PNG images of slices with target spheres annotated.
- **outputMetaTargets.xlsx**: Per-slice and per-sphere statistics.
- **outputMidPoints3D.xlsx**: 3D optimization summary for each sphere.
- **...targets.xlsx**: Raw pixel data for each region.

---

## Customization

- Adjust the number of spheres, diameters, or pixel spacing by editing the corresponding arrays/variables.
- Modify the optimization range or region extraction logic as needed for your specific imaging scenario.

---

## Notes

- Always verify that your clicks are as close as possible to the actual sphere centers for best results.
- For large scans or many spheres, processing may take several minutes.

---

## Contact

For questions or improvements, please open an issue or pull request on this repository.

