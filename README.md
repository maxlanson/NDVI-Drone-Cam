# NDVI viewer

This version separates NDVI processing from the interactive viewer and uses
OpenCV's built-in `COLORMAP_TURBO` instead of a manually maintained color table.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python ndvi_app.py path/to/image.jpg
```

Drag over a region in the image to print its mean NDVI. Press `Esc` or `q` to
close the viewer.

The original script used the blue channel as a stand-in for near-infrared. That
can be useful for experimenting with ordinary RGB photos, but it is not true
NDVI. For meaningful measurements, provide imagery with a real NIR channel and
adjust the channel mapping in `calculate_ndvi`.