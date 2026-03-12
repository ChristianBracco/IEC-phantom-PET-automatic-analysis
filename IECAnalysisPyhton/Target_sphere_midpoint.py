import os
import math
from pathlib import Path

import numpy as np
import pydicom
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd
import tkinter as tk
from PIL import Image, ImageTk

# ---------------------- DICOM Handling ---------------------- #

def read_dicom_folder(folder_path):
    """
    Reads all DICOM files in a folder and returns sorted image arrays and metadata.
    """
    files = sorted(os.listdir(folder_path))
    image_order = []
    image_info = []
    rescaled_images = []

    for file in files:
        image_location = os.path.join(folder_path, file)
        ds = pydicom.dcmread(image_location)
        rescale_slope = ds.RescaleSlope
        rescale_intercept = ds.RescaleIntercept
        slice_location = ds.SliceLocation
        image = ds.pixel_array.astype(np.float64)
        image_rescaled = image * rescale_slope + rescale_intercept

        image_order.append(slice_location)
        rescaled_images.append(image_rescaled)
        image_info.append({
            'RescaleSlope': rescale_slope,
            'RescaleIntercept': rescale_intercept,
            'order': slice_location
        })

    # Sort images and metadata by slice location
    sorted_indices = np.argsort(image_order)
    images_sorted = [rescaled_images[i] for i in sorted_indices]
    info_sorted = [image_info[i] for i in sorted_indices]
    return images_sorted, info_sorted

def find_center_slice(images):
    """
    Returns the index and image of the slice with the highest mean intensity.
    """
    mean_values = [np.mean(image) for image in images]
    max_index = np.argmax(mean_values)
    return max_index, images[max_index]

def circular_mask(array, center_y, center_x, radius):
    """
    Returns a mask and the array values within a circle at (center_x, center_y) with given radius.
    """
    X, Y = np.ogrid[:array.shape[0], :array.shape[1]]
    dist_from_center = np.sqrt((X - center_x) ** 2 + (Y - center_y) ** 2)
    mask = dist_from_center <= radius
    circular_region = np.where(mask, array, np.nan)
    circular_pixels = array[mask]
    return circular_region, circular_pixels

def circular_pixels(image, center_x, center_y, diam, pixelspacing, is_cylinder, nrslices, slice_idx, slice_thickness):
    """
    Returns the matplotlib circle patch, dataframe of circular pixels, numpy array of pixels, and the circle radius in pixels.
    """
    radius_mm = diam / 2
    if is_cylinder:
        radius_px = radius_mm / pixelspacing
    elif radius_mm ** 2 > ((nrslices / 2 - slice_idx) * slice_thickness) ** 2:
        radius_px = math.sqrt(radius_mm ** 2 - ((nrslices / 2 - slice_idx) * slice_thickness) ** 2) / pixelspacing
    else:
        radius_px = 0

    circle_patch = Circle((center_y, center_x), radius_px, fill=False, edgecolor='red', linewidth=1)
    circular_region, circular_pixels_arr = circular_mask(image, center_y, center_x, radius_px)
    df_circular_region = pd.DataFrame(circular_region)
    return circle_patch, df_circular_region, circular_pixels_arr, radius_px

def find_midpoint_3d(images, center_x, center_y, center_z, diam, pixelspacing, z_range):
    """
    Optimizes the (x, y, z) midpoint location for a target sphere based on local mean intensity.
    """
    offsets = 5  # Range of pixels to search around initial guess
    nrslices = round(diam / 2)
    slice_thickness = 2  # This should be parameterized if needed
    candidate_midpoints = []
    mean_intensities = []
    stats_records = []

    for z in range(center_z - z_range, center_z + z_range):
        for dx in range(-offsets, offsets):
            for dy in range(-offsets, offsets):
                x = center_x + dx
                y = center_y + dy
                sphere_pixels = []
                start_slice = int(z - (nrslices / 2))
                end_slice = int(z + (nrslices / 2))
                for slice_nr in range(start_slice, end_slice + 1):
                    if 0 <= slice_nr < len(images):
                        _, _, circular_pixels_arr, _ = circular_pixels(
                            images[slice_nr], x, y, diam, pixelspacing,
                            is_cylinder=False, nrslices=nrslices,
                            slice_idx=slice_nr - start_slice,
                            slice_thickness=slice_thickness
                        )
                        sphere_pixels.extend(circular_pixels_arr)
                if sphere_pixels:
                    mean_val = np.mean(sphere_pixels)
                    max_val = np.max(sphere_pixels)
                else:
                    mean_val = max_val = np.nan
                candidate_midpoints.append((x, y, z))
                mean_intensities.append(mean_val)
                stats_records.append({
                    'MidPoint x': x,
                    'MidPoint y': y,
                    'MidPoint z': z,
                    'Mean': mean_val,
                    'Max': max_val
                })

    best_idx = int(np.nanargmax(mean_intensities))
    center_x_opt, center_y_opt, center_z_opt = candidate_midpoints[best_idx]
    df_stats = pd.DataFrame(stats_records)
    return center_x_opt, center_y_opt, center_z_opt, df_stats

# ---------------------- GUI for User Input ---------------------- #

class ClickCapture:
    """
    Simple GUI for displaying slices and recording user click coordinates.
    """
    def __init__(self, images, center_slice):
        self.coordinates = []
        self.images = images
        self.current_slice = center_slice
        self.slice_count = len(images)

        # Global min/max for consistent display
        self.global_min = np.min([np.min(image) for image in images])
        self.global_max = np.max([np.max(image) for image in images])

        self.root = tk.Tk()
        self.root.title("Click on the image to guess the midpoints of target spheres (scroll to change slice)")

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack()

        self.label = tk.Label(self.main_frame)
        self.label.pack(side=tk.LEFT)

        self.slice_label = tk.Label(self.root, text=f"Slice: {self.current_slice + 1}/{self.slice_count}")
        self.slice_label.pack(side=tk.BOTTOM)

        self.colorbar_legend = self.create_colorbar_legend()
        self.colorbar_legend.pack(side=tk.RIGHT, fill=tk.Y)

        self.update_image()
        self.label.bind("<Button-1>", self.on_click)
        self.root.bind("<MouseWheel>", self.on_mousewheel)

    def create_colorbar_legend(self):
        legend_frame = tk.Frame(self.main_frame)
        canvas = tk.Canvas(legend_frame, width=50, height=256)
        canvas.pack()
        max_label = tk.Label(legend_frame, text=f"{self.global_max:.2f}")
        max_label.pack(side=tk.TOP)
        for i in range(256):
            color = int(i)
            canvas.create_line(0, 255 - i, 50, 255 - i, fill=f'#{color:02x}{color:02x}{color:02x}')
        min_label = tk.Label(legend_frame, text=f"{self.global_min:.2f}")
        min_label.pack(side=tk.BOTTOM)
        return legend_frame

    def update_image(self):
        img = self.images[self.current_slice]
        normalized_image = (img - self.global_min) / (self.global_max - self.global_min) * 255
        image = Image.fromarray(normalized_image.astype(np.uint8), mode='L')
        self.tk_image = ImageTk.PhotoImage(image)
        self.label.config(image=self.tk_image)
        self.slice_label.config(text=f"Slice: {self.current_slice + 1}/{self.slice_count}")

    def next_slice(self, event=None):
        if self.current_slice < self.slice_count - 1:
            self.current_slice += 1
            self.update_image()

    def prev_slice(self, event=None):
        if self.current_slice > 0:
            self.current_slice -= 1
            self.update_image()

    def on_mousewheel(self, event):
        if event.delta > 0:
            self.prev_slice()
        else:
            self.next_slice()

    def on_click(self, event):
        z = self.current_slice
        self.coordinates.append((event.x, event.y, z))
        print(f"Clicked at: ({event.x}, {event.y}, {z})")
        if len(self.coordinates) == 6:
            print(f"Six clicks recorded: {self.coordinates}")
            self.root.quit()

    def get_coordinates(self):
        self.root.mainloop()
        return self.coordinates

# ---------------------- Main Pipeline ---------------------- #

def main():
    # --------- User Input (Edit Here) ---------
    folder_path = 'D:/IEC_PET_CT_PHILIPS/pet'
    output_folder_prefix = 'D:/IECAnalysisPyhton/FolderPrefix'
    output_excel_name = f"{output_folder_prefix}/ExcelName.xlsx"
    output_midpoints_name = f"{output_folder_prefix}/outputMidPoints.xlsx"
    output_meta_name = f"{output_folder_prefix}/outputMetaTargets.xlsx"
    output_images_dir = f"{output_folder_prefix}/output_images"
    Path(output_folder_prefix).mkdir(parents=True, exist_ok=True)
    Path(output_images_dir).mkdir(parents=True, exist_ok=True)
    # ------------------------------------------

    images, image_info = read_dicom_folder(folder_path)
    center_slice, _ = find_center_slice(images)
    print(f'Center slice is {center_slice}')

    # User selects sphere midpoints
    click_capture = ClickCapture(images, center_slice)
    coordinates = click_capture.get_coordinates()

    # Sphere settings
    diameters = [37, 37, 28, 22, 17, 13, 10]  # mm
    pixelspacing = 4  # mm
    slice_thickness = 4  # mm
    spheres = ["B0", "B1", "B2", "B3", "B4", "B5", "B6"]
    n_spheres = 6  # Adjust if needed

    # Refine midpoints in x,y,z for each sphere
    midpoints = []
    stats_dfs = []
    for isphere in range(n_spheres):
        diam = diameters[isphere + 1]
        center_y, center_x, z_slice = coordinates[isphere]
        center_x, center_y, center_z, df_stats = find_midpoint_3d(
            images, center_x, center_y, z_slice, diam, pixelspacing, z_range=2
        )
        midpoints.append((center_y, center_x, center_z))
        stats_dfs.append(df_stats)
        df_stats.to_excel(output_midpoints_name, sheet_name=f'B0{isphere + 1}', engine='openpyxl')

    # Collect pixel values for all spheres and slices, and create visualizations
    all_mean_max_stats = []
    all_pixels_per_sphere = [[] for _ in range(n_spheres)]
    global_min = np.min([np.min(image) for image in images])
    global_max = np.max([np.max(image) for image in images])

    for slice_nr in range(center_slice - 10, center_slice + 11):
        array_i = images[slice_nr]
        fig, ax = plt.subplots()
        im = ax.imshow(array_i, cmap='gray', vmin=global_min, vmax=global_max)
        circles_added = False

        for isphere in range(n_spheres):
            diam = diameters[isphere + 1]
            center_y, center_x, z_slice = midpoints[isphere]
            nrslices = round(diam / slice_thickness)
            start_slice = int(z_slice - (nrslices / 2))
            end_slice = int(z_slice + (nrslices / 2))

            if start_slice <= slice_nr <= end_slice:
                circle_patch, df_circular_region, circular_pixels_arr, radius_px = circular_pixels(
                    array_i, center_x, center_y, diam, pixelspacing,
                    is_cylinder=False, nrslices=nrslices,
                    slice_idx=slice_nr - start_slice,
                    slice_thickness=slice_thickness
                )
                if radius_px > 0:
                    ax.add_patch(circle_patch)
                    circles_added = True
                all_pixels_per_sphere[isphere].extend(circular_pixels_arr.flatten())
                all_mean_max_stats.append({
                    'Slice NR': slice_nr,
                    'Mean': np.mean(circular_pixels_arr),
                    'Max': np.max(circular_pixels_arr),
                    'Nr Pixels': circular_pixels_arr.size,
                    'Radius [mm]': radius_px * pixelspacing,
                    'Sphere': isphere
                })
                # Save masked region to Excel
                excel_exists = os.path.exists(output_excel_name)
                mode = 'a' if excel_exists else 'w'
                df_circular_region = df_circular_region.dropna(how='all').dropna(how='all', axis=1)
                with pd.ExcelWriter(output_excel_name, engine='openpyxl', mode=mode) as writer:
                    df_circular_region.to_excel(writer, sheet_name=f'Slice{slice_nr}_B0{isphere + 1}')

        if circles_added:
            plt.colorbar(im, orientation='vertical', label='Pixel Value [Bq/mL]')
            plt.title(f'Slice NR = {slice_nr}')
            plt.savefig(f'{output_images_dir}/slice_{slice_nr}.png')
            plt.close(fig)

    # Save pixel statistics and metadata
    mean_max_df = pd.DataFrame(all_mean_max_stats)
    mean_max_df.to_excel(output_meta_name, sheet_name='Meta data per slice', engine='openpyxl')

    # Per-sphere summary
    meta_per_sphere = []
    with pd.ExcelWriter(output_meta_name, engine='openpyxl', mode='a') as writer:
        for i, pixels in enumerate(all_pixels_per_sphere):
            sphere_name = f'B{i+1}'
            if pixels:
                meta_per_sphere.append({
                    'Sphere': sphere_name,
                    'Max': np.max(pixels),
                    'Mean': np.mean(pixels),
                    'Variance': np.var(pixels),
                    'Nr Pixels': len(pixels)
                })
            else:
                meta_per_sphere.append({
                    'Sphere': sphere_name,
                    'Max': None,
                    'Mean': None,
                    'Variance': None,
                    'Nr Pixels': 0
                })
            pd.DataFrame(pixels, columns=[f'Pixel Value {sphere_name}']).to_excel(writer, sheet_name=f'All Pixels {sphere_name}')
        pd.DataFrame(meta_per_sphere).to_excel(writer, sheet_name='Meta data per sphere')

    print("All pixel data and statistics have been saved.")
    print(f"Final coordinates: {midpoints}")

if __name__ == '__main__':
    main()
