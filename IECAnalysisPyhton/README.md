# VOI Identification Tools for PET-CT Phantom Study

This repository contains the tools and scripts used to support the research paper:

> "Effect of data-driven motion correction for respiratory movement on lesion detectability in PET-CT: a phantom study"
> 
> Submitted to European Journal of Nuclear Medicine and Imaging - Physics (EJNMI - Physics)

## Overview

This toolkit provides two complementary Python scripts for analyzing PET-CT phantom images, specifically designed for NEMA phantom studies focusing on lesion detectability and quantification. The tools enable precise identification and analysis of both target spheres and background regions in PET-CT images.

### Components

1. [Target Sphere Analysis](README%20target%20spheres.md) (`Target_sphere_midpoint.py`)
   - Enables 3D coordinate identification of multiple target spheres
   - Provides interactive midpoint selection and optimization
   - Computes metrics of sphere regions
   - Generates comprehensive visualization and data outputs

2. [Background Sphere Analysis](README%20background%20sphere.md) (`background_sphere.py`)
   - Facilitates background region selection and analysis
   - Implements interactive GUI for precise midpoint selection
   - Computes metrics for background region
   - Produces detailed per-slice and aggregate statistics

## Key Features

- **DICOM Processing**: Both tools support direct DICOM image processing
- **Interactive GUI**: User-friendly interfaces for precise region selection
- **Automated Analysis**: Statistical computation and data extraction
- **Comprehensive Output**: Excel-based statistics and annotated visualizations
- **Research-Grade Tools**: Designed for academic and clinical research purposes

## Getting Started

1. Review the detailed documentation for each component:
   - [Target Spheres Documentation](README%20target%20spheres.md)
   - [Background Sphere Documentation](README%20background%20sphere.md)

2. Install the required dependencies as specified in each component's README

3. Follow the usage instructions for each tool depending on your analysis needs

## Dependencies

Both scripts require Python 3.7 and the following packages:
- numpy
- pandas
- pydicom
- tkinter
- matplotlib
- Pillow
- openpyxl

Install all dependencies with:

```bash
pip install numpy pandas pydicom matplotlib pillow openpyxl
```

## Citation

If you use these tools in your research, please cite our paper (citation details to be added upon publication).

## License

This project is licensed under the terms included in the [LICENSE](LICENSE) file.

## Contact

For questions about the tools or the associated research paper, please contact the repository maintainers or refer to the paper's corresponding author.
