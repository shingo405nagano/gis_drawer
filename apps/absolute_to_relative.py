"""
経緯度などの絶対座標から方位角や水平距離などの相対座標を計算する。

"""
from dataclasses import dataclass
from typing import List

import pyproj
import shapely

from disassembly import geom_disassembly
from projective_transformer import transform


@dataclass
class RelatieCoords:
    azimuth: float
    h_distance: float

@dataclass
class RelatieCoordinates:
    azimuth: List[float]
    h_distance: List[float]


class _Absolute2Relative(object):
    def __init__(self, lons: List[float], lats: List[float], epsg: int):
        self.ellipsoid = 'GRS80'
        if epsg != 4326:
            coords = transform(lons, lats, epsg, 4326)
            self._lons = coords.lons
            self._lats = coords.lats
        else:
            self._lons = lons
            self._lats = lats

    def calc_azimuth_and_distance(
        self,
        behind_lon: float, 
        behind_lat: float, 
        forward_lon: float, 
        forward_lat: float,
    ) -> RelatieCoords:
        """経緯度から方位角と水平距離を計算します
        """
        geod = pyproj.Geod(ellps=self.ellipsoid)
        result = geod.inv(behind_lon, behind_lat, forward_lon, forward_lat)
        azimuth = result[0]
        if azimuth < 0:
            azimuth += 360
        distance = result[2] 
        return RelatieCoords(azimuth=azimuth, h_distance=distance)
    
    def __closed(self, closed: bool):
        if closed:
            # closedの場合、最初の座標を最後にも追加する
            if (self._lons[0] != self._lons[-1]) & (self._lats[0] != self._lats[-1]):
                lons = self._lons + [self._lons[0]]
                lats = self._lats + [self._lats[0]]
                return lons, lats
        return self._lons, self._lats
        
    def calc_azimuth_and_distance_all(self, closed: bool=True):
        """
        経緯度のリストから真北の方位角と水平距離を計算します。
        """
        lons, lats = self.__closed(closed)
        # 方位角と水平距離を計算
        azimuth_lst = []
        distance_lst = []
        for i in range(1, len(lons)):
            behind_lon = lons[i - 1]
            behind_lat = lats[i - 1]
            forward_lon = lons[i]
            forward_lat = lats[i]
            relative_coords = self.calc_azimuth_and_distance(
                behind_lon, behind_lat, forward_lon, forward_lat)
            azimuth_lst.append(relative_coords.azimuth)
            distance_lst.append(relative_coords.h_distance)
        
        return RelatieCoordinates(
            azimuth=azimuth_lst, h_distance=distance_lst
        )



def absolute_to_relative_coords(
    geometry: shapely.geometry.LineString 
        | shapely.geometry.MultiLineString 
        | shapely.geometry.MultiPolygon 
        | shapely.geometry.Polygon, 
    epsg: int,
    closed: bool=True
) -> RelatieCoordinates | List[RelatieCoordinates]:
    """
    shapely.geometryを分解して絶対座標から相対座標を計算する
    Args:
        geometry(LineString | MultiLineString | MultiPolygon | Polygon):
        epsg(int): epsg code
        closed(bool): 閉合するか、閉合する場合は0番目の経緯度を最後にも追加する
    Returns:
        RelatieCoordinates:
            azimuth(List[float]): 真北の方位角
            h_distance(List[float]): 水平距離
    """
    x, y, z = geom_disassembly(geometry, 'x_y_z')
    if isinstance(x, float):
        a2r = _Absolute2Relative(x, y, epsg)
        return a2r.calc_azimuth_and_distance_all(closed)
    relative_corods = []
    for _x, _y in zip(x, y):
        a2r = _Absolute2Relative(_x, _y, epsg)
        r_coords = a2r.calc_azimuth_and_distance(closed)
        relative_corods.append(r_coords)
    return relative_corods

