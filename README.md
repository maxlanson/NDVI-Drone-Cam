# NDVI viewer

This version separates NDVI processing from the interactive viewer. Latest Ver. uses
OpenCV's built-in `COLORMAP_TURBO` instead of some random hard-coded variable I once used.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python ndvi_app.py path/to/image.jpg
```

Drag over a region in the image to print its mean NDVI. Press `Esc` or `q` to

## WIP aerial survey

`ndvi_survey.py` is an early crop-health mapping prototype. It divides one
drone orthomosaic or aerial image into a grid, classifies each cell as
`healthy`, `watch`, or `stressed`, and writes:

- `health_map.png` with colored grid cells and NDVI scores
- `health_cells.csv` with one row per grid cell
- `survey_summary.json` with field-level percentages and average NDVI

Run it with:

```bash
python ndvi_survey.py path/to/orthomosaic.tif --output survey_output
```

The default thresholds are NDVI `< 0.20` for stressed and `>= 0.55` for
healthy. Adjust them with `--stressed-threshold` and `--healthy-threshold`.
The default channel mapping follows the existing prototype (`--nir-channel 0`
and `--red-channel 2`); replace it with the actual channel layout of the
camera. This WIP does not yet stitch individual flight photos, read GPS/IMU
metadata, create GeoTIFFs, or use a trained crop model. Those are required
before treating the output as an agronomic or geographically accurate map.
close the viewer.

The original script used the blue channel as a stand-in for near-infrared. That
can be useful for experimenting with ordinary RGB photos, but it is not true
NDVI, unless you set the proper filters on the camera. For meaningful measurements, provide imagery with a real NIR channel and
adjust the channel mapping in `calculate_ndvi`.
