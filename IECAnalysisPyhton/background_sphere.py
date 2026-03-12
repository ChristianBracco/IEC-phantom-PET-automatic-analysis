import os
import math
import numpy as np
import pandas as pd
import pydicom
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from pathlib import Path
from PIL import Image, ImageTk
from openpyxl import load_workbook

def read_dicom_images(folder_path):
    """Reads every DICOM image in a folder and returns structured images and metadata."""
    files = sorted(os.listdir(folder_path))
    images, meta = [], []
    slice_locations = []
    for file in files:
        ds = pydicom.dcmread(os.path.join(folder_path, file))
        image = ds.pixel_array.astype(np.float64) * ds.RescaleSlope + ds.RescaleIntercept
        images.append(image)
        slice_locations.append(ds.SliceLocation)
        meta.append({'RescaleSlope': ds.RescaleSlope, 'RescaleIntercept': ds.RescaleIntercept, 'order': ds.SliceLocation})
    sort_idx = np.argsort(slice_locations)
    images = [images[i] for i in sort_idx]
    meta = [meta[i] for i in sort_idx]
    return images, meta

def create_circular_mask(image, center_y, center_x, radius):
    """Creates a mask for a circle and returns the pixel values of this circle."""
    Y, X = np.ogrid[:image.shape[0], :image.shape[1]]
    dist = np.sqrt((X - center_x) ** 2 + (Y - center_y) ** 2)
    mask = dist <= radius
    circular_region = np.where(mask, image, np.nan)
    pixels = image[mask]
    return circular_region, pixels

class ClickCapture:
    """Class to click the midpoint of a slice with a GUI."""
    def __init__(self, images, initial_slice):
        self.images = images
        self.current_slice = initial_slice
        self.slice_count = len(images)
        self.global_min = np.min([np.min(img) for img in images])
        self.global_max = np.max([np.max(img) for img in images])
        self.coordinates = []
        self._build_gui()

    def _build_gui(self):
        self.root = tk.Tk()
        self.root.title("Select the midpoint of your background sphere, scroll for next slices.")
        self.label = tk.Label(self.root)
        self.label.pack(side=tk.LEFT)
        self.slice_label = tk.Label(self.root, text=f"Slice: {self.current_slice + 1}/{self.slice_count}")
        self.slice_label.pack(side=tk.BOTTOM)
        self._update_image()
        self.label.bind("<Button-1>", self._on_click)
        self.root.bind("<MouseWheel>", self._on_mousewheel)

    def _update_image(self):
        norm_img = ((self.images[self.current_slice] - self.global_min) /
                    (self.global_max - self.global_min) * 255).astype(np.uint8)
        img = Image.fromarray(norm_img, mode='L')
        tk_img = ImageTk.PhotoImage(img)
        self.label.config(image=tk_img)
        self.label.image = tk_img  
        self.slice_label.config(text=f"Slice: {self.current_slice + 1}/{self.slice_count}")

    def _on_mousewheel(self, event):
        if event.delta > 0 and self.current_slice > 0:
            self.current_slice -= 1
        elif event.delta < 0 and self.current_slice < self.slice_count - 1:
            self.current_slice += 1
        self._update_image()

    def _on_click(self, event):
        self.coordinates.append((event.x, event.y, self.current_slice))
        print(f"Clicked on: ({event.x}, {event.y}, slice {self.current_slice})")
        self.root.quit()

    def get_coordinates(self):
        self.root.mainloop()
        return self.coordinates

def calculate_circle_pixels(image, center_x, center_y, diameter, pixel_spacing, total_slices, slice_idx, slice_thickness):
    """Calculates the pixels within a circle on a slice."""
    radius = diameter / 2
    z_dist = (total_slices / 2 - slice_idx) * slice_thickness
    pixel_radius = math.sqrt(radius ** 2 - z_dist ** 2) / pixel_spacing if radius ** 2 > z_dist ** 2 else 0
    circle_patch = Circle((center_y, center_x), pixel_radius, fill=False, edgecolor='red', linewidth=1)
    circular_region, pixels = create_circular_mask(image, center_y, center_x, pixel_radius)
    return circle_patch, pd.DataFrame(circular_region), pixels, pixel_radius

def main():
    # User settings
    folder_path = 'D:/IEC_PET_CT_PHILIPS/pet'
    OF, Ampl, TBR = 'OF', 'A10', 'T5'
    pixel_spacing, slice_thickness = 4 , 4
    diams = [37, 37, 28, 22, 17, 13, 10]
    output_dir = f'PET_{OF}_{Ampl}_{TBR}/BG_output_images'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    filepath = f'PET_{OF}_{Ampl}_{TBR}/'
    Path(filepath).mkdir(parents=True, exist_ok=True)

    images, _ = read_dicom_images(folder_path)
    initial_slice = 55
    click_capture = ClickCapture(images, initial_slice)
    [(center_y, center_x, z)] = click_capture.get_coordinates()
    nrslices = round(diams[1] / slice_thickness)
    start_slice = int(z - nrslices / 2)
    pd_B0, pd_mean_max = [], []
    global_min, global_max = np.min([np.min(img) for img in images]), np.max([np.max(img) for img in images])

    for islice in range(nrslices+1):
        slice_nr = start_slice + islice
        array_i = images[slice_nr]
        fig, ax = plt.subplots()
        im = ax.imshow(array_i, cmap='gray', vmin=global_min, vmax=global_max)
        diam = diams[1]
        circle, _, pixels, pixel_radius = calculate_circle_pixels(
            array_i, center_x, center_y, diam, pixel_spacing, nrslices, islice, slice_thickness)
        if pixel_radius > 0:
            ax.add_patch(circle)
            plt.colorbar(im, orientation='vertical', label='Pixel Value [Bq/mL]')
            plt.title(f'Slice NR = {slice_nr}')
            plt.savefig(f'{output_dir}/slice_{slice_nr}.png')
            plt.close()
            pd_B0.extend(pixels.flatten().tolist())
            pd_mean_max.append({
                'Slice NR': slice_nr, 'Mean': np.mean(pixels), 'Max': np.max(pixels),
                'Nr Pixels': np.size(pixels), 'Radius [mm]': pixel_radius * pixel_spacing, 'Sphere': 0
            })

    mean_max_sphere = [{
        'Sphere': "B0",
        'Max': np.max(pd_B0),
        'Mean': np.mean(pd_B0),
        'Variance': np.var(pd_B0),
        'Nr Pixels': np.size(pd_B0)
    }]

    # Save to Excel
    with pd.ExcelWriter(filepath + 'outputMetaBackground.xlsx', engine='openpyxl') as writer:
        pd.DataFrame(pd_mean_max).to_excel(writer, sheet_name='Meta data per slice')
        pd.DataFrame(mean_max_sphere).to_excel(writer, sheet_name='Meta data per sphere')

    print("Circular region pixel data has been saved to outputMetaBackground.xlsx")

if __name__ == "__main__":
    main()
