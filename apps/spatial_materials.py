"""
空間検索の材料にする為のPolygonを作成する。
1. directional_rectangle
   ベース地点からある方向に向かって長方形のバッファーを作成する。
2.  directional_fan
    ベース地点から扇状のPolygonを作成する。空港の侵入方向等に使用。
3. regular_hexagon
    指定座標から指定した面積の正六角形のPolygonオブジェクトを作成する。
4. regular_hexagon_gdf
    指定範囲全体に指定した面積の正六角形のPolygonオブジェクトを作成する。
"""
from dataclasses import dataclass
import math
from typing import List

import geopandas as gpd
import shapely


def _to_point(base_point, distance, angle) -> shapely.Point:
    """距離と方向から新しいPointObjectを作成する"""
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



@dataclass
class SortedHexagons:
    hexagon_lst: List[shapely.Polygon]
    rows_idx: List[str]
    cols_idx: List[str]


class Hexagons(object):
    def __init__(
        self, 
        hectare: float, 
        x_min: float, 
        y_min: float, 
        x_max: float, 
        y_max: float, 
        margin: float=0
    ):
        self._hectare = hectare
        self._square_metre = hectare * 10_000
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        if 0 < margin:
            self._add_margin(margin)
    
    def _add_margin(self, margin: float):
        """指定した範囲に余白を追加する"""
        self.x_min += (margin * -1)
        self.y_min += (margin * -1)
        self.x_max += (margin)
        self.y_max += (margin)

    def _regular_hexagon(
        self, 
        center_x: float, 
        center_y: float
    ) -> shapely.Polygon:
        """中心座標から設定している面積の六角形を作成する。"""
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
    
    def __calc_x_max(self, poly: shapely.Polygon) -> float:
        """Polygon内のx座標の最大値を計算"""
        x_max = max([coord[0] for coord in poly.exterior.coords])
        return x_max
    
    def __calc_y_min(self, poly: shapely.Polygon) -> float:
        """Polygon内のy座標の最小値を計算"""
        y_min = min([coord[1] for coord in poly.exterior.coords])
        return y_min
    
    def _side_by_side(
        self, 
        start_x: float, 
        start_y: float, 
        end_x: float
    ) -> List[shapely.Polygon]:
        """
        指定したstart座標からend_xまで、六角形を生成し続ける。\n
        Args:
            start_x(float): x_min
            start_y(float): y_max
            end_x(float): x_max
        Returns:
            List(shapely.Polygon): 横並びの六角形
        """
        _xoff = math.sqrt(self._square_metre / (2 * math.sqrt(3))) * 2
        xoff = _xoff - _xoff / 100_000_000
        hexagon = self._regular_hexagon(start_x, start_y)
        hexagon_list = [hexagon]
        while True:
            shift_hexagon = shapely.affinity.translate(hexagon_list[-1], xoff)
            x_max = self.__calc_x_max(shift_hexagon)
            hexagon_list.append(shift_hexagon)
            if end_x < x_max:
                break
        return hexagon_list
    
    def _lower_side_by_side(
        self, 
        start_x: float, 
        start_y: float, 
        end_x: float
    ) -> List[shapely.Polygon]:
        """
        指定したstart座標からend_xまで、六角形を生成し続ける。\n
        生成した六角形を斜め下にフィットする様にずらす。
        Args:
            start_x(float): x_min
            start_y(float): y_max
            end_x(float): x_max
        Returns:
            List(shapely.Polygon): 横並びのずらした六角形
        """
        _xoff = math.sqrt(self._square_metre / (2 * math.sqrt(3)))
        xoff = _xoff - _xoff / 100_000_000
        yoff = math.sqrt((xoff * 2) ** 2 - (xoff ** 2)) * -1
        hexagons = self._side_by_side(start_x, start_y, end_x)
        new_hexagons = []
        for hexagon in hexagons:
            new_hexagon = shapely.affinity.translate(hexagon, xoff, yoff)
            new_hexagons.append(new_hexagon)
        # 右側にずらしたので、最初に新しく六角形を追加する。
        first_hexagon = shapely.affinity.translate(new_hexagons[0], xoff * 2 * -1)
        return [first_hexagon] + new_hexagons
    
    def __move_down(
        self, 
        hexagons: List[shapely.Polygon], 
        yoff: float
    ) -> List[shapely.Polygon]:
        """下にずらす"""
        new_hexagon_list = []
        for hexagon in hexagons:
            new_hexagon = shapely.affinity.translate(hexagon, yoff=yoff)
            new_hexagon_list.append(new_hexagon)
        return new_hexagon_list
    
    def _sort_hexagons(
        self, 
        upper_polys: List[shapely.Polygon], 
        lower_polys: List[shapely.Polygon]
    ) -> SortedHexagons:
        """
        生成済みの六角形を左上から右下にかけて並び替え、idを割り当てる。\n
        Args:
            upper_polys(List[shapely.Polygon]): 横並びの六角形
            lower_polys(List[shapely.Polygon]): 斜め下にずらした横並びの六角形
        Retuens:
            SortedHexagons:
                hexagon_lst(List[shapely.Polygon]): 六角形のリスト
                rows_idx(int): 行番号
                cols_idx(int): 列番号
        """
        hexagon_lst = []
        rows_idx = []
        cols_idx = []
        row = 0
        while True:
            if 1 <= len(upper_polys):
                polys = upper_polys.pop(0)
                for i, poly in enumerate(polys):
                    hexagon_lst.append(poly)
                    rows_idx.append(row)
                    cols_idx.append(i)
            row += 1
            if 1 <= len(lower_polys):
                polys = lower_polys.pop(0)
                for i, poly in enumerate(polys):
                    hexagon_lst.append(poly)
                    rows_idx.append(row)
                    cols_idx.append(i)
            if (len(upper_polys) == 0) & (len(lower_polys) == 0):
                break
            row += 1
        return SortedHexagons(hexagon_lst, rows_idx, cols_idx)
    
    def _create_gdf(
        self, 
        upper_polys: List[shapely.Polygon], 
        lower_polys: List[shapely.Polygon]
    ) -> gpd.GeoDataFrame:
        """
        生成済みの六角形を左上から右下にかけて並び替え、idを割り当てたGeoDataFr
        ameを作成する。\n
        Args:
            upper_polys(List[shapely.Polygon]): 横並びの六角形
            lower_polys(List[shapely.Polygon]): 斜め下にずらした横並びの六角形
        """
        sorted_hexs = self._sort_hexagons(upper_polys, lower_polys)
        data = {
            'rows_idx': sorted_hexs.rows_idx,
            'cols_idx': sorted_hexs.cols_idx,
            'unique_id': [
                f"{r}-{c}" for r, c in 
                zip(sorted_hexs.rows_idx, sorted_hexs.cols_idx)]
        }
        # CRSは設定しない
        gdf = gpd.GeoDataFrame(data=data, geometry=sorted_hexs.hexagon_lst)
        return gdf

    @property   
    def create_hexagons_gdf(self):
        """
        指定範囲に指定面積の六角形を並べたGeoDataFrameを作成する。
        """
        # 横並びの六角形を作成する
        sbs_polys = self._side_by_side(self.x_min, self.y_max, self.x_max)
        # 上記で作成した六角形を斜め下にずらし、フィットさせる
        lsbs_polys = self._lower_side_by_side(self.x_min, self.y_max, self.x_max)
        # 設定した範囲までデータをコピーし、ずらし続ける
        _yoff = math.sqrt(self._square_metre / (1.5 * math.sqrt(3)))
        yoff = (_yoff - _yoff / 100_000_000) * 3 * -1  # 少し重ねないとtouchesでFalseになるので
        upper_polys = [sbs_polys]
        lower_polys = [lsbs_polys]
        while True:
            shift_sbs_polys = self.__move_down(upper_polys[-1], yoff)
            y_min = self.__calc_y_min(shift_sbs_polys[0])
            upper_polys.append(shift_sbs_polys)
            if y_min < self.y_min:
                break
            shift_lsbs_polys = self.__move_down(lower_polys[-1], yoff)
            y_min = self.__calc_y_min(shift_lsbs_polys[0])
            lower_polys.append(shift_lsbs_polys)
            if y_min < self.y_min:
                break
        gdf = self._create_gdf(upper_polys, lower_polys)
        return gdf
    

def regular_hexagon(
    hectare: float, 
    center_x: float, 
    center_y: float,
) -> shapely.Polygon:
    """
    正六角形のPolygonオブジェクトを作成する。\n
    メルカトル図法を対象としています。\n
    Args:
        hectare(float): 面積（ヘクタール）
        center_x(float): 中心となるx座標
        center_y(float): 中心とするy座標
    Returns:
        shapely.geometry.Polygon
    """
    hxgs = Hexagons(hectare, None, None, None, None)
    hexagon = hxgs._regular_hexagon(center_x, center_y)
    return hexagon


def regular_hexagon_gdf(
    hectare: float, 
    x_min: float, 
    y_min: float, 
    x_max: float, 
    y_max: float, 
    margin: float=0
) -> gpd.GeoDataFrame:
    """
    指定した範囲全体に正六角形のPolygonオブジェクトを作成し
    ユニークなIDを入力したGeoDataFrameを作成する。\n
    メルカトル図法を対象としています。\n
    Args:
        hectare(float): 面積（ヘクタール）
        x_min(float): x_min
        y_min(float): y_min
        x_max(float): x_max
        y_max(float): y_max
        margin(float): 作成範囲に余白を追加するか
    Returns:
        gpd.GeoDataFrame
    """
    hxgs = Hexagons(hectare, x_min, y_min, x_max, y_max, margin)
    gdf = hxgs.create_hexagons_gdf
    return gdf