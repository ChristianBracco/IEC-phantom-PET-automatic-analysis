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

# ============================================================
# DICOM
# ============================================================

def read_dicom_images(folder_path):
    files = sorted(os.listdir(folder_path))
    images, slice_locations = [], []

    for f in files:
        ds = pydicom.dcmread(os.path.join(folder_path, f))
        img = ds.pixel_array.astype(np.float64) * ds.RescaleSlope + ds.RescaleIntercept
        images.append(img)
        slice_locations.append(ds.SliceLocation)

    order = np.argsort(slice_locations)
    return [images[i] for i in order]

def find_center_slice(images):
    return int(np.argmax([np.mean(im) for im in images]))

# ============================================================
# ROI
# ============================================================

def circular_mask(image, center_y, center_x, radius_px):
    Y, X = np.ogrid[:image.shape[0], :image.shape[1]]
    dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    mask = dist <= radius_px
    return np.where(mask, image, np.nan), image[mask]

# ============================================================
# GUI – 12 CLICK
# ============================================================

class ClickCapture:
    def __init__(self, image):
        self.image = image
        self.coords = []

        self.root = tk.Tk()
        self.root.title("Click 12 TARGET disks (same slice)")

        norm = (image - image.min()) / (image.max() - image.min()) * 255
        img = Image.fromarray(norm.astype(np.uint8), mode="L")
        self.tk_img = ImageTk.PhotoImage(img)

        self.label = tk.Label(self.root, image=self.tk_img)
        self.label.pack()
        self.label.bind("<Button-1>", self._onclick)

    def _onclick(self, event):
        self.coords.append((event.x, event.y))
        print(f"Click {len(self.coords)} → x={event.x}, y={event.y}")
        if len(self.coords) == 12:
            self.root.quit()

    def get(self):
        self.root.mainloop()
        return self.coords
# ============================================================
# GUI – 12 CLICK ROI preview
# ============================================================        

def interactive_roi_selector(image, radius_px, n_rois=12):

    centers = []
    fig, ax = plt.subplots()
    ax.imshow(image, cmap='gray')
    ax.set_title("Move mouse to preview ROI – click to fix (12 total)")

    preview_circle = Circle((0, 0), radius_px,
                            fill=False, edgecolor='yellow', linewidth=1)
    ax.add_patch(preview_circle)



    def on_move(event):
        if event.inaxes != ax:
            return
        preview_circle.center = (event.xdata, event.ydata)
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax:
            return

        cx, cy = event.xdata, event.ydata
       centers.append((int(round(cx)), int(round(cy))))

        circle = Circle((cx, cy), radius_px,
                        fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(circle)
        fixed_circles.append(circle)

        print(f"ROI {len(centers)} fixed at x={int(cx)}, y={int(cy)}")

        if len(centers) == n_rois:
            fig.canvas.mpl_disconnect(cid_move)
            fig.canvas.mpl_disconnect(cid_click)
            plt.close(fig)

        fig.canvas.draw_idle()

    cid_move = fig.canvas.mpl_connect('motion_notify_event', on_move)
    cid_click = fig.canvas.mpl_connect('button_press_event', on_click)

    plt.show()
    return centers




# ============================================================
# MAIN
# ============================================================

def main():

    # ---------- USER SETTINGS (identici al background) ----------
    folder_path = 'D:/IEC_PET_CT_PHILIPS/pet'
    OF, Ampl, TBR = 'OF', 'A10', 'T5'
    pixel_spacing = 4.0           # mm
    disk_diameter = 37.0          # mm
    # -----------------------------------------------------------

    base_path = Path(f'PET_{OF}_{Ampl}_{TBR}')
    img_path  = base_path / 'TARGET_output_images'
    base_path.mkdir(exist_ok=True)
    img_path.mkdir(exist_ok=True)

    excel_roi = base_path / 'outputTargetROIs.xlsx'
    excel_meta = base_path / 'outputMetaTargets.xlsx'

    # SOVRASCRITTURA FORZATA
    for f in [excel_roi, excel_meta]:
        if f.exists():
            f.unlink()

    images = read_dicom_images(folder_path)
    slice_idx = find_center_slice(images)
    image = images[slice_idx]

    print(f"Slice utilizzata: {slice_idx}")

    # ---- CLICK ----

    radius_px = (disk_diameter / 2) / pixel_spacing
    
    centers = interactive_roi_selector(
    image=image,
    radius_px=radius_px,
    n_rois=12
)

    global_min, global_max = image.min(), image.max()

    fig, ax = plt.subplots()
    im = ax.imshow(image, cmap='gray', vmin=global_min, vmax=global_max)

    meta_slice = []
    meta_disk = []

    for i, (cx, cy) in enumerate(centers):

        roi_img, pixels = circular_mask(image, cy, cx, radius_px)
        ax.add_patch(Circle((cx, cy), radius_px, fill=False, edgecolor='red'))

        meta_slice.append({
            'Slice NR': slice_idx,
            'Mean': np.mean(pixels),
            'Max': np.max(pixels),
            'Nr Pixels': pixels.size,
            'Radius [mm]': disk_diameter / 2,
            'Sphere': f'T{i+1}'
        })

        meta_disk.append({
            'Sphere': f'T{i+1}',
            'Max': np.max(pixels),
            'Mean': np.mean(pixels),
            'Variance': np.var(pixels),
            'Nr Pixels': pixels.size
        })

        df_roi = pd.DataFrame(roi_img).dropna(how='all').dropna(how='all', axis=1)
        with pd.ExcelWriter(excel_roi, engine='openpyxl',
                            mode='a' if excel_roi.exists() else 'w') as writer:
            df_roi.to_excel(writer, sheet_name=f'T{i+1}')

    plt.colorbar(im, orientation='vertical', label='Pixel Value [Bq/mL]')
    plt.title(f'TARGET IEC – Slice {slice_idx}')
    plt.savefig(img_path / f'slice_{slice_idx}_TARGET.png', dpi=300)
    plt.close()

    # --------- EXCEL META (stesso schema background) ---------
    with pd.ExcelWriter(excel_meta, engine='openpyxl') as writer:
        pd.DataFrame(meta_slice).to_excel(writer, sheet_name='Meta data per slice', index=False)
        pd.DataFrame(meta_disk).to_excel(writer, sheet_name='Meta data per sphere', index=False)

    print("✔ TARGET 2D analysis completata")
    print(f"File generati in: {base_path}")

if __name__ == "__main__":
    main()
