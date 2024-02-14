"""
空間検索の材料にする為のPolygonを作成する。
1. directional_rectangle
   ベース地点からある方向に向かって長方形のバッファーを作成する。
2.  directional_fan
    ベース地点から扇状のPolygonを作成する。空港の侵入方向等に使用。

"""

import math
from typing import List

import geopandas as gpd
import shapely


def _to_point(base_point, distance, angle) -> shapely.Point:
    # 距離と方向から新しいPointObjectを作成する
    angle_rad = math.radians(angle)
    x = base_point.x + distance * math.sin(angle_rad)
    y = base_point.y + distance * math.cos(angle_rad)
    destination = (x, y)
    return shapely.Point(destination)


def directional_rectangle(
    base_point: shapely.Point, 
    distance: int, 
    angle: float, 
    width: float
) -> shapely.Polygon:
    """
    ベース地点からある方向に向かって長方形のバッファーを作成する。\n
    Args:
        base_point(shapely.Point):
        distance(int): 長方形の高さ
        angle(float): 長方形を作成する方位
        width(float): 長方形の幅
    Returns:
        shapely.Polygon
    """
    trg_point = _to_point(base_point, distance, angle)
    line = shapely.LineString([base_point, trg_point])
    rectangles = line.buffer(width, cap_style='flat')
    return rectangles


def directional_fan(
    base_point: shapely.Point, 
    distance: int, 
    angle1: float, 
    angle2: float
) -> shapely.Polygon:
    """
    ベース地点から扇状のPolygonを作成する。\n
    Args:
        base_point(shapely.Point):
        distance(int): コーナーまでの距離
        angle1(float): 1コーナーへの方位角
        angle2(float): 2コーナーへの方位角
    Returns:
        shapely.Polygon
    """
    circle = base_point.buffer(distance)
    pt1 = _to_point(base_point, distance * 2, angle1)
    pt2 = _to_point(base_point, distance * 2, angle2)
    triangle = shapely.Polygon([base_point, pt1, pt2])
    fun = circle.intersection(triangle)
    return fun



class Tessellation(object):
    def __init__(self, hectare: float, x_min: float, x_max: float, y_min: float, y_max: float):
        self._hectare = hectare
        self._square_metre = hectare * 10_000
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
    
    def _regular_hexagon(self, center_x: float, center_y: float) -> shapely.Polygon:
        center = shapely.Point(center_x, center_y)
        # 正六角形の一辺の長さを計算
        side_length = math.sqrt(self._square_metre / (1.5 * math.sqrt(3)))
        # 正六角形の頂点座標を計算（時計回りで）
        h_vertices = []
        for angle in range(0, 420, 60):
            x = center.x + side_length * math.sin(math.radians(angle))
            y = center.y + side_length * math.cos(math.radians(angle))
            point = shapely.Point(x, y)
            h_vertices.append(point)
        # 正六角形のPolygonを作成
        hexagon = shapely.Polygon(h_vertices)
        return hexagon
    
    def __calc_max_x(self, poly: shapely.Polygon) -> float:
        max_x = max(coord[0] for coord in poly.exterior.coords)
        return max_x
    
    def __calc_min_y(self, poly: shapely.Polygon) -> float:
        min_y = min(coord[1] for coord in poly.exterior.coords)
        return min_y
    
    def _side_by_side(self, start_x: float, start_y: float, end_x: float) -> List[shapely.Polygon]:
        _xoff = math.sqrt(self._square_metre / (2 * math.sqrt(3))) * 2
        xoff = _xoff - _xoff / 100_000_000
        hexagon = self._regular_hexagon(start_x, start_y)
        hexagon_list = [hexagon]
        while True:
            shift_hexagon = shapely.affinity.translate(hexagon_list[-1], xoff)
            new_max_x = self.__calc_max_x(shift_hexagon)
            hexagon_list.append(shift_hexagon)
            if end_x < new_max_x:
                break
        return hexagon_list
    
    def _lower_side_by_side(self, start_x: float, start_y: float, end_x: float) -> List[shapely.Polygon]:
        _xoff = math.sqrt(self._square_metre / (2 * math.sqrt(3)))
        xoff = _xoff - _xoff / 100_000_000
        yoff = math.sqrt((xoff * 2) ** 2 - (xoff ** 2)) * -1
        hexagons = self._side_by_side(start_x, start_y, end_x)
        new_hexagons = []
        for hexagon in hexagons:
            new_hexagon = shapely.affinity.translate(hexagon, xoff, yoff)
            new_hexagons.append(new_hexagon)
        first_hexagon = shapely.affinity.translate(new_hexagons[0], xoff * 2 * -1)
        return [first_hexagon] + new_hexagons
    
    def __move_down(self, hexagons: List[shapely.Polygon], yoff: float) -> List[shapely.Polygon]:
        new_hexagon_list = []
        for hexagon in hexagons:
            new_hexagon = shapely.affinity.translate(hexagon, yoff=yoff)
            new_hexagon_list.append(new_hexagon)
        return new_hexagon_list
    
    def __create_gdf(self, upper_polys: List[shapely.Polygon], lower_polys: List[shapely.Polygon]) -> gpd.GeoDataFrame:
        idxs = []
        polys = []
        
            
    @property
    def generate_hexagons_gdf(self):
        sbs_polys = self._side_by_side(self.x_min, self.y_max, self.x_max)
        lsbs_polys = self._lower_side_by_side(self.x_min, self.y_max, self.x_max)
        _yoff = math.sqrt(self._square_metre / (1.5 * math.sqrt(3)))
        yoff = (_yoff - _yoff / 100_000_000) * 3 * -1
        upper_polys = [sbs_polys]
        lower_polys = [lsbs_polys]
        while True:
            shift_sbs_polys = self.__move_down(upper_polys[-1], yoff)
            y_min = self.__calc_min_y(shift_sbs_polys[0])
            upper_polys.append(shift_sbs_polys)
            if y_min < self.y_min:
                break
            shift_lsbs_polys = self.__move_down(lower_polys[-1], yoff)
            y_min = self.__calc_min_y(shift_lsbs_polys[0])
            lower_polys.append(shift_lsbs_polys)
            if y_min < self.y_min:
                break
        
        return upper_polys, lower_polys