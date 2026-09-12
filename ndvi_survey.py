"""WIP aerial crop-health survey pipeline.

This prototype analyzes one orthomosaic or one image at a time. It does not
stitch flight images or georeference output yet.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from ndvi_processor import calculate_ndvi, load_image


@dataclass(frozen=True)
class HealthCell:
    row: int
    column: int
    x: int
    y: int
    width: int
    height: int
    mean_ndvi: float
    health: str


@dataclass(frozen=True)
class SurveyResult:
    cells: list[HealthCell]
    healthy_percent: float
    stressed_percent: float
    average_ndvi: float


def classify_health(ndvi: float, stressed_threshold: float, healthy_threshold: float) -> str:
    """Convert an NDVI score into a transparent baseline health category."""
    if ndvi < stressed_threshold:
        return "stressed"
    if ndvi >= healthy_threshold:
        return "healthy"
    return "watch"


def analyze_grid(
    ndvi: np.ndarray,
    rows: int,
    columns: int,
    stressed_threshold: float = 0.2,
    healthy_threshold: float = 0.55,
) -> SurveyResult:
    """Score equal-sized grid cells across an NDVI image."""
    if rows < 1 or columns < 1:
        raise ValueError("rows and columns must be positive")
    if stressed_threshold >= healthy_threshold:
        raise ValueError("stressed threshold must be lower than healthy threshold")

    height, width = ndvi.shape[:2]
    cells: list[HealthCell] = []
    for row in range(rows):
        y_start, y_end = round(row * height / rows), round((row + 1) * height / rows)
        for column in range(columns):
            x_start = round(column * width / columns)
            x_end = round((column + 1) * width / columns)
            region = ndvi[y_start:y_end, x_start:x_end]
            mean_ndvi = float(region.mean())
            cells.append(
                HealthCell(
                    row=row,
                    column=column,
                    x=x_start,
                    y=y_start,
                    width=x_end - x_start,
                    height=y_end - y_start,
                    mean_ndvi=mean_ndvi,
                    health=classify_health(mean_ndvi, stressed_threshold, healthy_threshold),
                )
            )

    healthy = sum(cell.health == "healthy" for cell in cells)
    stressed = sum(cell.health == "stressed" for cell in cells)
    return SurveyResult(
        cells=cells,
        healthy_percent=100 * healthy / len(cells),
        stressed_percent=100 * stressed / len(cells),
        average_ndvi=float(ndvi.mean()),
    )


def render_health_map(
    image: np.ndarray,
    result: SurveyResult,
    stressed_threshold: float,
    healthy_threshold: float,
) -> np.ndarray:
    """Render the grid and scores over the source image."""
    output = image.copy()
    colors = {"stressed": (40, 40, 220), "watch": (0, 190, 255), "healthy": (40, 180, 40)}
    for cell in result.cells:
        color = colors[cell.health]
        top_left = (cell.x, cell.y)
        bottom_right = (cell.x + cell.width - 1, cell.y + cell.height - 1)
        cv2.rectangle(output, top_left, bottom_right, color, 2)
        cv2.putText(
            output,
            f"{cell.mean_ndvi:.2f}",
            (cell.x + 6, cell.y + 22),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    cv2.putText(
        output,
        f"red: < {stressed_threshold:.2f}  yellow: watch  green: >= {healthy_threshold:.2f}",
        (12, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return output


def write_outputs(output_dir: Path, result: SurveyResult, health_map: np.ndarray) -> None:
    """Write the visual map and machine-readable survey results."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_dir / "health_map.png"), health_map)
    with (output_dir / "health_cells.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=asdict(result.cells[0]).keys())
        writer.writeheader()
        writer.writerows(asdict(cell) for cell in result.cells)
    (output_dir / "survey_summary.json").write_text(json.dumps(asdict(result), indent=2) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a WIP crop-health map from an aerial image.")
    parser.add_argument("image", type=Path, help="Orthomosaic or aerial image path")
    parser.add_argument("--output", type=Path, default=Path("survey_output"))
    parser.add_argument("--rows", type=int, default=10)
    parser.add_argument("--columns", type=int, default=10)
    parser.add_argument("--nir-channel", type=int, default=0, help="NIR channel index in the input image")
    parser.add_argument("--red-channel", type=int, default=2, help="Red channel index in the input image")
    parser.add_argument("--stressed-threshold", type=float, default=0.2)
    parser.add_argument("--healthy-threshold", type=float, default=0.55)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image = load_image(str(args.image))
    ndvi = calculate_ndvi(image, args.nir_channel, args.red_channel)
    result = analyze_grid(ndvi, args.rows, args.columns, args.stressed_threshold, args.healthy_threshold)
    health_map = render_health_map(image, result, args.stressed_threshold, args.healthy_threshold)
    write_outputs(args.output, result, health_map)
    print(f"Average NDVI: {result.average_ndvi:.3f}")
    print(f"Healthy cells: {result.healthy_percent:.1f}%")
    print(f"Stressed cells: {result.stressed_percent:.1f}%")
    print(f"Wrote survey outputs to {args.output}")


if __name__ == "__main__":
    main()