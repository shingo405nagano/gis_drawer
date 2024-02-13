"""
座標の投影変換のモジュール
"""
from dataclasses import dataclass, asdict
from typing import List

import pyproj
from shapely.geometry import Point


@dataclass
class Coords:
    lon: float = None
    lat: float = None
    lons: List[float] = None
    lats: List[float] = None
    points: List[Point] = None
    dict=asdict


class _TransformerProject(object):
    def __init__(
        self, 
        lon: float | List[float], 
        lat: float | List[float], 
        in_epsg: int,
        out_epsg: int
    ):
        super().__init__()
        self._transformer = self._create_tramsformer(in_epsg, out_epsg)
        self.lon = lon
        self.lat = lat

    def _create_tramsformer(
        self,
        in_epsg: int, 
        out_epsg: int
    ) -> pyproj.Transformer:
        # 投影変換器の作成
        transformer = pyproj.Transformer.from_crs(
            crs_from=f'epsg:{in_epsg}', crs_to=f'epsg:{out_epsg}', 
            always_xy=True
        )
        return transformer

    def _transformer_project_xy(self, lon: float, lat: float) -> Coords:
        x, y = self._transformer.transform(lon, lat)
        return x, y

    @property
    def result(self) -> Coords:
        _x, _y = self._transformer_project_xy(self.lon, self.lat)
        if isinstance(_x, float):
            coords = Coords(
                lon=_x,
                lat=_y,
                points=[Point(_x, _y)]
            )
        else:
            coords = Coords(
                lons=_x,
                lats=_y,
                points=[Point(x, y) for x, y in zip(_x, _y)]
            )
        return coords


    
def transform(
    lon: float | List[float], 
    lat: float | List[float], 
    in_epsg: int,
    out_epsg: int
) -> Coords:
    """
    投影変換モジュール
    >>> transformer_project(39773.1479, 126992.7959, 6678, 4326)
    Coords(lon=141.30713264233432, lat=41.14274895389813, lons=None, lats=None, points=[<POINT (141.307 41.143)>])
    >>> transformer_project([39773.1479, 39773.147955], [126992.7959, 126992.795955], 6678, 4326)
    Coords(lon=None, lat=None, lons=[141.30713264233432, 141.30713264299308], lats=[41.14274895389813, 41.14274895439072], points=[<POINT (141.307 41.143)>, <POINT (141.307 41.143)>])
    """
    tp = _TransformerProject(lon, lat, in_epsg, out_epsg)
    return tp.result



if __name__ == '__main__':
    import doctest
    doctest.testmod()