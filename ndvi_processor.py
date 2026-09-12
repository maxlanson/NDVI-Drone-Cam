"""NDVI calculation and visualization helpers."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class NdviResult:
    """Images produced during the NDVI pipeline."""

    source: np.ndarray
    ndvi: np.ndarray
    display: np.ndarray


def load_image(path: str) -> np.ndarray:
    """Load an image or raise a useful error when it cannot be read."""
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not read image: {path}")
    return image


def calculate_ndvi(image: np.ndarray, nir_channel: int = 0, red_channel: int = 2) -> np.ndarray:
    """Calculate NDVI from two channels of a BGR image.

    For a normal color photograph, channel 0 is only a blue proxy, not true
    near-infrared data. Use an image with a real NIR channel for scientifically
    meaningful NDVI values.
    """
    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Expected a color image with at least three channels")

    nir = image[:, :, nir_channel].astype(np.float32)
    red = image[:, :, red_channel].astype(np.float32)
    denominator = nir + red
    return np.divide(
        nir - red,
        denominator,
        out=np.zeros_like(denominator, dtype=np.float32),
        where=denominator != 0,
    )


def normalize_ndvi(ndvi: np.ndarray) -> np.ndarray:
    """Map NDVI's normal range of -1..1 to an 8-bit display image."""
    clipped = np.clip(ndvi, -1.0, 1.0)
    return ((clipped + 1.0) * 127.5).astype(np.uint8)


def colorize_ndvi(ndvi: np.ndarray, colormap: int = cv2.COLORMAP_TURBO) -> np.ndarray:
    """Apply an OpenCV colormap instead of maintaining a hard-coded lookup table."""
    return cv2.applyColorMap(normalize_ndvi(ndvi), colormap)


def process_image(image: np.ndarray, colormap: int = cv2.COLORMAP_TURBO) -> NdviResult:
    """Calculate and colorize NDVI for an image."""
    ndvi = calculate_ndvi(image)
    return NdviResult(source=image, ndvi=ndvi, display=colorize_ndvi(ndvi, colormap))


def roi_mean(ndvi: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
    """Return the mean NDVI for a clipped rectangular region."""
    left, right = sorted((max(0, x1), min(ndvi.shape[1], x2)))
    top, bottom = sorted((max(0, y1), min(ndvi.shape[0], y2)))
    region = ndvi[top:bottom, left:right]
    if region.size == 0:
        raise ValueError("Selected region is empty")
    return float(region.mean())