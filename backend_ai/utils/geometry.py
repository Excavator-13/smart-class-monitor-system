from __future__ import annotations

import math
from typing import Iterable, Sequence, Tuple

Point = Tuple[float, float]
BBox = Sequence[float]


def normalize_point(point: Point, width: int, height: int) -> Point:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return point[0] / width, point[1] / height


def denormalize_point(point: Point, width: int, height: int) -> Point:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return point[0] * width, point[1] * height


def bbox_foot_point(bbox: BBox, normalized: bool = False, width: int | None = None, height: int | None = None) -> Point:
    if len(bbox) != 4:
        raise ValueError("bbox must contain [x1, y1, x2, y2]")
    x1, _y1, x2, y2 = [float(v) for v in bbox]
    foot = ((x1 + x2) / 2.0, y2)
    if normalized:
        if width is None or height is None:
            raise ValueError("width and height are required when normalized=True")
        return normalize_point(foot, width, height)
    return foot


def point_in_polygon(point: Point, polygon: Iterable[Point]) -> bool:
    pts = list(polygon)
    if len(pts) < 3:
        return False

    x, y = point
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        on_vertical_span = (yi > y) != (yj > y)
        if on_vertical_span:
            x_intersect = (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi
            if x <= x_intersect:
                inside = not inside
        j = i
    return inside


def distance_point_to_segment(point: Point, start: Point, end: Point) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    if dx == 0 and dy == 0:
        return math.hypot(px - sx, py - sy)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
    nearest = (sx + t * dx, sy + t * dy)
    return math.hypot(px - nearest[0], py - nearest[1])


def distance_point_to_polygon(point: Point, polygon: Iterable[Point]) -> float:
    pts = list(polygon)
    if len(pts) < 2:
        return math.inf
    distances = []
    for idx, start in enumerate(pts):
        end = pts[(idx + 1) % len(pts)]
        distances.append(distance_point_to_segment(point, start, end))
    return min(distances)


def parse_polygon_coordinates(coordinates: Iterable[dict | Sequence[float]]) -> list[Point]:
    points: list[Point] = []
    for item in coordinates:
        if isinstance(item, dict):
            points.append((float(item["x"]), float(item["y"])))
        else:
            points.append((float(item[0]), float(item[1])))
    return points

