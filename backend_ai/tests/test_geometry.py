from backend_ai.utils.geometry import (
    bbox_foot_point,
    distance_point_to_polygon,
    normalize_point,
    parse_polygon_coordinates,
    point_in_polygon,
)


def test_point_in_polygon_and_outside():
    polygon = [(0.1, 0.1), (0.5, 0.1), (0.5, 0.5), (0.1, 0.5)]

    assert point_in_polygon((0.2, 0.2), polygon)
    assert not point_in_polygon((0.8, 0.8), polygon)


def test_distance_point_to_polygon_edge():
    polygon = [(0.1, 0.1), (0.5, 0.1), (0.5, 0.5), (0.1, 0.5)]

    assert round(distance_point_to_polygon((0.55, 0.3), polygon), 2) == 0.05


def test_normalize_and_bbox_foot_point():
    assert normalize_point((320, 180), 640, 360) == (0.5, 0.5)
    assert bbox_foot_point([10, 20, 30, 60]) == (20, 60)


def test_parse_polygon_coordinates_from_dicts():
    points = parse_polygon_coordinates([{"x": "0.1", "y": "0.2"}, {"x": 0.3, "y": 0.4}])

    assert points == [(0.1, 0.2), (0.3, 0.4)]

