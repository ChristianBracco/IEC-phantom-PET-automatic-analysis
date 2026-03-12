
# `background_sphere.py` - Background Sphere for NEMA Phantom

This script provides an interactive tool for selecting and analyzing the background sphere region in a stack of DICOM PET images, commonly used for NEMA phantom studies. It allows a user to select the midpoint of the background sphere in a series of PET images, extracts circular regions across slices, and computes pixel statistics, saving the results and images for further quantitative analysis.

## Features

- **DICOM Loading:** Loads and sorts DICOM image slices from a user-specified folder.
- **Interactive GUI:** Lets the user select the midpoint of the background sphere in any slice.
- **Circular Mask Extraction:** Extracts pixels within a circular region around the user-selected midpoint across multiple slices.
- **Statistics Calculation:** Computes mean, max, variance, and count of pixels per slice and for the whole sphere.
- **Visualization:** Saves annotated images with the circular region overlaid.
- **Excel Output:** Saves per-slice and per-sphere statistics to an Excel file for further analysis.

## Dependencies

- Python 3.x
- `numpy`
- `pandas`
- `pydicom`
- `tkinter`
- `matplotlib`
- `Pillow`
- `openpyxl`

Install dependencies with:

```bash
pip install numpy pandas pydicom matplotlib pillow openpyxl
```

(`tkinter` is usually included with Python.)

## Usage

1. **Update User Settings:**  
   At the start of the `main()` function, set the following variables as needed:
   - `folder_path`: Path to the folder containing your DICOM images.
   - `OF`, `Ampl`, `TBR`: Output folder naming parameters (customize as needed).

2. **Run the Script:**

   ```bash
   python background_sphere.py
   ```

3. **Interact with the GUI:**  
   - An image viewer window will appear.
   - Scroll to navigate through slices.
   - Click on the midpoint of the background sphere.
   - The script will process the region and save results.

4. **Outputs:**  
   - Annotated images are saved in a folder like `PET_<OF>_<Ampl>_<TBR>/BG_output_images/`.
   - Per-slice and summary statistics are saved in `PET_<OF>_<Ampl>_<TBR>/outputMetaBackground.xlsx`.

## File Outputs

- **outputMetaBackground.xlsx**  
  - `Meta data per slice`: Statistics for the background region in each slice.
  - `Meta data per sphere`: Summary statistics for the background sphere.

- **BG_output_images/**  
  - PNG images of each slice with the analyzed circle overlaid.

## Notes

- The default initial slice for selection is set as `initial_slice = 55`. Adjust as appropriate for your dataset.
- The circular region diameter is set based on the second entry in `diams` (default 37 mm).
- Ensure your DICOM files are in the specified folder before running the script.

## License

See repository license.

