"""
空間検索の材料にする為のPolygonを作成する。
1. directional_rectangle
   ベース地点からある方向に向かって長方形のバッファーを作成する。
2.  directional_fan
    ベース地点から扇状のPolygonを作成する。空港の侵入方向等に使用。

"""

import math

import shapely


def _to_point(base_point, distance, angle) -> shapely.geometry.Point:
    # 距離と方向から新しいPointObjectを作成する
    angle_rad = math.radians(angle)
    x = base_point.x + distance * math.sin(angle_rad)
    y = base_point.y + distance * math.cos(angle_rad)
    destination = (x, y)
    return shapely.geometry.Point(destination)


def directional_rectangle(
    base_point: shapely.geometry.Point, 
    distance: int, 
    angle: float, 
    width: float
) -> shapely.geometry.Polygon:
    """
    ベース地点からある方向に向かって長方形のバッファーを作成する。\n
    Args:
        base_point(shapely.geometry.Point):
        distance(int): 長方形の高さ
        angle(float): 長方形を作成する方位
        width(float): 長方形の幅
    Returns:
        shapely.geometry.Polygon
    """
    trg_point = _to_point(base_point, distance, angle)
    line = shapely.geometry.LineString([base_point, trg_point])
    rectangles = line.buffer(width, cap_style='flat')
    return rectangles


def directional_fan(
    base_point: shapely.geometry.Point, 
    distance: int, 
    angle1: float, 
    angle2: float
) -> shapely.geometry.Polygon:
    """
    ベース地点から扇状のPolygonを作成する。\n
    Args:
        base_point(shapely.geometry.Point):
        distance(int): コーナーまでの距離
        angle1(float): 1コーナーへの方位角
        angle2(float): 2コーナーへの方位角
    Returns:
        shapely.geometry.Polygon
    """
    circle = base_point.buffer(distance)
    pt1 = _to_point(base_point, distance * 2, angle1)
    pt2 = _to_point(base_point, distance * 2, angle2)
    triangle = shapely.geometry.Polygon([base_point, pt1, pt2])
    fun = circle.intersection(triangle)
    return fun

