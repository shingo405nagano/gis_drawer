"""
1. transform
    座標の投影変換のモジュール

"""
from dataclasses import dataclass, asdict
import logging
from typing import Any
from typing import List

import pyproj
import shapely

from disassembly import geom_disassembly
from settings import JGD2011_UTM_RANGE_LST
from settings import JGD2011_UTM_CODES_DICT


@dataclass
class Coords:
    lon: float = None
    lat: float = None
    lons: List[float] = None
    lats: List[float] = None
    points: List[shapely.geometry.Point] = None
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
                points=[shapely.geometry.Point(_x, _y)]
            )
        else:
            coords = Coords(
                lons=_x,
                lats=_y,
                points=[shapely.geometry.Point(x, y) for x, y in zip(_x, _y)]
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
    >>> transform(39773.1479, 126992.7959, 6678, 4326)
    Coords(lon=141.30713264233432, lat=41.14274895389813, lons=None, lats=None, points=[<POINT (141.307 41.143)>])
    >>> transform([39773.1479, 39773.147955], [126992.7959, 126992.795955], 6678, 4326)
    Coords(lon=None, lat=None, lons=[141.30713264233432, 141.30713264299308], lats=[41.14274895389813, 41.14274895439072], points=[<POINT (141.307 41.143)>, <POINT (141.307 41.143)>])
    """
    tp = _TransformerProject(lon, lat, in_epsg, out_epsg)
    return tp.result




class EstimationJgdUTM(object):    
    def _check_shapely(self, geom: Any):
        try:
            _ = geom.distance
        except:
            return False
        else:
            return True
    
    def _get_epsg(self, lon: float):
        epsg = None
        for idx, (x_min, x_max) in enumerate(JGD2011_UTM_RANGE_LST):
            if x_min <= lon < x_max:
                epsg = JGD2011_UTM_CODES_DICT.get(idx)
                break
        if epsg is None:
            logging.warning('Failed to estimate UTM coordinate system.')
        return epsg
        



def estimation_jgd_utm_from_geom(geom: Any) -> int:
    """
    日本のUTM座標系を推定する。
    Args:
        geom(Any): shapely.geometry. のオブジェクト
    Return:
        int: epsg code
    Doctest:
        >>> estimation_jgd_utm_from_geom(shapely.Point(160.00, 40.00))
        >>> estimation_jgd_utm_from_geom(shapely.Point(140.00, 40.00))
        6691
        >>> estimation_jgd_utm_from_geom(shapely.Point(130.00, 40.00))
        6689
    """
    epsg = None
    e_utm = EstimationJgdUTM()
    if e_utm._check_shapely(geom):
        center = geom.centroid
        epsg = e_utm._get_epsg(center.x)
    else:
        logging.warning(f'Failed to estimate UTM coordinate system. {__file__}')
    return epsg


def estimation_jgd_utm_from_lon(lon: float):
    """
    日本のUTM座標系を推定する。
    Args:
        lon(float): 経度
    Return:
        int: epsg code
    Doctest:
        >>> estimation_jgd_utm_from_lon(160.00)
        >>> estimation_jgd_utm_from_lon(140.00)
        6691
        >>> estimation_jgd_utm_from_lon(130.00)
        6689
    """
    epsg = None
    e_utm = EstimationJgdUTM()
    if isinstance(lon, float) | isinstance(lon, int):
        epsg = e_utm._get_epsg(lon)
    else:
        logging.warning(f'Failed to estimate UTM coordinate system. {__file__}')
    return epsg





if __name__ == '__main__':
    import doctest
    doctest.testmod()